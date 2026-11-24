# Guided Caesar practice

Built after the notification/admin release checkpoint `333604b`. The lesson
ships through the main-branch static-site deployment workflow. Open Learn →
Caesar cipher basics, or preview the same build at `http://localhost:8502`.

The saved student-learning plan prioritizes explaining transformations and
guided practice. This increment adds one three-step unit inside the existing
Learn chooser rather than another top-level tab:

1. Predict Y shifted forward three places, with a wraparound trace after success.
2. Recover CAT from FDW by reversing a three-place shift.
3. Use the known word MEET to find shift 7 and recover MEET ME AT NOON.

All checks call the existing Python cipher engine through `requestCipher`;
there is no separate JavaScript encryption implementation. Each step offers
two small hints and specific wrong-answer feedback. Correct steps unlock the
next task. Editing a prerequisite invalidates dependent completion. The unit
explains that 26 possible shifts make Caesar unsuitable for protecting secrets.

Only canonical successful practice answers and the current step persist under
`ciphercraft.learn.caesar.v1`. Other drafts, lesson records, campaign saves and
messages are unchanged. The completion button opens existing cipher tools
without replacing their input or result. Reset clears only this lesson and
invalidates in-flight checks. Practice works offline after its module and the
shared engine have loaded; first load still needs the bundled assets.

Validation: the browser suite uses the real shared engine and checks hints,
wrong/right feedback, keyboard steps, offline use, reload, reset races, work
isolation, and 320/390/768/1440px layouts. Existing password and integrity lesson
suites pass. Automated WCAG A/AA scans report no findings on all three steps;
390px with 200% text has no horizontal overflow. Screenshots were inspected.
This is self-paced local practice, not teacher-controlled assessment or proof
of measured learning outcomes. Physical Android installation is still pending.

Internal review heuristics: hierarchy 9, consistency 9, responsiveness 9,
feedback 9, usability 8.5, accessibility 8.5, performance 8. Prioritize a real
student/teacher playtest, screen-reader checks and field performance measurement.
The next planned product slice is teacher-created assignments with explicit
practice/assessment controls; a client-side hint toggle cannot secure an exam.
