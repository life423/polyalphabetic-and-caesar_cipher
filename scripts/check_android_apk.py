"""Fail CI if the APK loses its bundled engine or account-deletion interface."""
import sys
import zipfile


def check(path):
    with zipfile.ZipFile(path) as apk:
        for name in ('index.html', 'engine.zip', 'runtime/pyodide.asm.wasm',
                     'account-deletion.js', 'account-deletion.css',
                     'delete-account.html', 'messenger.js'):
            assert apk.getinfo('assets/public/' + name).file_size > 0, name
        assert b'Delete my account' in apk.read('assets/public/index.html')
        assert not any('firebase-adminsdk' in name or name.endswith('.keystore')
                       for name in apk.namelist())
    print('APK contains the offline engine, AI runtime and account-deletion UI.')


if __name__ == '__main__':
    check(sys.argv[1])
