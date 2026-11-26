# Google Play internal-test release

CipherCraft was created under the drewclark.io developer account on November 25,
2026. App ID: `4972287139354057929`. Package:
`io.drewclark.ciphercraft.beta` (matches the existing Firebase Android client).
Free download with possible paid features later is the owner's chosen model.

The Android workflow accepts a manual `sign_release=true` dispatch on main.
It builds and tests first, then signs `dist/CipherCraft-play-internal.aab` with
the dedicated upload key. Version codes use the increasing workflow run number.
Normal push/PR builds remain unsigned; no automatic Google Play rollout occurs.
Release signing does not use the debug certificate. Google Play App Signing
manages the installed application's separate signing key.

Private upload key and password are stored with restricted permissions at
`%USERPROFILE%/.ciphercraft-signing/` and as encrypted GitHub Actions secrets
`ANDROID_UPLOAD_KEYSTORE_BASE64` and `ANDROID_UPLOAD_PASSWORD`. Never commit,
print, or attach them to workflow artifacts. Keep a separate secure owner
backup; replacing the upload key later requires Play's reset procedure.

Public privacy policy: <https://cipher.drewclark.io/privacy>.
Account deletion: <https://cipher.drewclark.io/delete-account>.
Owner-approved public support/privacy email: drew@drewclark.io.

Internal testing is the first distribution target. Console production access
requires a closed test with at least 12 testers opted in continuously for 14
days. Neither automated tests nor internal testers replace that requirement.
Store declarations must match the implementation; messaging safety/reporting,
target-audience review and policy compliance remain production release work.
