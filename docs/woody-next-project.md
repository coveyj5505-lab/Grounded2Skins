# Woody → Pete preparation

User requested Woody preparation while testing Jessie/Hoops. Jessie has a verified downloadable first test but no reported Windows result yet. Buzz and Bo Peep remain preserved; Bo Peep's hand/cape correction targets are documented. No current gameplay files or original reference assets are changed for Woody preparation.

## Supplied source already inspected

User supplied `woody-toy-story-v2-kh3.zip` (27,658,224bytes, SHA256 `75be881beae616f9eb53e051e4523b4d6dca1f2d9cb8dc51225335b1dd014229`), containing `source/Woody.fbx` and twelve PNGs (six diffuse, six normal). No license/readme/exact listing URL is bundled; the earlier searched Woody candidate is not attribution for this archive. No further model download is required.

Blender imports a 290-bone source rig with no animation actions, nine weighted character mesh parts (32,379vertices /54,801triangles), and twelve unweighted `mmd_tools_rigid_*` helper meshes (408vertices /768triangles). The helpers are preserved and hidden from playable export. Two hat-material mesh parts share positions/counts but do not have identical full topology/UV/weight fingerprints, so both are preserved; do not blindly delete a duplicate.

`inspection/Woody-source-inspection.blend` preserves the import; `prepared-source/Woody-source-prepared.blend` restores named diffuse bindings for hat/boots/clothes/shirt/hair/skin and packs all twelve supplied maps persistently. Original geometry, weights and source rig transforms are not fitted or changed. Actual front/back previews were rendered; front confirms hat, sheriff shirt/vest, holster, jeans and boots. Material `New ` in the eye/mouth region remains unresolved and uses a neutral inspection placeholder. Investigate existing sheet UVs or a temporary eye solution after stock Pete arrives; do not claim materials finished.

Private root `/workspace/mod-work/woody-stage`; source file inventory/hashes, original metadata, prepared material report and previews are retained. Native Pete binding, cooked assets and a Woody gameplay ZIP do not exist yet. User then prioritized Jessie V2 deformation corrections, so preserve this source preparation while correcting Jessie.

## Stock Pete input

`Player_Male02` is the expected directory; actual gameplay mesh paths, character identity, mesh-local skeleton and LODs remain unverified. Shared stock skeleton metadata contains Pete-labelled material curve names, corroborating a character convention but not proving those mesh paths or bone count. Do not substitute Max's, Hoops's or SuperEvie's bone tables. No stock Male02 meshes are in the current selected uploads.

`Pete-Compatibility-Extractor.zip` uses the same retoc0.1.5/Python3.11+ workflow as the successful Willow and Hoops helpers. It discovers actual indexed SK meshes under Male02, reads their Zen imports and follows skeleton/physics dependencies without guessing filenames. User runs Start-Extraction.cmd, chooses original Augusta-WinGDK.utoc and uploads Desktop Grounded2-Pete-[timestamp].zip. It makes no game edits and does not copy the full UCAS. Budget48packages/128MiB decoded; partial data/report remains useful.

Control tests actually run against Commander101: explicit Male01 discovery/extraction matches existing known chunks, reports missing external original skeletons, and leaves input size/mtime unchanged; default Male02 discovery returns zero, avoiding false Pete identification. These are tool controls, not Pete compatibility evidence. Exact control counts/hashes are in the private stage reports. Windows dialogs reuse the user's working launcher and cannot be executed here.

When the stock ZIP arrives, `inspect_character_extraction.py` safely normalizes Windows ZIP backslashes, checks every chunk SHA/size and parses native bone tables. Read every target LOD with CUE4Parse and adapt template hash/layout guards to the actual stock profiles. Preserve native bone transforms, animation and physics references; do not use an arbitrary UE5.6 cook.

## Reuse and isolation

Reuse Jessie/Bo Peep native buffer encoding, per-section palettes, four-LOD writing where actually supported, measured Zen relocation, private material cloning, flat-BC5 fix, atlas V conversion, IoStore packaging and independent CUE/texture read-back. Planned separate mod basename `zWoodyTest_P`, private namespace `/Game/_Woody00` (eight characters, suitable for existing equal-length template cloning), private material token `_Wdy_`. Verify all paths and chunk IDs remain disjoint from Buzz/Bo Peep/Jessie before release. Preserve all existing ZIPs.

Private staging root `/workspace/mod-work/woody-stage` stores actual public model metadata and extractor control logs. No source model, fitted Woody, cooked Woody asset or installable Woody mod exists yet. The remaining external input is targeted stock Pete extraction; no other upload, new toolchain or reverse-engineering restart is required.
