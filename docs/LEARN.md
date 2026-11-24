# Learn: hashes and file integrity

The first Learn unit, **Can you trust this file?**, is a three-step, self-paced
lesson using the established navy/teal interface and the shared SHA-256 helper.
It introduces concepts, runs a real experiment, then asks the learner to identify
altered evidence and interpret what a mismatch proves. It is not a teacher
dashboard, formal assessment system or a complete cryptography curriculum.

## Lesson flow

1. Understand: distinguish hashing from reversible encryption and check that
   identical bytes produce identical SHA-256 digests. Incorrect answers provide
   explanations and can be retried without penalties.
2. Experiment: hash `Meet at dawn.` and `Meet at Dawn.` on the device. Their digests
   differ in 129 output bits. The question reinforces that the count varies; it
   is not always exactly 128 bits.
3. Investigate: hash three original fictional harbor records against a trusted
   record, identify the mismatch, and select a valid conclusion. Merely naming
   the altered file does not complete the lesson: the learner must also recognize
   that the hash alone cannot establish authorship, motive or safety.

The exercise explicitly assumes the keeper supplied the expected digests in
person. Two delivered files match. `beacon-order.txt` has a changed instruction
and differs from the trusted digest. Lesson content and bytes are bundled,
original, and independently verified by Python's hashlib. `.gitattributes`
prevents Git newline conversion from altering the evidence across platforms.

## Integration and state

Learn is a fifth top-level workflow. Keyboard arrows/Home/End cover the five
tabs; the lesson's three steps use their own tab controls. **Practice in Hash
Lab** opens the existing lab without changing its text, selected file, expected
digest or result. **Back to lesson** returns to the current step. Evidence can
be downloaded for manual lab use; Android uses the existing system Save picker.
Web downloads preserve exact fixture bytes.

The isolated key `ciphercraft.learn.hash-integrity.v1` stores only this unit's
choices, checked answers, observed-file IDs and current step. It does not store
uploaded files or personal messages. Previously observed hashes are recomputed
from actual bundled bytes after reload; stored digests are never trusted. Reset
requires a confirmation and clears only lesson progress. Revision guards prevent
pending hashes from restoring observations after reset. Unavailable storage
shows an explicit session-only notice. Progress is self-reported practice, not
a verified grade or certificate; browser state is not an anti-cheat boundary.

The lesson module loads lazily and does not depend on the cipher worker. Missing
assets show a retry state while the existing workflows remain usable. All lesson
files are loaded together, permitting offline steps after initial loading.
Android includes the complete unit; the web app still has no offline reload
cache. A missing secure-context crypto API permits reading but disables hashing.

## Validation

- All 211 Python tests and critical lint pass, including independent expected
  digest checks and exactly one evidence mismatch.
- All four browser suites pass: original cipher/AI workflows, five-case campaign,
  Hash Lab and Learn. Learn coverage includes wrong/empty answers, interpretation
  errors, real digests, exact downloads, offline steps, lab/campaign isolation,
  progress/reload/reset, storage and asset errors, corrupt saves, and reset races.
- Captured 320/390/768/1440 CSS pixel states show no horizontal overflow.
  Representative phone, tablet and desktop renders were reviewed. Phone step
  tabs were made more compact after review. Axe found zero issues under its
  WCAG A/AA rules on the lesson and evidence screens, not a full accessibility
  or screen-reader audit.
- Android APK built and installed. The actual Pixel WebView completed the lesson,
  calculated all evidence hashes, checked the conclusion and restored completion
  after reload, without internet permission. Test saves were removed and the
  previous Learn state restored. The phone was locked: native visual/touch and
  the new lesson's system Save dialog remain pending checks.

Internal design review (judgment, not measured quality): usability 8, hierarchy 9,
accessibility 8, consistency 9, responsiveness 8, feedback 9, performance 8.
Prioritize novice/teacher comprehension tests, unlocked phone and landscape
checks, screen-reader feedback and radio navigation, and lower-end performance
measurements. No Core Web Vitals or paid-demand validation is claimed.

Implementation is on `codex/hash-integrity-lesson`, alongside the uncommitted
Hash Lab work. No merge or deployment is implied by local verification.

## Lesson chooser

Learn includes a native select for the integrity and [password-storage](PASSWORD_LESSON.md)
units. Each has separate local progress. Selection is remembered without adding
a main navigation tab. Current work is uncommitted on `codex/grouped-navigation`.
