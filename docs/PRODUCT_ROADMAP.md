# CipherCraft product direction

## Approved goal — November 23, 2026

Build an interactive codebreaking experience while preserving the existing
Crack a message and Encrypt / decrypt tools, their locally trained AI, and
offline Android operation. The new Play workflow owns its mission state and
never overwrites tool messages, keys, files or results.

Deliver in small increments on a separate branch; test web and Android before
merge. Preserve the established navy/teal design and accessible mobile controls.

1. One complete mission: an interactive letter-mapping board, guesses, undo,
   reset, answer checking and a satisfying story conclusion.
2. Progressive hints grounded in cipher evidence. Clearly distinguish authored
   clues from model-based analysis; never claim generated explanations are AI.
3. A five-mission campaign with local progress and an original mystery story.
4. Puzzle creation and sharing after validating the core play experience.
5. Paid case packs only after playtests and purchase experiments establish demand.

The initial commercial hypothesis is a free introduction with a one-time paid
campaign. Suggested prices are experiments, not evidence of willingness to pay.
The first validation target is a polished, roughly 15-minute mystery tested with
ten puzzle enthusiasts; observe completion, requests for hints and willingness
to buy a follow-up. Do not add payments or deploy merely because of this plan.

## Messenger idea — proposed, not approved for implementation

The user proposed sending encrypted messages between app users. Investigate
**secret challenges** and collaborative puzzles: a friend decrypts a note using a
shared key or solves it with optional hints. Start by evaluating a shareable file
or link before accounts, servers, push notifications or an in-app inbox.

Paid group puzzle packs, treasure hunts and collaborative mysteries are possible
extensions. Ordinary encrypted chat alone has no validated commercial demand.
Classical puzzle ciphers must never be marketed as secure private messaging.
Actual confidential messaging would require a separate modern security design.

## First increment

The Observatory Note is a single original introductory mission. Its ciphertext
is generated and checked against the existing Caesar engine. Authored clues cite
actual repetitions and frequencies. Gameplay is independent of engine startup;
all assets ship inside the web and Android builds. Only versioned mission
progress is saved locally; tool messages and keys retain their existing behavior.

This is a prototype mission, not the five-mission campaign or a validated paid
product. Wider device, assistive-technology and human playtesting remain release
work. Keep validation results and concrete shortcomings here as work progresses.

### First increment validation

Developed on `codex/first-codebreaking-mission`. On November 24, 2026 the user
approved committing the work, merging and pushing to main, and deploying it to
cipher.drewclark.io. The Android wrapper ships alongside this increment. The
default workflow remains Crack a message. Production rollout uses the existing
Custom Domain workflow, which now verifies both tool and Play browser suites
before deploying.

- 203 Python tests pass, including matching the mission to the existing engine.
- Existing browser regression suite passes: all six ciphers, four analyzers,
  file processing, clipboard/downloads, offline operation and session isolation.
- New Play browser suite passes: guided first move, lowercase input, repeated
  letter updates, duplicate/invalid guesses, undo/reset, clues, incorrect-answer
  rejection, completion, reveal distinction, persistence, tool state isolation,
  loading failure/retry, unavailable storage and 320/390/768/1440 CSS pixel widths.
- Phone, tablet and desktop screenshots reviewed. Axe found zero violations
  for its WCAG A/AA rules on the guided Play screen; that is not a complete
  accessibility audit. Keyboard tab navigation was also exercised.
- Updated APK built and installed on the Pixel 10 Pro XL. The original native
  smoke checks pass. Play's first move, saved progress after reload, mapping and
  completion pass in the real Android WebView without internet permission.
- The actual Android keyboard reduced the viewport to 554 CSS pixels. The
  sticky note occupied approximately y=15–215 and the active input began at
  y=431, with no horizontal overflow. Screenshot reviewed. Tests restored the
  pre-test mission state and left Play open for later testing.

Internal design review (judgment, not measured product quality): usability 8,
hierarchy 9, accessibility 8, consistency 9, responsiveness 8, feedback 9,
performance 8. Prioritized follow-up: observe novice players completing the
first case; reduce any tedious letter entry based on that evidence; verify
screen-reader pronunciation and reading order; test landscape/smaller keyboards
and older WebViews; measure load/interaction performance on lower-end phones.
Commercial demand and whether the mission is fun remain unvalidated.

The user's later clarification was that they were tired, not reporting a
specific inability to understand the puzzle. Do not treat that comment as a
failed usability test. The guided first move is an implementation choice that
still needs human validation.
