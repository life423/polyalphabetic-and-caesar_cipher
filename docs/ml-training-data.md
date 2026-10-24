# Offline ML training data — Step 1

This prepares **labeled examples for future machine-learning experiments**.
It does **not train a model**, modify the desktop application, or use a remote API.
Python's standard library and CipherCraft's existing six cipher implementations
are the only dependencies.

## Try a local smoke test

Run at the repository root:

~~~bash
python -m src.ai.training_data \
  --demo \
  --output-dir generated_datasets/demo-v1 \
  --samples-per-class 30 \
  --seed 2026
~~~

This writes **180 examples total**: 30 of each of the six classes, split
roughly 80%/10%/10% for training, validation and test. All files are plain
JSONL or JSON, and no data is downloaded.

The 20 original passages in src/ai/demo_corpus.py are ONLY for pipeline
validation. Training a real classifier on such a tiny corpus would produce
misleading results. A **large, diverse, legally usable plaintext corpus** is
required before training and benchmarking.

## Generate a larger local dataset

Provide UTF-8 text documents under a local folder such as local_corpora/.
Each .txt file is treated as a distinct **document group**; files should
contain original/licensed material and be reasonably long, with different
topics, styles, and writers where possible.

~~~bash
python -m src.ai.training_data \
  --corpus-dir local_corpora/ \
  --output-dir generated_datasets/v1-120k \
  --samples-per-class 20000 \
  --seed 2026 \
  --min-length 64 \
  --max-length 192
~~~

This *requests* **120,000 examples (20,000 per class)**. Actual generation
requires enough distinct plaintext windows; if the corpus is too small it
stops with an error instead of silently repeating passages. Use a new output
directory for every run — existing directories are never overwritten.
These local folders are .gitignored, not uploaded to GitHub.

## Output contract

| File | Purpose |
| --- | --- |
| train.jsonl | Classifier training examples |
| validation.jsonl | Hyperparameter selection and checkpoint validation |
| test.jsonl | Holdout evaluation; keep untouched until final evaluation |
| *_answers.jsonl | Plaintext, keys, source IDs, SHA-256 verification; **not model inputs** |
| manifest.json | Generator version, labels, split counts, source hashes, warnings |

Classifier row example (illustrative):

~~~json
{"sample_id":"train-0000001-caesar","group_id":"train-0000001","ciphertext":"KHOORZRUOG","label":"caesar"}
~~~

**Only ciphertext should be passed into the classifier.**
The label field is the supervised learning target. sample_id and group_id
help tests and audits, not model features. Keys and plaintext are in separate
answer files.

## How we prevent misleading performance claims

- Whole **documents** are assigned to only one of train/validation/test
  *before* windows are selected. Identical normalized documents are rejected.
  Distinct plaintext windows are used across all splits. Near-duplicate
  documents still require independent deduplication.
- Every plaintext **group** generates one example of *each* cipher. This
  means each class has an identical plaintext length and topic distribution.
- All ciphertext is **uppercase A–Z without spaces or punctuation**.
  Columnar transposition keys divide the plaintext length exactly, avoiding
  a padding X shortcut that would otherwise leak the cipher label.
- Caesar keys are 1–25, Vigenère keys are multi-letter, and Affine multipliers
  exclude 1 so generated Affine examples don't collapse into Caesar.
- --seed makes files byte-for-byte reproducible for identical inputs and
  relative document names. SHA-256 of source material is in the manifest.

**Important limitations:** Classical cipher families share mathematical
properties. Some texts are genuinely ambiguous, particularly short messages.
Synthetic data can also make the classifier learn properties of this generator
rather than real-world encrypted messages. Track a realistic held-out corpus,
lengths outside the training range, language variety, frequency baselines,
and calibration before reporting accuracy.

This project is educational cryptanalysis, **not secure encryption**.
