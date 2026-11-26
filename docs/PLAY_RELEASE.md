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

## First internal release published

Version `0.1.0`, code `11`, is available to internal testers. The owner-only
email list contains drew@drewclark.io. Join link:
<https://play.google.com/apps/internaltest/4699221079626521322>.
Google may show the temporary package-based name until the app is reviewed.

Signed CI run `45752710333` passed all Android build/emulator/signature checks.
It produced two native 1080×1920 screenshots. Store description, icon, feature
graphic, screenshots, category and support details were saved. Privacy, no ads,
non-government, no-financial-feature and no-health-feature declarations are saved.
The Data safety questionnaire is completed and saved for review. Do not claim
production approval.

The owner approved ages 13 and older and IARC terms acceptance. The IARC
questionnaire is saved: ESRB Everyone / Users Interact, PEGI 3 / Users Interact,
with regional variants. These content ratings are separate from the intended
13+ audience. Responses disclose text interaction and blocking, and do not claim
in-app reporting, chat moderation or friend-only interaction limits.

App trader status was confirmed using the developer account's existing trader
declaration. No account-level trader details were changed. Two ordinary reviewer
accounts (`play_reviewer_a` and `play_reviewer_b`) passed login/key-backup checks
and were denied administrator access. Their private passwords are outside the
repository. With explicit owner approval, both passwords and English instructions
were saved in Google's reviewer-only Sign in details form. The optional wider
feedback use on Google/trusted partner devices is off. The audience is saved as
13–15, 16–17 and 18+. Data safety discloses optional user IDs, in-app messages,
interaction records and device IDs, secure transport, and the account-deletion
URL; service-provider transfers use Google's sharing exemption.

Public Terms of Service: <https://cipher.drewclark.io/terms>. Terms and privacy
links are visible in the app. Messages requires an unchecked 13+/Terms checkbox
before login or registration; sign-out and successful login clear the form.
Offline tools remain accessible. This is a client consent step, not verified
age identification or a server-side consent ledger. Existing internal build 11
predates the checkbox; distribute the updated signed build before closed testing.

Verification: all 245 Python tests, full messenger/deletion browser regressions,
consent-before-authentication checks and public legal pages at phone/tablet/desktop
sizes and enlarged phone text pass. Internal design-review heuristics: hierarchy
9, consistency 9, responsiveness 9, feedback 9, accessibility 8.5 and usability
8.5. Remaining follow-ups are native screen-reader/keyboard checks and a concise
legal review; these are not measured usability scores or policy approval.

Play reported two nonblocking diagnostics warnings: no obfuscation mapping file
(release minification is disabled) and no native dependency debug symbols.
No signing password, private key or administrator login is in the repository.
