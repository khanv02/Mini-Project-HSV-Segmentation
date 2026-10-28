# Implementation Stages

Work proceeds one phase at a time. Complete and verify the current phase, report
its results, then stop at the boundary. Do not start the next phase automatically.
The authoritative individual task criteria remain in
`specs/001-hsv-color-segmentation/tasks.md`.

Current status: **Phases 1 through 7 and Phase 9 are complete; the automated/documentation
portion of Phase 8 is complete**. Phase 7 includes a fixed photographed scene under two
documented real lighting conditions, with source permission and hashes recorded. The final
human acceptance tasks T049-T050 remain open.

| Phase | Tasks | Deliverable | Exit check |
| --- | --- | --- | --- |
| 1. Project setup | T001–T004 | Plan, dependencies, package skeleton, install guide | Locked dependencies import; local package installs; discovery works |
| 2. Shared foundation | T005–T007 | Media/threshold/result models, typed errors, analytical fixtures | Shared contracts and independent reference values are ready |
| 3. Still-image MVP | T008–T021 | Tested HSV algorithm, image loading, GUI and six controls | Core tests pass; original/mask/result update together |
| 4. Video | T022–T027 | Sequential video input and playback | Open, play, pause, threshold edits, end and restart work |
| 5. Output | T028–T032 | PNG mask/result and video-frame export | Saved dimensions and decoded pixels match the source result |
| 6. Error recovery | T033–T036 | Validation and recoverable input/output errors | Each failure is followed by a successful valid operation |
| 7. Experiments | T037–T044 | Recording, at least 10 images and 20 runs, comparisons | Automatic replay succeeds; licensed real-lighting pair is documented |
| 8. Verification baseline and final gate | T045–T050 | Performance and documentation baseline, then independent acceptance after Phase 9 | T045–T048 complete; T049–T050 require actual student evidence |
| 9. HSV histogram aid | T051–T056 | Source/frame H/S/V counts, continuous threshold overlays and cache | Analytical/GUI tests pass and panel-visible Full-HD benchmark meets SC-003 |
| 10. Clean analysis workspace | T057–T064 | Semantic theme and responsive scientific layout | Existing workflows and 960x640 preview geometry pass |
| 11. Object separation and evaluation | feature-002 T001–T030 | Components/contours, optional Watershed, IoU/Dice and schema-2 evidence | Feature tests, full regression, replay and documented three-mode benchmark pass |

Phase 1 does not deliver an executable desktop window or image processing code.
Phase 2 adds data validation and independent reference fixtures, with 60 passing
foundation checks. Phase 3 delivers the first working image application; Phase 4 adds
bounded sequential video playback; Phase 5 adds lossless still/video-frame PNG export;
Phase 6 adds structured recovery and the seven-case format inventory. Phase 7 adds atomic local
records, a GUI experiment panel, 20 retained runs, exact replay, and licensed photographs under
two documented real lighting conditions. Phase 9 adds a compact optional histogram panel using
the existing NumPy/Tk stack; source/frame counts are cached while overlays follow exact numeric
thresholds. The 210 automated checks pass and the panel-visible benchmark meets SC-003 at
99/100 updates within one second. Independent human acceptance in Phase 8 must be performed by
actual participants; unavailable evidence stays open.

Phase 11 preserves HSV thresholding as the core algorithm. New NumPy/OpenCV processing modules
remain independent of Tk and filesystem adapters; the controller only coordinates immutable
settings/results. Advanced settings are disabled by default, so legacy image/video masks,
exports and schema-1 records remain unchanged. The implementation order is components and area
filtering, Watershed, evaluation, GUI, experiment publication, then integrated verification.
