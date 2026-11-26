"""Run the existing native WebView smoke suite on a disposable CI emulator."""
from pathlib import Path
import subprocess
import sys
import time


def adb(*args):
    return subprocess.check_output(['adb', *args], text=True)


def main():
    output = Path('dist/android-checks')
    output.mkdir(parents=True, exist_ok=True)
    try:
        adb('install', '-r', 'mobile/android/app/build/outputs/apk/debug/app-debug.apk')
        adb('shell', 'am', 'start', '-W', '-n',
            'io.drewclark.ciphercraft.beta/.MainActivity')
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            # pidof exits 1 while Android is still starting the process.
            # Keep polling within the startup deadline instead of failing early.
            result = subprocess.run(
                ['adb', 'shell', 'pidof', 'io.drewclark.ciphercraft.beta'],
                capture_output=True, text=True)
            pid = result.stdout.strip() if result.returncode == 0 else ''
            socket = 'webview_devtools_remote_' + pid
            if pid and socket in adb('shell', 'cat', '/proc/net/unix'):
                adb('forward', 'tcp:9224', 'localabstract:' + socket)
                break
            time.sleep(1)
        else:
            raise RuntimeError('Installed app did not expose its debug WebView')
        subprocess.run([sys.executable, 'tests/smoke_android.py'], check=True)
    finally:
        with (output / 'screen.png').open('wb') as stream:
            subprocess.run(['adb', 'exec-out', 'screencap', '-p'], stdout=stream)
        (output / 'logcat.txt').write_text(adb('logcat', '-d'), encoding='utf-8')


if __name__ == '__main__':
    main()
