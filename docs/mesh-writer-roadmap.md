# Current evidence and the path to Buzz

The user reports that the delivered `zMeshTest_P` loads correctly in Grounded 2
WinGDK build **0.316.9020.0**, renders Commander101, and animates successfully.
A small helmet bump was observed, but its difference from the original has not
been conclusively compared. [The test record](windows-test-0.316.9020.0.json)
distinguishes those findings. User PC file hashes and individual equipment or
animation coverage were not separately reported.

The existing ZIP, its SHA-256, original reference trio, and proven packaging
helpers remain unchanged. Historical machine reports saying `NOT RUN` describe
their original creation time; the separate Windows record supersedes that
status for this specific delivered test only.

## What the new code can actually do

[The native-buffer encoder](../pipeline/native_buffers.py) now produces new,
variable-count native position, index, tangent/normal/UV, color, and skin-weight
records. It is no longer limited to overwriting equal-size position data.

It accepts a different indexed mesh with split UV/hard-normal/tangent seams,
groups triangles by material, splits sections at a conservative bone-palette
cap, duplicates vertices shared between sections, maps original skeleton IDs to
local palette indices, and quantizes weights to UNORM8 with exact totals of255.
It compacts positive influences before padding so a shader reading the first
`MaxBoneInfluences` entries does not lose weights stored after zero slots.

The 230-bone reference is identified by its names, parents and native rest
transforms, hashed to a stable signature. Imported meshes with a different
signature or unknown bone IDs are rejected. The encoder does not change the
skeleton or retarget animations.

The measured format supported here is one UV channel in float16, packed 8-bit
tangent frames, 32-bit triangle indices, native BGRA colors, and fixed eight-slot
UNORM8 skin weights. The palette cap70 is the largest palette seen in the
working reference, not a claim that the engine cannot support more. Cloth,
morphs, extra UV channels, material graphs, and arbitrary cooked package
serialization have not been implemented.

[CUE4Parse read-back results](native-buffer-validation.json) cover:

| Case | Result |
| --- | --- |
| Full recovered Commander101 mesh | 258,064 vertices, 364,319 triangles, nine section plans; read-back passes |
| Different topology/material assignment | Four input vertices become six section-local render vertices; two triangles; passes |
| Bone-palette split | Two sections, correct local-to-global bone mapping; passes |
| Weights with holes between influences | Positive influences compacted without changing bone-to-weight associations; passes |
| Ten invalid-input cases | Rejected: changed skeleton, invalid coordinates/indices, unweighted vertex, missing skin, unknown/duplicate bones, bad material, excess influences, and float16 UV overflow |

Indices, float32 positions, colors, decoded local IDs and raw weights compare
exactly. UVs match float16 quantization; normal/tangent component error is below
0.004. All decoded weights sum to255 and map back to the intended original
bones. The full-reference *new-buffer* test explicitly orthogonalizes tangent
frames and repairs three near-zero tangents; it is not an unchanged-asset
byte-round-trip claim. No original asset was altered by those tests.

## Buzz archive: inspected, not rigged

The user confirmed the supplied archive came directly from the linked Sketchfab
model. Its nested source is OBJ/MTL: **13,450 position records, 20,482 triangles,
one UV layer, eight material slots, and eight referenced diffuse textures**.
The actual OBJ count differs from the site's earlier reported vertex count;
the measured file counts are used for processing. No `vn` normals, skeleton,
animation clips, or skin weights are stored in the OBJ. The bundled converter
executable was not run; Blender imports the OBJ directly.

The model has been imported, textured, oriented to face the same direction as
the reference, and initially scaled/grounded to a height of1.9324701m. This is
**initial bounds alignment**, not anatomical alignment of hips, shoulders,
hands or fingers. Buzz is in a T-pose with extended wings; the reference has a
different rest pose and proportions. Those differences still need fitting.

The saved scene contains the untouched 230-bone reference armature and packed
textures. A fresh Blender process reopened it and checked vertex/face counts,
all eight packed textures, and a hash of all reference bone rest matrices.

The geometry exporter generated normals/tangents from the OBJ and UVs, split
render seams, and recorded removal of two degenerate triangles (source IDs1415
and2926). The prepared stream has **61,413 render vertices and 20,480 triangles**.
Its larger render-vertex count reflects split corner attributes and source flat
shading; this has not been optimized. Source-vertex IDs are retained for later
weight transfer. **No weights were fabricated.** The skinned encoder rejects
this stream with `No skin weights: weight transfer and binding are required`.

[Intake and license record](buzz-intake.json) includes a real unresolved
discrepancy: Sketchfab lists CC BY4.0, while the nested `License.txt` says
"Personal Use only (Students)" and mentions a commercial membership. Direct
Sketchfab provenance is confirmed, but the conflicting redistribution terms
are not resolved. Model/texture files and the Blender scene have not been
uploaded to this public repository. Local inspection and preparation continue.

## Remaining implementation, in order

1. **Fit and bind Buzz.** Align anatomical landmarks and adapt its T-pose to the
   existing rest pose. Transfer/review weights while retaining all230 bones.
   Treat wings/backpack and rigid suit pieces deliberately; nearest-surface
   weights alone can attach wings to arms or nearby unrelated parts. Review
   shoulders, elbows, hips, face, and fingers with controlled poses.
2. **Serialize the complete resized native LOD.** Emit actual render-section
   structures from the section plan, including ranges, flags, palettes and
   influence limits; update streamed-buffer size and active-bone ancestry.
   The original required-bone array already contains230 entries; active bones
   contain77. These arrays must be validated against the new weighted bones.
3. **Relocate the Zen package correctly.** Integrate the new LOD into both body
   and backpack packages, update the relevant export size and all affected
   offsets, inspect the zero-length bulk-data-map entry, and preserve the
   remaining native tail. Do not append new bytes while leaving stale sizes.
4. **Update bounds and materials/textures.** The original imported bounds are
   seven float64 values at body offset8502, ending at the material array8558.
   CUE4Parse has independently read this field and the complete LOD. Buzz's
   extended wings exceed the reference's width, so preserving old bounds is
   insufficient. Eight source material IDs do not themselves create eight
   compatible Unreal material assets; shader/texture integration is still needed.
5. **Repackage and validate, then game-test separately.** Use the proven retoc
   container identity, hashes, offsets, path and extraction checks. Decode the
   entire rewritten asset independently, bind/reopen it in Blender, compare
   buffers and skeleton, and only then prepare another Windows test mod. The
   successful fixed-count test does not establish arbitrary replacement support.

[Reader-validated layout](reference-package-layout.json) records the native
regions and bone arrays. The measured body has buffer records at34361..15761130,
a full LOD at32898..15761184, and100 bytes after that LOD. Retoc's original Zen
header also shows two exports and a zero-size bulk entry; their resize/relocation
semantics have not yet been implemented or validated. Full UObject mapping is
not required for the buffer work already completed and is not being repeated
as a blanket blocker.

There is **no Buzz cooked asset or installable Buzz mod yet**. The new native
buffer tests are local parser checks, not a Windows runtime result.
