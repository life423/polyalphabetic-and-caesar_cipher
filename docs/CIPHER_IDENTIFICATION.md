# Cipher identification: first trained model

CipherCraft now includes an experimental **Identify cipher** action in the static
browser app. It ranks three likely types among Caesar, Vigenère, substitution,
columnar transposition, Rail Fence and Affine. Selecting a result changes the
cipher controls; the existing **Analyze cipher** action still searches for keys.
Identification itself needs neither a selected cipher nor a key. It does not
automatically decrypt, replace user input or claim to recover a key.

## What we built

This is our own trained neural network, not a paid API, downloaded pretrained
model or relabeling of the existing analyzer. We generate ciphertext with our
existing implementations, extract 133 statistical features, and train a small
48-unit tanh hidden layer with six output scores using our NumPy training code.
Features include letter frequencies, coincidence rates, entropy, repeated-key
periodicity, bigrams and frequency fits for Caesar/Affine transformations. It is
a learned classifier built on cryptanalytic features, not a language model.

Weights live in `src/ai/cipher_identifier.json` (about 141 KiB). Inference in
`src/ai/identifier.py` uses only standard-library Python and runs in the existing
Pyodide worker. The model is bundled into `engine.zip`, served from our own
origin and usable without a connection after startup. Messages, keys and files
stay on the device. NumPy is required only for local training.

## Data and evaluation

Public-domain literary texts come from GITenberg's Project Gutenberg mirrors.
The report records each download URL, book ID and full-file SHA-256. Original
files and their license notices stay in ignored `.venv/training-corpus/`; raw
books are not shipped with the app. Headers/license boilerplate and the first
and last 5,000 letters are excluded from examples.

| Split | Books | Ciphertext examples |
| --- | --- | ---: |
| Training | Pride and Prejudice; The Adventures of Sherlock Holmes; Frankenstein | 5,076 |
| Validation | Alice's Adventures in Wonderland | 390 |
| Held-out test | The Time Machine; The Adventures of Tom Sawyer | 1,362 |

Books and authors are separated between splits. Every plaintext window yields
six cipher examples, so the test contains **227 plaintext windows**, not 1,362
independent passages. Windows do not overlap within a book. Case, punctuation
and whitespace are removed before encryption, so the model cannot identify a
cipher merely from the generator's formatting. Random keys and sample lengths
of 100, 150, 250, 400, 700 and 1,200 letters are used.

The checkpoint is selected by validation loss over 120 epochs; test results
never select weights. On this synthetic held-out test:

| Measure | Result |
| --- | ---: |
| First suggestion correct | 89.43% |
| Correct type somewhere in the three suggestions | 99.93% |
| Simple nearest-centroid baseline, same features | 82.01% |
| Columnar transposition first suggestion correct | 67.84% |
| Rail Fence first suggestion correct | 77.53% |

These are benchmark measurements, **not probabilities for a user's message**
or evidence of equivalent performance on arbitrary real-world ciphertext.
Full confusion matrices, accuracy by length, provenance and the matching model
hash are in [IDENTIFIER_EVALUATION.json](IDENTIFIER_EVALUATION.json).

## Limits

- English prose only; require at least 100 ASCII letters and at most 5,000
  characters. Typed samples are treated as one message. Files use the line
  containing the most ASCII letters because file ciphers reset each line.
- Training covers Vigenère key lengths 2–16, Rail Fence 2–20 and column counts
  2–16. Other keys may work but have not been established by this benchmark.
- The training sample lengths stop at 1,200 letters; the larger UI limit is a
  resource bound, not a claim of measured quality across every allowed length.
- Caesar is a special case of Affine, and both are substitution ciphers. Some
  transposition and Rail Fence keys also produce identical outputs. Encryption
  history cannot always be determined from ciphertext alone.
- The model always ranks within its six known types. Plain English, random
  strings, non-English text, unknown ciphers and repeated text can be wrongly
  ranked. The UI makes no calibrated confidence or general cipher-breaking claim.

## Reproduce locally

```bash
python -m pip install -e ".[train]"
python -m scripts.train_identifier
python -m pytest tests/test_identifier.py -q
```

The measured run used Python 3.13.7, NumPy 2.5.5 and seed 423. Matching cached
source files are needed to reproduce the report; source-hash mismatches stop
training for review. Training does not upload user data. No corpus download or
training is required in CI or at runtime; CI tests the checked-in model.

## Interface verification and next improvements

Automated Chromium checks cover identification while offline, independence from
the selected cipher/empty key, selecting a type then recovering a key and
decrypting, short-input errors, source-change invalidation, keyboard access and
320/390/768/1440-pixel layouts. Existing cipher/file workflows remain covered.
Screenshots show identification above the transformed-message field, so the
shortlist does not hide below an empty output box.

Internal review priorities: reliability 8/10 (improve transposition separation
and test unsupported-input rejection), accessibility 8/10 (manual screen-reader
verification remains), hierarchy/consistency/responsiveness/feedback 9/10 based
on the rendered checks. These are review heuristics, not measured user ratings.
Next work should add independent modern prose and real puzzle cases to an
untouched test set before tuning further. Safari/Firefox and assistive-technology
testing remain pending; do not broaden success claims from Chromium alone.
