# Password-storage lesson

Inside Learn, choose **2. Password storage & salts**. Three gated steps teach:

1. Why a fast general-purpose hash permits cheap repeated password guesses.
2. Two fictional accounts with the same password: identical plain SHA-256 values,
   but independent 16-byte random salts and PBKDF2-HMAC-SHA-256 derived values.
3. Verification by re-deriving a guess with the stored salt and settings.

The browser performs real Web Crypto operations: 600,000 iterations, 256-bit
output. There is no backend authentication or message delivery in this lesson.
Use only the supplied fictional password or invented guesses.

PBKDF2 is supported directly by browser Web Crypto. This is a teaching choice:
[OWASP generally recommends Argon2id](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
Production systems should use maintained authentication libraries and tune cost
for their environment. See [MDN salt guidance](https://developer.mozilla.org/en-US/docs/Web/API/Pbkdf2Params).

Only quiz choices, step and practice completion are stored under
`ciphercraft.learn.password-storage.v1`. Guesses, random salts and derived values
remain in memory. Reloading requires fresh demo records before another check.
Completion remains practice progress, not verified assessment. The selected
lesson is an independent enum in `ciphercraft.learn.selected.v1`.

Reset affects only this unit. Asynchronous derivations are guarded so a reset
or edited guess cannot apply stale results. Unsupported crypto and derivation
failures have readable feedback. No new dependencies or paid services.

`tests/smoke_password_browser.py` independently checks generated values with
Python hashlib, wrong/right answers, verification, reload, reset, privacy and
layout overflow at 320, 390, 768 and 1440 pixels. Existing browser suites cover
the cipher/AI, campaign, Hash Lab, integrity lesson and navigation.
