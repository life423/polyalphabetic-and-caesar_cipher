# CipherCraft web interface

## Workflows

The default **Crack a message** workflow shows ciphertext input, an upload action,
an example and a single prominent **Identify & crack** action. Cipher/key controls
are hidden because automatic recovery does not need them. Input limits remain
100+ ASCII English letters and at most 5,000 characters for automatic search.
The supported-cipher and file-processing explanation is available in a native
disclosure, rather than a permanent instruction banner.

**Encrypt / decrypt** exposes the six ciphers and their appropriate key fields.
Encrypt and Decrypt are the main manual actions; Find key is shown only for
supported searches. The two workflows share their message, file contents, key
and result. Switching workflows does not erase a useful result or its text
selection. A workflow change invalidates pending requests so an older operation
cannot unexpectedly update the newly selected workflow.

## Result presentation

The separate **Play** tab opens a lazy-loaded mission module and its own panel.
Its versioned progress is stored locally; it never reads or writes tool input,
keys, uploaded files or results. A mission loading error leaves the tools usable.
The three tabs support arrow/Home/End navigation. See PRODUCT_ROADMAP.md for
the first mission's scope, validation and pending product decisions.

An empty result has a compact explanation instead of a large disabled textarea.
Completed results use selectable text with preserved whitespace, a bounded
keyboard-accessible scrolling region, contextual heading and Copy/Download/Reuse
actions. Ciphertext is monospaced; recovered prose uses the normal reading font.
Only rendered text is used for output; user data is never inserted as HTML.
The underlying unmodified string is used for clipboard/download operations,
preserving uploaded line endings. Copy errors do not remove the result.

Suggested cipher/key metadata stays adjacent to the recovered text. **Other key
guesses** opens manual mode and runs Find key, preserving the current result.
Unsupported/uncertain results explain the limitation and offer manual entry.
The existing learned models and supported cipher algorithms are unchanged.

## Visual system

The interface retains the navy/teal identity, a neutral canvas, restrained borders
and a clear single primary action per workflow. Spacing uses a 4/8px rhythm;
typography uses rem units and respects the user's root font size. Manual settings
and the workspace stack on smaller screens. Controls are at least 44px high,
with visible focus rings, labeled tabs and arrow/Home/End keyboard navigation.
Busy indicators reflect actual worker state and stop animating for reduced-motion
preferences. Background color transitions were removed after a contrast audit
found low-contrast intermediate disabled-to-enabled frames. Tab hover styles are
isolated from primary-button hover styles for the same reason.

## Verification — November 23, 2026

- All 199 Python tests passed before publication.
- The real Chromium/WASM browser suite covers all six ciphers, four key searches,
  automatic recovery, ORBIT regression, uploads, exact mixed CR/LF file downloads,
  independent sessions and operation without a network connection after loading.
- UI checks cover default hidden settings, keyboard tabs, preserved source/results
  on mode switches, other key guesses, the built-in example, actual clipboard
  copy and rejected clipboard access, and stale requests after mode/input changes.
- Screenshots and horizontal-overflow checks cover 320, 390, 768 and 1440px widths,
  including empty, recovered and manual layouts. Both workflows reflow without
  horizontal overflow at 320px with a 200% root text size.
- axe-core 4.14.1 reported no WCAG 2/2.1/2.2 A/AA violations in ten checked states:
  default desktop, recovered desktop, all six manual cipher settings, enlarged
  phone text and the phone error state with reduced motion. Automated results
  do not establish full accessibility compliance; real screen-reader and other
  browser verification remain pending.
- One controlled localhost Chromium measurement recorded initial LCP 72ms,
  CLS 0 and engine-ready time 1.922 seconds. This is not a production or field
  Core Web Vitals claim. INP and representative mobile-network performance still
  need measurement.

Internal review heuristics: usability, hierarchy, consistency, responsiveness and
feedback 9/10; accessibility and performance 8/10 pending manual screen-reader,
Safari/Firefox, and representative hosted performance checks. Prioritize those
checks over additional visual effects. These scores are review judgments, not
measured user satisfaction or a claim of visual perfection.

The redesign adds no production dependencies, external font requests, paid model
APIs or server-side processing of messages. Azure hosting remains unchanged.
