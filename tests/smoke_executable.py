"""Smoke-test the packaged CLI independently of the Python source tree."""
import os
from pathlib import Path
import subprocess


def main():
    filename = "cipher_tool.exe" if os.name == "nt" else "cipher_tool"
    executable = (Path(__file__).resolve().parents[1] / "dist" / filename).resolve()
    if not executable.is_file():
        raise SystemExit(f"Missing packaged executable: {executable}")

    result = subprocess.run(
        [str(executable)],
        input="e\nc\n1\nHello\n3\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )
    if result.returncode or "Khoor" not in result.stdout:
        raise SystemExit(
            f"Packaged CLI smoke test failed (exit {result.returncode}):\n{result.stdout}"
        )
    print("Packaged CLI smoke test passed")


if __name__ == "__main__":
    main()
