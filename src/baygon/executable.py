"""
Safe Executable wrapper with basic resource limits, timeouts and optional sandbox hooks.

Limitations / notes:
 - POSIX: uses resource.setrlimit in preexec_fn (works only on UNIX; preexec_fn is unsafe in multi-threaded programs).
 - Windows: tries to use Job Objects via pywin32 if available, else best-effort fallback.
 - For production-grade sandboxing prefer external tools (nsjail, bubblewrap, firejail, gVisor, containers).
"""

import contextlib
import logging
import os
import shutil
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

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
        import ctypes
    except Exception:
        ctypes = None


class InvalidExecutableError(Exception):
    pass


forbidden_binaries = {"rm", "mv", "dd", "wget", "mkfs"}


def get_env(env: dict | None = None) -> dict:
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
        if no_new_privs:
            PR_SET_NO_NEW_PRIVS = 38
            try:
                # linux prctl via ctypes to set no_new_privs
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
            except Exception:
                pass

    return _inner


# Windows Job Object helper (best-effort)
class _WinJob:
    def __init__(self, cpu_time_ms=None, memory_bytes=None):
        self.job = None
        self.cpu_time_ms = cpu_time_ms
        self.memory_bytes = memory_bytes

    def create(self):
        if ctypes is None:
            return None
        # Minimal safe-guard: create job and return handle; detailed limit setting omitted for brevity
        # For robust implementation, prefer pywin32 and JobObjectExtendedLimitInformation structures.
        # Here we just create a job and return it.
        kernel32 = ctypes.windll.kernel32
        job = kernel32.CreateJobObjectW(None, None)
        if job == 0:
            return None
        self.job = job
        # NOTE: proper limit configuration requires building JOBOBJECT_EXTENDED_LIMIT_INFORMATION struct.
        return job

    def assign(self, pid):
        if ctypes is None or self.job is None:
            return False
        kernel32 = ctypes.windll.kernel32
        PROCESS_ALL_ACCESS = 0x1F0FFF
        OpenProcess = kernel32.OpenProcess
        hproc = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not hproc:
            return False
        res = kernel32.AssignProcessToJobObject(self.job, hproc)
        # Close handle to process
        kernel32.CloseHandle(hproc)
        return bool(res)


class Executable:
    def __new__(cls, filename):
        if isinstance(filename, cls):
            return filename
        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding="utf-8"):
        if isinstance(filename, self.__class__):
            self.filename = filename.filename
            self.encoding = filename.encoding
        else:
            self.filename = filename
            self.encoding = encoding

        if not self._is_executable(self.filename):
            if "/" not in filename and shutil.which(filename) is not None:
                if filename in forbidden_binaries:
                    raise InvalidExecutableError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
                self.filename = filename
            else:
                raise InvalidExecutableError(f"Program '{filename}' is not an executable!")

    def run(
        self,
        *args,
        stdin=None,
        env: dict | None = None,
        timeout: float | None = None,
        cpu_time: int | None = None,      # seconds (POSIX)
        mem_bytes: int | None = None,     # address space bytes
        nproc: int | None = None,         # max child procs
        uid: int | None = None,
        gid: int | None = None,
        chroot_dir: str | None = None,
        use_external_sandbox: dict | None = None,  # e.g. {"tool":"nsjail","args":[...]}
        hook=None,
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
            extra = use_external_sandbox.get("args", [])
            if tool:
                # naive wrapper: tool + extra + -- cmd...
                # user must ensure tool is present and args are correct
                cmd = [tool, *extra, "--", *cmd]

        popen_kwargs = {
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
            if ctypes:
                win_job = _WinJob(cpu_time_ms=(cpu_time * 1000 if cpu_time else None),
                                  memory_bytes=mem_bytes)
                job_handle = win_job.create()
                if job_handle:
                    # we will assign after spawn
                    pass

        # spawn
        proc = subprocess.Popen([str(x) for x in cmd], **popen_kwargs)

        # assign to job on Windows
        if WINDOWS and win_job and win_job.job:
            with contextlib.suppress(Exception):
                win_job.assign(proc.pid)

        try:
            stdin_bytes = stdin.encode(self.encoding) if stdin is not None else None

            stdout, stderr = proc.communicate(input=stdin_bytes, timeout=timeout)
        except subprocess.TimeoutExpired:
            # timeout: kill process tree / job
            with contextlib.suppress(Exception):
                proc.kill()
            proc.wait()
            stdout, stderr = proc.communicate(timeout=1)
        except Exception:
            proc.kill()
            proc.wait()
            raise

        if stdout is not None:
            try:
                stdout = stdout.decode(self.encoding)
            except Exception:
                stdout = stdout.decode(errors="ignore")
        else:
            stdout = ""

        if stderr is not None:
            try:
                stderr = stderr.decode(self.encoding)
            except Exception:
                stderr = stderr.decode(errors="ignore")
        else:
            stderr = ""

        if hook and callable(hook):
            hook(cmd=cmd, stdin=stdin, stdout=stdout, stderr=stderr, exit_status=proc.returncode)

        return Outputs(proc.returncode, stdout, stderr)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.filename}>"

    @staticmethod
    def _is_executable(filename):
        path = Path(filename)
        return path.is_file() and os.access(path, os.X_OK)
