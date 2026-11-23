# Independent verification — November 23, 2026

Reviewed the locally trained cipher identifier, neural language scorer, data
separation, scoring integration, packaging and browser workflows. The model
weights and recorded benchmark results were not changed during this review.

## Findings fixed

1. A rejected file upload changed `fileMode` before decoding succeeded. If the
   previous message came from a file, a subsequent transform could use the
   textarea's normalized line endings instead of its preserved original bytes.
   Uploads now preserve the previous source and file mode on failure, reject
   empty files, and disable transform actions while reading. Errors explicitly
   state that the previous message was kept. Stale reads cannot replace newer
   input. Browser regression checks attempt malformed UTF-8, an empty file and
   an oversized file, then verify the original mixed CR/LF file round-trips and
   downloads with exactly its original bytes.
2. A one-character Rail Fence analysis returns no possible keys. The browser
   previously displayed a success announcement anyway. Empty candidate lists
   now produce an actionable message without a success heading or buttons.

The evaluation CLI also accepts `--output` to replay a benchmark into an audit
artifact without replacing the recorded report and its original timing data.

## Evidence

- Full Python suite: 186 passed and one hard-link test skipped by the filesystem
  sandbox; the exact skipped test passed separately with native filesystem
  access, using temporary files inside `dist/audit/`. All 187 tests were verified.
- Critical Python lint and `git diff --check`: passed.
- Held-out benchmark independently replayed to
  `dist/audit/language-model-replay.json`: all 384 generated cases matched the
  recorded inputs, keys and exact-recovery outcomes. Model hashes also match.
  Timing fields were intentionally excluded from equality checks.
- Learned scorer: 372/384 recovered messages versus 355/384 for the old scorer;
  Vigenère specifically: 84/96 versus 70/96. These are correlated synthetic cases
  from 48 passages, not 384 independent real-world puzzles.
- Full neural/table parity: all 17,576 contexts and 456,976 next-letter
  predictions checked. Maximum absolute cost error was
  0.0004999986102500742 nats, within the documented .001-nat quantization step.
  Maximum probability-mass deviation after quantization was 0.00047201825976783685.
- Numerical training-gradient spot checks: 50 coordinates across all five
  parameter arrays, including repeated embedding indices. Maximum absolute
  error against finite differences was 3.69e-11 (rounded up).
- Real Chromium worker checks passed with network disabled after startup:
  six cipher workflows, four key analyzers, cipher identification, learned
  scoring, keyboard interaction, exact file downloads, input invalidation,
  loading-error recovery, independent browser sessions and 320/390/768/1440-pixel
  layout checks. New upload/empty-analysis regressions passed too.

Training, validation and test source books are disjoint. The trained model is
still a small three-letter-context English scorer, not a conversational model.
The reports do not establish general cipher-breaking reliability. Firefox,
Safari, screen-reader compatibility and deployed-site performance were not
retested. This review does not publish or deploy the local changes.
