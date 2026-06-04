import os
import signal
import subprocess
import sys
import time
from pathlib import Path


WATCH_DIR = Path(os.getenv("BOT_WATCH_DIR", "/app/bot"))
POLL_SECONDS = float(os.getenv("BOT_WATCH_POLL_SECONDS", "1"))


def _snapshot() -> dict[Path, int]:
    """Return modification timestamps for watched Python files."""
    return {path: path.stat().st_mtime_ns for path in WATCH_DIR.rglob("*.py") if path.is_file()}


def _terminate(process: subprocess.Popen[bytes]) -> None:
    """Terminate a child process gracefully, then force-kill if needed."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> None:
    """Run the bot process and restart it when watched source files change."""
    stopping = False
    process: subprocess.Popen[bytes] | None = None

    def stop(_signum: int, _frame: object) -> None:
        """Handle shutdown signals and stop the child bot process."""
        nonlocal stopping
        stopping = True
        if process is not None:
            _terminate(process)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    previous = _snapshot()
    while not stopping:
        process = subprocess.Popen([sys.executable, "-m", "bot.main"])
        changed = False
        while not stopping and process.poll() is None:
            time.sleep(POLL_SECONDS)
            current = _snapshot()
            if current != previous:
                previous = current
                changed = True
                _terminate(process)
                break

        while not stopping and not changed:
            time.sleep(POLL_SECONDS)
            current = _snapshot()
            if current != previous:
                previous = current
                break

    if process is not None:
        _terminate(process)


if __name__ == "__main__":
    main()
