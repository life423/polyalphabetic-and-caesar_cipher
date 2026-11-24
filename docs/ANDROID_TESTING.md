# Android test build

The Capacitor shell bundles the existing static app, Pyodide, Python engine and
both locally trained models. It does not load the deployed website. The beta
manifest now includes INTERNET permission for Messages. It has no broad storage
access, camera or microphone permissions. Cipher tools, AI and lessons remain
bundled and work offline. Copy uses Android's clipboard; Save uses the system document picker.

## Build

Requirements: Node 22+, Java 21, Android SDK platform 36 and build tools, the
project Python virtual environment, and `tools/runtime` npm dependencies.

```powershell
./scripts/build_android.ps1 -JavaHome 'C:/path/to/jdk-21' -SdkHome 'C:/path/to/Android/Sdk'
```

The script installs locked mobile npm dependencies, rebuilds the static assets,
synchronizes Android assets, and creates `dist/CipherCraft-android-test.apk` plus
its SHA256 checksum. It discovers a local `.venv/android-tools/jdk-21*` when
JAVA_HOME is unset. No SDK paths, signing keys, or built assets belong in Git.

This is a debug-signed sideload build named **CipherCraft Beta**, package
`io.drewclark.ciphercraft.beta`, version `0.1.0-test`. Minimum Android is 7/API 24;
an up-to-date Android System WebView is required for the WebAssembly engine.
WebView debugging is enabled in this test build. Store publishing, release signing
and testing older Android/WebView combinations remain separate release work.

## Verified November 23, 2026

- Build script completed; APK signature verified with Android `apksigner`.
- Bundled engine/runtime present; both packaged model files matched source bytes.
- Installed and launched on the connected Pixel 10 Pro XL, Android API 37.
- Engine initialized and recovered the ORBIT Vigenere example without internet
  permission. Five cipher round trips and an exact columnar transposition vector
  passed in the actual Android WebView.
- Native Copy succeeded. Save cancellation returned to the app. Saving a uniquely
  named test file and reading it back preserved UTF-8 and mixed CRLF/LF exactly.
- Opening that same file through Android's document picker and encrypting it
  preserved the mixed newlines. The fixture remains in Downloads for inspection.
- Phone screenshot reviewed; no horizontal overflow at its 448 CSS pixel width.
  Opening the keyboard reduced the viewport from 930 to 554 CSS pixels without
  horizontal overflow. Native insets keep content clear of system bars.
- All 202 Python tests passed. The existing browser smoke suite passed across
  320, 390, 768 and 1440 CSS pixel widths, including six ciphers, four analyzers,
  offline operations, file downloads, errors and isolated sessions.

The device checks use Playwright over the beta's own debug WebView plus ADB for
its system document dialogs; they are not a substitute for human touch usability
testing, screen-reader testing or a wider device matrix.

## Five-case campaign follow-up

The campaign test APK includes `campaign.json` and all five mission files. It
built and installed successfully. With the phone locked, its debug WebView
verified all five cases, next-case navigation, reveal-versus-solved counts,
campaign completion and selected-case persistence after reload. Test progress
was removed and the original pre-test saves restored; Play was left open.
New campaign visual/touch behavior on an unlocked phone still needs review.
The original tools' browser regression suite and all 209 Python tests pass.

To repeat the WebView smoke check, unlock the phone, open the beta, obtain its PID
with `adb -s <serial> shell pidof io.drewclark.ciphercraft.beta`, and forward only
that app's debug socket:

```powershell
adb -s <serial> forward tcp:9224 localabstract:webview_devtools_remote_<PID>
.venv/Scripts/python.exe tests/smoke_android.py
adb -s <serial> forward --remove tcp:9224
```

Leave the app open for the user after testing. Do not change phone security or
network settings, inspect unrelated files, or erase app data to run these checks.

## Messenger checkpoint — November 24, 2026

The APK now includes INTERNET for the optional messenger. Actual Pixel WebView
HTTPS calls to Azure passed account creation, browser-to-phone cipher challenge
delivery, known-key decode/checksum success, encrypted reply and signout.
The phone was locked: DOM automation overrode page visibility for the test.
This does not verify physical touch, keyboard or background operation. Existing
local cipher/AI and lesson browser suites still pass. Both Android and ordinary
localhost:8502 preview use Azure by default; isolated API development uses
localhost:8502/?messenger=local with scripts/run_messenger.py on port8503.
