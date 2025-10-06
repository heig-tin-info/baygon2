import stat
import sys
import textwrap

import pytest

from baygon.executable import Executable, InvalidExecutableError


@pytest.mark.parametrize("binary, args, expected", [
    ("echo", ["hello", "world"], "hello world\n"),
    (sys.executable, ["-c", "print('ok')"], "ok\n"),
])
def test_run_basic_commands(binary, args, expected):
    exe = Executable(binary)
    result = exe.run(*args)
    assert result.exit_status == 0
    assert result.stdout == expected
    assert result.stderr == ""


def test_run_with_stdin_and_env(tmp_path):
    script = tmp_path / "reader.py"
    script.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import os
            import sys

            prefix = os.environ.get("EXEC_PREFIX", "")
            data = sys.stdin.read()
            sys.stdout.write(prefix + data.upper())
            """
        )
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    exe = Executable(str(script))
    result = exe.run(stdin="hello", env={"EXEC_PREFIX": "::"})
    assert result.exit_status == 0
    assert result.stdout == "::HELLO"
    assert result.stderr == ""


def test_timeout_kills_process(tmp_path):
    script = tmp_path / "sleeper.py"
    script.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import time
            time.sleep(10)
            """
        )
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    exe = Executable(str(script))
    result = exe.run(timeout=0.5)
    assert result.exit_status != 0


@pytest.mark.parametrize("binary", ["rm", "mv", "dd", "wget", "mkfs"])
def test_forbidden_binaries(binary):
    with pytest.raises(InvalidExecutableError):
        Executable(binary)


def test_invalid_executable_path(tmp_path):
    non_exec = tmp_path / "non_exec.txt"
    non_exec.write_text("data")
    with pytest.raises(InvalidExecutableError):
        Executable(str(non_exec))
