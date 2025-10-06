"""
Safe Executable wrapper with basic resource limits, timeouts and optional sandbox hooks.

Limitations / notes:
 - POSIX: uses resource.setrlimit in preexec_fn (works only on UNIX; preexec_fn is unsafe in multi-threaded programs).
 - Windows: tries to use Job Objects via pywin32 if available, else best-effort fallback.
 - For production-grade sandboxing prefer external tools (nsjail, bubblewrap, firejail, gVisor, containers).
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import subprocess
import sys
from collections import namedtuple
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Sequence

logger = logging.getLogger("baygon")
Outputs = namedtuple("Outputs", ["exit_status", "stdout", "stderr"])

try:
    import resource  # POSIX-only
except Exception:
    resource = None

# Windows job-object helpers (best-effort)
WINDOWS = sys.platform.startswith("win")

if WINDOWS:
    try:
        import ctypes as _ctypes  # type: ignore
    except Exception:  # pragma: no cover - platform specific
        _ctypes = None
else:
    _ctypes = None

# During type checking we want the real module so that attribute resolution works.
if TYPE_CHECKING:  # pragma: no cover - type checking only
    import ctypes as _ctypes_types

ctypes: ModuleType | Any | None = _ctypes


class InvalidExecutableError(Exception):
    """Raised when a provided executable path fails validation."""


FORBIDDEN_BINARIES = {"rm", "mv", "dd", "wget", "mkfs"}


EnvMapping = dict[str, str]
SandboxConfig = dict[str, object]


def get_env(env: dict[str, str] | None = None) -> EnvMapping:
    return {**os.environ, **(env or {})}


def _posix_preexec_fn(
    cpu_time: int | None = None,
    mem_bytes: int | None = None,
    nproc: int | None = None,
    no_new_privs: bool = True,
    uid: int | None = None,
    gid: int | None = None,
    chroot_dir: str | None = None,
):
    """
    Returns a function suitable for subprocess.Popen(preexec_fn=...).
    Must be called in the child process. Only on POSIX.
    """
    def _inner():
        # setrlimit wrappers are best-effort
        if resource is None:
            return

        if cpu_time is not None:
            # RLIMIT_CPU in seconds
            with contextlib.suppress(Exception):
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))

        if mem_bytes is not None:
            # RLIMIT_AS: total address space
            with contextlib.suppress(Exception):
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

        if nproc is not None:
            with contextlib.suppress(Exception):
                resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))

        # optionally chroot (requires root)
        if chroot_dir:
            try:
                os.chroot(chroot_dir)
                os.chdir("/")
            except Exception:
                # fail silently; caller should ensure permissions
                pass

        # drop privileges
        if gid is not None:
            with contextlib.suppress(Exception):
                os.setgid(gid)
        if uid is not None:
            with contextlib.suppress(Exception):
                os.setuid(uid)

        # prevent gaining new privileges (recommended)
        if no_new_privs and ctypes is not None:
            pr_set_no_new_privs = 38
            with contextlib.suppress(Exception):
                # linux prctl via ctypes to set no_new_privs
                libc = ctypes.CDLL("libc.so.6")
                libc.prctl(pr_set_no_new_privs, 1, 0, 0, 0)

    return _inner


# Windows Job Object helper (best-effort)
class _WinJob:
    """Best-effort Windows Job Object wrapper used to apply limits."""
    def __init__(self, cpu_time_ms: int | None = None, memory_bytes: int | None = None):
        self.job: int | None = None
        self.cpu_time_ms = cpu_time_ms
        self.memory_bytes = memory_bytes

    @staticmethod
    def _kernel32() -> Any | None:
        if ctypes is None:
            return None
        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return None
        return getattr(windll, "kernel32", None)

    def create(self) -> int | None:
        kernel32 = self._kernel32()
        if kernel32 is None:
            return None
        # Minimal safe-guard: create job and return handle; detailed limit setting omitted for brevity
        # For robust implementation, prefer pywin32 and JobObjectExtendedLimitInformation structures.
        # Here we just create a job and return it.
        job = kernel32.CreateJobObjectW(None, None)
        if job == 0:
            return None
        self.job = job
        # NOTE: proper limit configuration requires building JOBOBJECT_EXTENDED_LIMIT_INFORMATION struct.
        return job

    def assign(self, pid: int) -> bool:
        kernel32 = self._kernel32()
        if kernel32 is None or self.job is None:
            return False
        process_all_access = 0x1F0FFF
        open_process = kernel32.OpenProcess
        hproc = open_process(process_all_access, False, pid)
        if not hproc:
            return False
        res = kernel32.AssignProcessToJobObject(self.job, hproc)
        # Close handle to process
        kernel32.CloseHandle(hproc)
        return bool(res)


class Executable:
    """Wrapper that executes binaries with optional resource constraints."""
    filename: str
    encoding: str

    def __new__(cls, filename: "Executable | str | os.PathLike[str] | None"):
        if isinstance(filename, cls):
            return filename
        return super().__new__(cls) if filename else None

    def __init__(self, filename: "Executable | str | os.PathLike[str]", encoding: str = "utf-8"):
        if isinstance(filename, self.__class__):
            self.filename = filename.filename
            self.encoding = filename.encoding
        else:
            self.filename = os.fspath(filename)
            self.encoding = encoding

        resolved = self.filename
        if not self._is_executable(resolved):
            if "/" not in resolved:
                located = shutil.which(resolved)
                if located:
                    if resolved in FORBIDDEN_BINARIES:
                        raise InvalidExecutableError(f"Program '{resolved}' is forbidden!")
                    self.filename = located
                    resolved = located
            if not self._is_executable(resolved):
                raise InvalidExecutableError(f"Program '{resolved}' is not an executable!")

    def run(
        self,
        *args: object,
        stdin: str | bytes | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
        cpu_time: int | None = None,      # seconds (POSIX)
        mem_bytes: int | None = None,     # address space bytes
        nproc: int | None = None,         # max child procs
        uid: int | None = None,
        gid: int | None = None,
        chroot_dir: str | None = None,
        use_external_sandbox: SandboxConfig | None = None,  # e.g. {"tool":"nsjail","args":[...]}
        hook: Callable[..., None] | None = None,
    ) -> Outputs:
        """
        Run executable with resource constraints.

        - use_external_sandbox: if provided, runs the command through an external tool, e.g.
            {"tool": "nsjail", "args": ["--config", "/etc/nsjail.cfg"]}
        """

        cmd = [self.filename, *[str(a) for a in args]]

        # If external sandbox requested, wrap command.
        if use_external_sandbox:
            tool = use_external_sandbox.get("tool")
            extra = use_external_sandbox.get("args")
            if tool:
                extra_args: list[str]
                if isinstance(extra, Sequence) and not isinstance(extra, (str, bytes)):
                    extra_args = [str(arg) for arg in extra]
                else:
                    extra_args = []
                # naive wrapper: tool + extra + -- cmd...
                # user must ensure tool is present and args are correct
                cmd = [str(tool), *extra_args, "--", *cmd]

        popen_kwargs: dict[str, object] = {
            "stdout": subprocess.PIPE,
            "stdin": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "env": get_env(env),
            "text": False,  # we handle encoding manually
        }

        preexec = None
        win_job = None
        if not WINDOWS:
            # POSIX: set resource limits in child
            if any(x is not None for x in (cpu_time, mem_bytes, nproc, uid, gid, chroot_dir)):
                if resource is None:
                    logger.warning("resource module not available on this platform")
                else:
                    preexec = _posix_preexec_fn(cpu_time=cpu_time, mem_bytes=mem_bytes,
                                                nproc=nproc, uid=uid, gid=gid, chroot_dir=chroot_dir)
                    popen_kwargs["preexec_fn"] = preexec
        else:
            # Windows: create job object with limits (best-effort)
            if ctypes is not None:
                win_job = _WinJob(cpu_time_ms=(cpu_time * 1000 if cpu_time else None),
                                  memory_bytes=mem_bytes)
                job_handle = win_job.create()
                if job_handle:
                    # we will assign after spawn
                    pass

        # spawn
        cmd_args = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd_args, **popen_kwargs)

        # assign to job on Windows
        if WINDOWS and win_job and win_job.job:
            with contextlib.suppress(Exception):
                win_job.assign(proc.pid)

        try:
            stdout_bytes: bytes | None
            stderr_bytes: bytes | None
            if stdin is None:
                stdin_bytes = None
            elif isinstance(stdin, bytes):
                stdin_bytes = stdin
            else:
                stdin_bytes = stdin.encode(self.encoding)

            stdout_bytes, stderr_bytes = proc.communicate(input=stdin_bytes, timeout=timeout)
        except subprocess.TimeoutExpired:
            # timeout: kill process tree / job
            with contextlib.suppress(Exception):
                proc.kill()
            proc.wait()
            stdout_bytes, stderr_bytes = proc.communicate(timeout=1)
        except Exception:
            proc.kill()
            proc.wait()
            raise

        stdout_text = ""
        if stdout_bytes is not None:
            try:
                stdout_text = stdout_bytes.decode(self.encoding)
            except Exception:
                stdout_text = stdout_bytes.decode(errors="ignore")

        stderr_text = ""
        if stderr_bytes is not None:
            try:
                stderr_text = stderr_bytes.decode(self.encoding)
            except Exception:
                stderr_text = stderr_bytes.decode(errors="ignore")

        if hook and callable(hook):
            hook(cmd=cmd_args, stdin=stdin, stdout=stdout_text, stderr=stderr_text, exit_status=proc.returncode)

        return Outputs(proc.returncode, stdout_text, stderr_text)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.filename}>"

    @staticmethod
    def _is_executable(filename: str | os.PathLike[str]) -> bool:
        path = Path(filename)
        return path.is_file() and os.access(path, os.X_OK)
