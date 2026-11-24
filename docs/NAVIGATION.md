# Responsive section navigation

The five sections keep a stable order: Crack a message, Encrypt / decrypt,
Play, Hash Lab and Learn. The user requested smoother transitions and a simpler
desktop layout. Desktop now shows a normal, fully visible row; carousel arrows,
perspective, card reordering and drag-to-switch behavior have been removed.
Phones retain the Amazon-style native scrolling chip row requested by the user.

## Motion and input

A shared selection indicator moves and resizes over 260 ms using an ease-out
curve. When another section is selected mid-transition, the next animation starts
from the indicator's currently visible bounds, rather than jumping to the prior
animation's endpoint. Web Animations avoids inline styles under the site's CSP.
Label colors remain readable throughout the transition. Content enters with a
small 180 ms translation; opacity and text contrast do not fade.

Reduced motion snaps the indicator into position and cancels content movement.
All tabs remain native buttons in a horizontal tablist, with a single roving tab
stop and ArrowLeft/Right/Home/End support. Desktop labels stay in fixed positions.
On phones, horizontal scrolling has native momentum and proximity snapping.
Swiping scrolls without selecting; a stationary tap activates exactly once,
including after a fling where a browser may suppress the usual click event.
Long presses and vertical gestures do not activate a section.

ResizeObserver keeps the indicator aligned after resizing. Existing lab inputs,
cipher results, campaign saves and lesson answers remain separate from the
navigation. Feature styles no longer override global navigation layout. A navy
and teal SVG favicon uses the app's C-and-dot identity.

## Verification

The navigation browser suite measures a real halfway animation frame, interrupted
animation continuity, alignment at the endpoint, stable desktop rows at 768/1440
pixels, keyboard wrap, reduced motion and native emulated mobile swipe/tap at
320/390 pixels. All 211 Python tests, critical lint and the four cipher/AI,
campaign, Hash Lab and Learn browser suites pass after the navigation change.
Representative phone, tablet and desktop renders were reviewed. Axe reports no
WCAG A/AA findings in the tested desktop view; this is not a complete audit.
The favicon link and SVG response were verified in the local preview.

The prior Android beta was tested with the earlier navigation. This smooth
navigation revision's native APK refresh and unlocked-phone visual/touch check
remain pending. Browser touch emulation does not establish physical phone feel.
Human usability, screen-reader, landscape and lower-end performance tests remain
recommended. Internal review (judgment): usability 8, hierarchy 9, accessibility 8,
consistency 9, responsiveness 8, feedback 9, performance 8. Prioritize those
checks over further decoration. The implementation remains uncommitted locally.
