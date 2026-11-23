# Our first locally trained language model

This is a small **neural next-letter language model**, trained from random
initial weights on this computer. It helps rank candidate decryptions in the
browser app's **Find key** and **Identify & crack** features. It is separate from the cipher-type
classifier, and it is not a general-purpose chatbot or large language model.
No pretrained model, model API, GPU or paid service is used.

## Architecture and inference

- Alphabet: 26 lowercase ASCII letters. Spaces, punctuation and non-ASCII
  characters are excluded for scoring, so unspaced cipher outputs are supported.
- Context: the previous three letters predict the next letter.
- Architecture: learned 8-dimensional letter embeddings, a 64-unit tanh hidden
  layer and 26-way softmax; 3,498 trained parameters.
- Training: our NumPy implementation of backpropagation and Adam, seed 901,
  24 epochs, up to 240,000 sampled training contexts. The checkpoint with the
  lowest validation negative log likelihood is retained (epoch 23 in this run).
- Ranking: average next-letter negative log likelihood, in nats. Lower is more
  English-like. These are language scores, not probabilities of a correct key.
  Samples of one to three letters use the training unigram distribution.

Every possible three-letter context can be evaluated in advance. Training
exports both the actual neural weights and a compressed table of its predicted
next-letter costs. The browser uses the table, quantized to .001 nats, instead
of repeatedly running matrix multiplications inside key search. Tests compare
table entries against the neural network within the quantization error.
This finite-context model is equivalent at inference to a learned four-letter
probability table; it does not understand arbitrary-length context.

`src/ai/english_language_model.json` is about 1.15 MiB. Inference uses standard
Python only and runs in the existing background worker, including while offline
after loading. No user text is cached in the model or used for online training.
NumPy is required only for training and optional numerical parity tests.

## Data and honest comparisons

We reuse the source-verified public-domain corpus described in
[CIPHER_IDENTIFICATION.md](CIPHER_IDENTIFICATION.md): three training books,
one validation book, and two test books by separate authors. SHA-256 fingerprints
are checked before training/evaluation. Downloaded books and their license
notices remain in ignored `.venv/training-corpus/`, outside deployment bundles.

The model learns to predict letters, not cipher labels. Test books do not train
the language model or select its checkpoint. On 16,000 sampled test next-letter
contexts, mean negative log likelihood is **2.231 nats**, compared with **2.886**
for a training-frequency unigram baseline. This checks whether context helps;
it does not establish superiority over a strong smoothed n-gram language model,
which remains a useful next benchmark.

We also compared the old scorer with the neural scorer on the **same ciphertexts
and search budgets**, using 48 held-out plaintext passages. Each passage produces
eight tests: four cipher types, preserving original formatting or retaining only
ASCII letters. These 384 cases are correlated variants of 48 passages, not 384
independent documents. Lengths are 80, 180 and 400 source characters. Vigenère
keys contain 2–8 random letters; Rail Fence uses 2–12 rails. Validation was checked
before running the test comparison. The test never selects model weights.

| Exact full-plaintext recovery | Previous scorer | Trained language model |
| --- | ---: | ---: |
| Caesar | 96/96 | 96/96 |
| Affine | 95/96 | 96/96 |
| Rail Fence | 94/96 | 96/96 |
| Vigenère | 70/96 (72.9%) | 84/96 (87.5%) |
| Overall | 355/384 (92.4%) | 372/384 (96.9%) |

Correctness means the complete recovered plaintext equals the expected message,
including formatting retained by that cipher. Rail Fence removes whitespace,
so its expected plaintext reflects that behavior. Equivalent keys that produce
the correct plaintext count as successes. Wrong outputs count as failures even
if they look plausible.

Reports include per-case results, source positions, generated keys, timing,
dataset fingerprints and matching model hashes:

- [Training and held-out next-letter loss](LANGUAGE_MODEL_TRAINING.json)
- [Validation cipher comparison](LANGUAGE_MODEL_VALIDATION.json)
- [Held-out cipher comparison](LANGUAGE_MODEL_TEST.json)

The gains are measured on this small synthetic English-literature benchmark.
They do not establish general cipher-breaking accuracy. Twelve Vigenère cases
still fail. Short, unusual, non-English, random or unsupported inputs may score
misleadingly. The model has only three letters of context and has no semantic
understanding, instruction-following ability or factual knowledge.

## Train, sample and evaluate on your machine

From the repository root:

```bash
python -m pip install -e ".[train]"
python -m scripts.train_language_model
python -m src.ai.language_model --prompt the --length 120
python -m scripts.evaluate_language_model --split validation --passages 12
python -m scripts.evaluate_language_model --split test --passages 24
```

Sampling prints an unspaced letter sequence as a next-letter diagnostic, not a
chat response. Reproducing the reports requires matching corpus files. The
recorded run used Python 3.13.7, NumPy 2.5.5 and `OPENBLAS_NUM_THREADS=1`.
Different numerical-library builds can produce different floating-point weights.
Do not repeatedly tune against the existing test books; add a fresh held-out
set for future model selection.

## Integration and verification

`NeuralCipherAnalyzer` reuses the existing key-search algorithms with learned
plaintext ranking. The web adapter uses it for Caesar, Affine, Rail Fence and
Vigenère. The existing desktop/CLI `CipherAnalyzer` stays available as the
baseline. Both static and Streamlit deployment packages include the model;
training code and corpus files are excluded. Existing desktop binaries are not
changed by this source work.

Tests check distribution normalization, neural/table parity, formatting
normalization, context sensitivity, short-input behavior, reproducible sampling,
global random-state isolation, model/report hashes and disjoint source books.
Browser checks exercise the real model offline, select a suggested key and
decrypt, and inspect phone/tablet/desktop layouts. The UI identifies the scorer
and describes guesses as suggestions. Key suggestions appear before the empty
output field and receive keyboard focus when ready, so mobile users do not have
to scroll past an unused text box to find the model's results.

Further work should benchmark modern prose, short puzzle text, other languages
and unsupported inputs, then compare a strong count-based n-gram baseline.
Increasing context or adding a substitution-key search should be measured as
separate experiments. No live-site deployment is implied by local training.
