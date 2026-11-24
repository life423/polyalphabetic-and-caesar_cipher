# Optional standalone encrypted-link sharing

For the full account/inbox messenger and cipher challenges, see [Messenger](MESSENGER.md).
This document describes the no-account link-sharing fallback only.

## Flow

Messages has Send and Receive views. Send encrypts up to 2,000 UTF-8 bytes with
fresh random key/IV, then offers an encrypted link and a separate unlock key.
Native Android opens ACTION_SEND; supported browsers use Web Share, with Copy
link available everywhere. Give the key through a separate trusted channel.
Receive accepts a link/code and key, verifies/decrypts locally and renders text
with textContent. No sender identity or delivery confirmation is claimed.

Android registers as a text/plain share target. Share an incoming encrypted link
to CipherCraft Beta; cold-start and already-running intents feed the receive
view. Opening a URL normally opens the web app; verified Android App Links are
not configured. Pasting works on both platforms. A new incoming message clears
the previous received key and plaintext. Unrelated/malformed input is rejected.

## Format and trust boundaries

The v1 envelope has exactly `v`, `alg`, `iv`, `ct`. It uses AES-256-GCM, random
32-byte keys, 12-byte IVs, a 128-bit authentication tag and fixed additional
authenticated data `CipherCraft message v1`. Base64url encodes envelope/fields.
The key is a separate canonical 43-character base64url value, never in the link.
Each encryption generates a fresh key and IV; users cannot reuse or select IVs.

Web Crypto performs the cryptography. See [AES-GCM parameters](https://developer.mozilla.org/en-US/docs/Web/API/AesGcmParams)
and [encryption API](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/encrypt).
Sharing uses a user action; support varies, so Copy link remains available:
[Web Share API](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share).

The URL fragment carries ciphertext; the server receives no fragment. Startup
removes the fragment from the current history entry/address bar. External share
apps, browsers and recipients may retain the encrypted link. The app stores
neither plaintext nor keys in local/session storage. Clear removes current DOM
values and module references, not previously copied/shared content, browser
memory copies or the OS clipboard. Android marks copied keys as sensitive for
clipboard previews. Browser clipboard behavior is controlled by the OS/browser.

This first increment has no contacts, public-key identity, sender authentication,
forward secrecy, key recovery, expiry, revocation, relay, inbox or notifications.
Anyone with both link and key can decrypt it. It has not had an independent
security audit; do not market it as an audited messenger or Signal replacement.
The classical cipher/AI tools remain educational and are not used for this flow.

## Validation and release

The browser suite exchanges messages between isolated contexts and independently
checks the ciphertext using Node crypto. It covers wrong keys, modified IV or
ciphertext, invalid versions/fields, Unicode/multiline/HTML-as-text, size limits,
offline decryption, no message/key persistence, sharing without keys, clipboard
failure, fresh keys, clearing and asynchronous reset. Four viewport sizes and
automated WCAG checks cover Send and Receive. Existing cipher/AI, campaign,
Hash Lab, both lesson units and navigation suites run separately.

This work follows checkpoint commit 91b75a1 and is not committed or deployed.
Native links target cipher.drewclark.io; the sharing update must be deployed
before public browser links work there. Local web links use the preview origin.
A URL is not automatic delivery: users choose an installed sharing app.

Internal design review (judgment, not measured quality): usability 8, hierarchy 9,
accessibility 8, consistency 9, responsiveness 9, feedback 9, performance 8.
Next: paired-phone usability and key handoff testing, screen-reader review and
low-end-device timing. Prioritize these over decorative additions. Touch/browser
emulation and automated accessibility checks do not establish those outcomes.

### Connected Android verification

The refreshed APK built and installed successfully. On the Pixel WebView,
targeted ACTION_SEND tests passed for a cold start and an already-running
activity. The message decrypted locally; a second incoming message cleared
the old key/plaintext. The native listener regression is also in browser tests.
The phone was locked, so physical touch, choosing a recipient in the Android
share sheet and paired-phone usability remain unverified. No message was sent
to another person during these tests. APK assets were compared byte-for-byte
with current source.
