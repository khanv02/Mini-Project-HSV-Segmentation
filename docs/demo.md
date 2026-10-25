# Academic demonstration walkthrough

This is a 10-minute presenter script. Run it on the Windows machine recorded in
`experiments/environment.json`; keep the repository offline throughout.

## Before the timer

- Confirm the light analysis workspace opens with media actions first, a channel-based HSV
  inspector on the left and three synchronized previews in the flexible work area.
- Confirm playback controls are hidden before video is opened. Demonstrate `Ctrl+O` and
  `Ctrl+Shift+O`, cancelling each chooser without changing application state.

Run `uv sync --locked --extra test` while installation resources are available. Confirm the
seven files in `tests/fixtures/acceptance_media/`, the ten retained inputs and twenty run
directories from `experiments/manifest.json`, and writable temporary/output folders. Launch:

```powershell
uv run hsv
```

## Timed walkthrough

| Time | Action and evidence |
|---|---|
| 0:00-1:30 | Open `tests/fixtures/acceptance_media/rgb.png`. Point out Original, Binary Mask and Segmented Result. Show the HSV Histogram panel for the current image: 360 H bins, 101 S/V bins, the fixed S>=5% hue note and excluded count. Explain that the charts assist manual selection and do not choose thresholds automatically. |
| 1:30-2:30 | Change each of the six controls. Show overlays moving without the source counts changing, an equal-bound labeled line, wrapped red H 350..10 at both hue-axis ends, an empty selection, and correction after invalid S or V ordering. Explain inclusive bounds and that invalid visible values preserve the prior valid result/overlay while disabling save actions. |
| 2:30-3:30 | Save mask and result PNGs. Reopen them or inspect properties to show source dimensions, binary 0/255 mask semantics, unchanged selected RGB, and black excluded pixels. Cancel one save and decline one overwrite to demonstrate safe no-op behavior. |
| 3:30-5:00 | Open `mjpg.avi`, verify frame 0 is paused and the histogram now represents that frame, then play, pause, edit thresholds on the retained frame, continue to end and restart. Confirm counts follow the current frame and save one displayed frame result. Repeat the open smoke check for `mp4v.mp4`; identify FFMPEG and the recorded MJPG/FMP4 codec evidence in `docs/acceptance.md`. |
| 5:00-6:00 | With a valid result retained, attempt one missing/corrupt input and one invalid parameter. Explain the five recovery fields: operation, affected item, cause, preserved state and corrective action. Return to a valid edit without restarting. Refer to the simulated write/resource/decode cases in `docs/verification.md`. |
| 6:00-8:30 | Open `experiments/report.md`. Walk through all ten retained entries and both threshold settings per image. For the eight SimpleCube++ photographs discuss missed targets/unwanted regions across natural, shadow, artificial, night and mixed descriptions. For `mit_main_experiment120_dir00.jpg` and `dir24.jpg`, emphasize that they are the same photographed scene under two documented real directional lights and compare the observed mask changes. Do not claim ground-truth accuracy. |
| 8:30-9:15 | Show a UUID run's `record.json`, `mask.png`, and `result.png`. Explain source/environment/artifact hashes and replay three runs using the command in `experiments/README.md`. |
| 9:15-10:00 | Show `docs/algorithm.md` and `experiments/performance.md`: float64 RGB-to-HSV equations, exact histogram bin/cutoff rules, inclusive/wrapped selection, limitations, and the histogram-visible 99/100 Full-HD result against the 95/100 criterion. State that all runtime workflows are local and require no Image Restoration project or network service. |

## Artifact cross-check

- Image/video formats and codecs: `docs/acceptance.md` and its seven hashed fixtures.
- Algorithm and limitations: `docs/algorithm.md`.
- Ten inputs, twenty configurations and lighting pair: `experiments/manifest.json` and
  `experiments/report.md`.
- Exact replay: `experiments/reproduction.md` and the retained UUID run directories.
- Responsiveness: `experiments/performance.md` and `performance_results.json`.
- Overall acceptance status: `docs/verification.md`.

The independent five-minute student workflow and second-student three-run reproduction must be
performed by real participants. Leave those fields pending until their names, dates, elapsed
times and outcomes are genuinely recorded.

