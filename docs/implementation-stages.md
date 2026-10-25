# Implementation Stages

Work proceeds one phase at a time. Complete and verify the current phase, report
its results, then stop at the boundary. Do not start the next phase automatically.
The authoritative individual task criteria remain in
`specs/001-hsv-color-segmentation/tasks.md`.

Current status: **Phases 1 through 7 complete and verified on 2026-10-24**. Phase 7 includes a
fixed photographed scene under two documented real lighting conditions, with source permission
and hashes recorded. Phase 8 has not started.

| Phase | Tasks | Deliverable | Exit check |
| --- | --- | --- | --- |
| 1. Project setup | T001–T004 | Plan, dependencies, package skeleton, install guide | Locked dependencies import; local package installs; discovery works |
| 2. Shared foundation | T005–T007 | Media/threshold/result models, typed errors, analytical fixtures | Shared contracts and independent reference values are ready |
| 3. Still-image MVP | T008–T021 | Tested HSV algorithm, image loading, GUI and six controls | Core tests pass; original/mask/result update together |
| 4. Video | T022–T027 | Sequential video input and playback | Open, play, pause, threshold edits, end and restart work |
| 5. Output | T028–T032 | PNG mask/result and video-frame export | Saved dimensions and decoded pixels match the source result |
| 6. Error recovery | T033–T036 | Validation and recoverable input/output errors | Each failure is followed by a successful valid operation |
| 7. Experiments | T037–T044 | Recording, at least 10 images and 20 runs, comparisons | Automatic replay succeeds; licensed real-lighting pair is documented |
| 8. Final verification | T045–T050 | Performance evidence, docs, demo and independent acceptance | Measured criteria and actual student acceptance are recorded |

Phase 1 does not deliver an executable desktop window or image processing code.
Phase 2 adds data validation and independent reference fixtures, with 60 passing
foundation checks. Phase 3 delivers the first working image application; Phase 4 adds
bounded sequential video playback; Phase 5 adds lossless still/video-frame PNG export;
Phase 6 adds structured recovery and the seven-case format inventory. Phase 7 adds atomic local
records, a GUI experiment panel, 20 retained runs, exact replay, and licensed photographs under
two documented real lighting conditions. The 195 automated checks pass.
Independent human acceptance in
Phase 8 must be performed by actual participants; unavailable evidence stays open.
