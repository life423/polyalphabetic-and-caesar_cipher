# Hash Lab

Hash Lab is a separate workflow beside the cipher tools and campaign. Its
lazy-loaded module uses the browser's SHA-256 implementation, independent of
the Python worker, trained models and saved campaign state. It adds no runtime
dependencies or backend endpoints. Inputs and results are held in memory only.

The digest and bit conversion live in `static/sha256.js`, shared with Learn's
guided integrity lesson. The existing lab behavior is unchanged. Learn can open
the lab and return to its lesson without injecting or overwriting lab inputs.

## Operations

- Text: UTF-8 encoding, including whitespace, case and empty input. Up to 100,000
  JavaScript string code units per box, consistent with HTML maxlength behavior.
  Textarea line endings follow browser normalization. Use File for original bytes.
- Comparison: two SHA-256 digests and their exact 256-bit Hamming distance. An
  optional 16-by-16 view underlines differing bits as well as changing their color.
- File: original bytes of any file up to 20 MiB, including binary and empty files.
  No text decoding, trimming or newline conversion. An optional expected digest
  accepts 64 hex characters, case-insensitively, with surrounding whitespace.
- Copy: existing native CipherFiles plugin on Android; Clipboard API on the web.
  Failure preserves a selectable digest for manual copying.

SHA-256 is not decrypted. The lab distinguishes digest equality from source
authentication and file safety. It does not implement password storage or claim
that a plain fast hash is appropriate for passwords. The avalanche explanation
says "often about half", not a guaranteed fixed percentage.

The built-in example changes `Meet at dawn.` to `Meet at Dawn.`. The independently
checked result differs in 129 of 256 output bits (50.4%).

## Boundaries and recovery

SubtleCrypto requires a secure context (HTTPS or localhost). Unsupported browsers
show an explanation with hashing controls disabled. Failed module loading can
be retried with a fresh module URL, without reloading or erasing other workflows.
Input revisions guard asynchronous reads/digests against stale results. Editing
text or changing files hides obsolete results; editing only the expected digest
rechecks the existing file hash without reading the file again.

The file size limit bounds memory because the browser digest API accepts the
whole input rather than a stream. A future large-file implementation would need
a separately verified incremental SHA-256 implementation, not concatenation of
per-chunk digests.

## Verification

Run `tests/smoke_hash_browser.py` against a static preview on port 8502. It checks
known vectors, UTF-8 and byte counts, empty input/files, bit differences, exact
binary bytes and mixed newlines, expected-digest validation, uppercase input,
oversize rejection, asynchronous input changes, clipboard errors, unavailable
crypto, failed module retry, offline operation and isolation from campaign and
cipher work. It captures 320/390/768/1440 CSS pixel layouts.

The original cipher/AI browser suite, five-case campaign suite, 209 Python tests
and critical lint pass. Representative phone, tablet and desktop renders were
reviewed. Axe reports zero findings for its WCAG A/AA rules on both hash modes;
this is not a complete accessibility audit or screen-reader test.

The Android beta built and installed successfully. On the locked Pixel's actual
WebView, SHA-256 vectors, comparison, native Copy, byte-exact File objects,
expected-hash matching/mismatch and no horizontal overflow passed. These checks
do not establish unlocked-phone touch/keyboard behavior or the real Android
document picker for this new input. Those remain pending.

Internal design review (judgment, not measured product quality): usability 8,
hierarchy 9, accessibility 8, consistency 9, responsiveness 8, feedback 9,
performance 8. Follow-up priorities: unlocked-phone and real file-picker checks,
screen-reader navigation, novice comprehension and lower-end device performance.
No Core Web Vitals result is claimed.

## References

- [Browser digest API and memory constraints](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest)
- [NIST Secure Hash Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)
- [NIST guidance on integrity and authentication](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175Br1.pdf)
