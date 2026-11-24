# CipherCraft messenger beta

## Play together

Messages now contains sign-in, an inbox and one-to-one conversations. Create an
account, tell a friend your exact username, and start a conversation with theirs.
The default is **Cipher challenge**: choose Caesar, Vigenere, Rail Fence or Affine,
enter a key and message, and optionally add a hint or hide the cipher name.
The recipient sees ciphertext and can **Decode** with a key or **Try AI**.
AI suggestions are guesses; automatic identification works best on longer
English messages. Short or difficult ciphertext may not produce a useful key.

A correct decoding is checked on-device against a checksum inside the encrypted
challenge and gets “You cracked it!” feedback. This is sender-authored practice,
not a certified assessment or a server-verified score. Rail Fence deliberately
removes whitespace, matching the existing cipher tools; the composer explains
that before sending. The checksum is of the actual core cipher round trip.
Ordinary encrypted messages and replies are available in the same composer.

Keys for the classical challenge are never included in its payload. The sender
can communicate a puzzle key separately, or leave the recipient to solve it.
Conversation encryption is separate and automatic after account sign-in.
The older encrypted-link flow remains under **Share a link without an account**.

## Runtime and data

- Frontend/AI: bundled static app; existing Python/WASM worker now has a separate
  request map for chat operations so it does not overwrite the cipher tools.
- API: Python WSGI service in `src/messenger`, SQLite and gunicorn. Existing Azure
  App Service `ciphercraft-drewclark`, F1 Free, is reused. The separately hosted
  main website is not replaced by this API deployment. Original Streamlit remains
  available locally; its old automatic deployment now requires explicit opt-in.
- Local preview: static app at localhost:8502, Azure API by default, matching the Android app so they can exchange messages.
  For isolated development use `localhost:8502/?messenger=local` plus
  `python scripts/run_messenger.py` on localhost:8503.
- Native INTERNET permission supports messaging. Ciphers, AI, lessons and campaign
  remain bundled and run offline. No new storage, contacts, SMS or microphone
  permissions are requested. A cloud conversation requires a connection.
- Foreground refresh every five seconds, unread counts, replies and block/unblock.
  Polling pauses when Messages is hidden or the app is in the background. No OS
  push notifications, background delivery promise or delivery/read receipts yet.
- Accounts, conversation membership, message timestamps/sizes, block/read state,
  public keys and encrypted backups are server-visible metadata. Message content,
  challenge hints/keys and solutions are not sent as plaintext.
- Session tokens and unlocked private keys remain in memory; refresh requires
  sign-in. Only public-key trust fingerprints persist locally. Signing out clears
  visible messages/keys/drafts and revokes that session. It cannot guarantee
  erasure of runtime/browser memory copies or previously shared material.

## Encryption and trust

The browser generates a P-256 ECDH identity. A random-salt PBKDF2-HMAC-SHA-256
600,000-iteration key encrypts its backup with AES-256-GCM. The raw password is
never transmitted: sign-in sends a separate domain-separated PBKDF2-derived
secret, which the server hashes again with an independent salt and 600,000
iterations. The authentication secret does not unwrap the identity backup.
No password recovery, account deletion or key rotation is implemented in this
beta; lost passwords cannot recover history. These are release prerequisites
for a broadly offered consumer service, alongside abuse/reporting controls.

Per-conversation ECDH secrets feed HKDF-SHA-256 with a conversation-specific salt.
Each message uses a random 96-bit IV and a 128-bit GCM tag. Authenticated data
binds protocol version, conversation and sender IDs. Keys are imported as
non-extractable once unlocked. The encrypted envelope is exactly `{v,iv,ct}`;
transport payloads never contain raw challenge keys.

Public keys are immutable server-side. Compare both fingerprint codes through a
trusted channel to check initial identity. Stored public fingerprints detect a
changed peer key and pause send/decrypt until explicitly verified. First-contact
identity is not automatically verified. This custom protocol has no forward
secrecy or post-compromise recovery and has not been independently audited. Do
not market it as an audited secure messenger or a replacement for Signal.

References: [Web Crypto key derivation](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey),
[ECDH parameters](https://developer.mozilla.org/en-US/docs/Web/API/EcdhKeyDeriveParams),
[HKDF parameters](https://developer.mozilla.org/en-US/docs/Web/API/HkdfParams).

## Hosting and operations

The backend ZIP allowlist excludes frontend files, local plans, credentials and
SQLite data. Database `/home/data/cipher-messenger.sqlite3` survives application
code deployment/restart; hosted persistence must be verified after provisioning.
DELETE journaling and one gunicorn worker avoid WAL shared-memory requirements
on the shared Azure filesystem. Multiple instances or a public-scale rollout
need a managed database and an operational review.

No hosting tier was upgraded. Free App Service has limited CPU and no uptime
SLA; sleeping/cold starts are expected. Storage caps are 500 accounts and 20,000
messages. Durable rate limits, exact-origin CORS and authenticated member checks
apply. The API records no request-body/credential logs. TLS is required.

The standalone API is deployed independently. The main cipher.drewclark.io
frontend still needs the new source committed/deployed; a locally rebuilt APK
can talk directly to the hosted API. Keep the old Streamlit rollback ZIP out of
source control. Preserve and back up database storage separately from app ZIPs.

## Verification and remaining work

Python tests cover credentials, session revocation/expiry, membership isolation,
invalid public keys/envelopes, persistence, concurrent idempotent retries, block
checks, pagination, read/unread state, rate limits and storage caps. Independent
Node crypto verifies ECDH/HKDF/GCM interoperability, backup/auth separation and
wrong-password/identity/context/tamper rejection. Browser tests exercise two
real accounts, replies, key decoding, known/hidden-cipher AI, all four challenge
ciphers, backup login, block/unblock, offline drafts and absence of plaintext or
passwords in API payloads/storage. Responsive renders cover 320/390/768/1440px.
Automated WCAG checks are evidence for the tested states, not a full audit.

Internal review heuristics (not measurements): usability 8, hierarchy 9,
accessibility 8, consistency 9, responsiveness 8, feedback 9, performance 8.
Priorities: paired human play/key handoff testing, screen readers, real mobile
keyboard/landscape, slow-network/cold-start feedback and representative device
latency. Also add account deletion/recovery design, abuse reporting and an
independent protocol review before a public paid messenger launch.

### Verified checkpoint — November 24, 2026

219 Python tests and critical flake8 pass. All nine browser suites passed across
the increment, including the complete messenger flow against both local and
hosted APIs. HTTPS browser CORS, hosted writes, App Service restart and durable
identity/history recovery passed. The refreshed APK installed on the Pixel.
An actual WebView-to-browser exchange through Azure passed: signup, receive a
challenge, known-key solve and checksum feedback, encrypted reply and signout.
The locked-phone check used DOM automation and a visibility override; physical
touch, keyboard ergonomics and background notifications were not established.
Phone/tablet/desktop screenshots were reviewed; automated WCAG found no issues
in the tested conversation state. APK assets match source byte-for-byte.

The API is deployed on the existing F1 plan; no pricing tier changed. The main
custom-domain frontend is not deployed. Current source is uncommitted on
`codex/encrypted-message-sharing`; checkpoint commit 91b75a1 remains the prior
lesson/navigation work. The private student plan and local Azure CLI cache are
ignored and are not part of any deployment package.

## Main release

The messenger source, campaign and lesson/navigation checkpoints are being
published together on main. Static and API workflows verify and deploy their
respective packages. Earlier statements about uncommitted/undeployed frontend
work describe the pre-release checkpoints above. The private student plan,
local Azure CLI cache and APK/database artifacts remain outside source control.
