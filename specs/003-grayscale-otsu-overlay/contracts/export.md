# Contract: Overlay Export

## Operation

`export_overlay(snapshot: OverlaySnapshot, path, overwrite=False) -> ExportReceipt`

## Preconditions

- `snapshot` is a complete immutable Overlay snapshot with validated source-sized RGB pixels.
- Destination resolves to a local `.png` path.
- Existing destination requires explicit overwrite confirmation.

## Publication semantics

- Write lossless PNG in RGB mode at exact source width and height.
- Use the current temporary-file plus atomic replace pattern.
- Never read Tk widget pixels or mutable controller fields inside the writer.
- Do not alter Save Mask or Save Result output, naming or receipt semantics.
- Return receipt kind `overlay`, final path, variant, source path, session and optional frame.

## Failure semantics

- Cancellation performs no call and creates no artifact.
- Invalid snapshot/path, missing parent, permission error and encode/write error are recoverable
  `WriteError` outcomes with operation `save overlay PNG` or `export overlay`.
- A failed write removes its temporary file when possible and does not replace an existing valid
  destination.
- UI changes during I/O cannot change the captured pixels. Completion messaging uses the receipt,
  not the controller's then-current source.

## Verification

Decode the written PNG and require:

- mode RGB and dimensions equal to the source;
- decoded array exactly equal to `OverlaySnapshot.rgb` at every pixel;
- decoded pixel hash equal to the evidence hash when retained in an experiment.
