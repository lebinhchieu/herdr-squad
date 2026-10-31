"""Run a pure-Python `bin/` CLI in this process instead of a new interpreter (ticket 14d, C3).

`run(cli_name, argv, env=None, stdin="")` loads the script with `squadtest.load_cli`, calls `main(argv)` with
`os.environ`, `sys.argv`, `sys.path` and the three standard streams replaced, and returns a `CompletedProcess`
with `stdout`/`stderr` as text and `returncode` like `subprocess.run(..., text=True)`.

Only for a CLI that has `main(argv)` and does not fork, `os.execv`, or read real TTY state. Those keep `subprocess`.
Every patched thing is restored in `finally`."""
import io
import os
import subprocess
import sys
import traceback

import squadtest


def _exit_code(code):
    """The exit status the interpreter would give for `sys.exit(code)`; a message goes to stderr first."""
    if code is None:
        return 0, ""
    if isinstance(code, int):
        return code, ""
    return 1, str(code) + "\n"


def run(cli_name, argv, env=None, stdin=""):
    """`env` is the whole environment of the "process" (None: the current one); `stdin` is str or bytes."""
    stdin_bytes = stdin if isinstance(stdin, bytes) else stdin.encode("utf-8")
    out, err = io.BytesIO(), io.BytesIO()
    saved = (dict(os.environ), sys.argv, list(sys.path), sys.stdin, sys.stdout, sys.stderr, sys.dont_write_bytecode)
    try:
        if env is not None:
            os.environ.clear()
            os.environ.update(env)
        sys.dont_write_bytecode = True  # the real script has no .pyc; loading it here must not leave one
        sys.argv = [cli_name] + list(argv)
        sys.stdin = io.TextIOWrapper(io.BytesIO(stdin_bytes), encoding="utf-8")
        # newline="\n": the bytes written are the bytes read, as in a binary pipe
        sys.stdout = io.TextIOWrapper(out, encoding="utf-8", newline="\n", write_through=True)
        sys.stderr = io.TextIOWrapper(err, encoding="utf-8", newline="\n", write_through=True)
        try:
            returncode = _exit_code(squadtest.load_cli(cli_name).main(list(argv)))[0]
        except SystemExit as e:
            returncode, msg = _exit_code(e.code)
            sys.stderr.write(msg)
        except Exception:  # an uncaught error: traceback on stderr, status 1, like the interpreter
            traceback.print_exc()
            returncode = 1
        sys.stdout.flush()
        sys.stderr.flush()
        stdout, stderr = out.getvalue().decode("utf-8"), err.getvalue().decode("utf-8")  # before the wrappers are dropped
    finally:
        os.environ.clear()
        os.environ.update(saved[0])
        sys.argv, sys.stdin, sys.stdout, sys.stderr = saved[1], saved[3], saved[4], saved[5]
        sys.path[:] = saved[2]
        sys.dont_write_bytecode = saved[6]
    return subprocess.CompletedProcess([cli_name] + list(argv), returncode, stdout, stderr)
