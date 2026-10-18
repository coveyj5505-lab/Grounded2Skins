# Experimental variable-size mesh preparation


**Current gate:** Commander101 is a third-party Max replacement. Its recovered 230-bone mesh reference pose has not yet been compared to stock Max. The atlas gameplay ZIP is paused for the [compatibility assessment](../docs/commander-stock-max-assessment.md); current rig and packaging work remain preserved.
The working `zMeshTest_P` release is unchanged. Buzz is now fitted and skinned,
with the approved stowed visibility state and six original wing panels preserved.
Both complete resized native LODs and Zen packages have passed independent
CUE4Parse/retoc readback and container round-trip checks. Unreal materials/textures
are still the original Commander references; this is not a finished textured or
in-game-tested Buzz release.

See [rigging and wing preservation](../docs/buzz-rigging.md) and
[resized package reproduction](../docs/resized-package-pipeline.md).
The standalone-buffer and unskinned-intake examples below remain useful isolated
stages; their historical limited scope does not describe the completed full writer.

## Tools and retained inputs

The tested environment uses Python3.12/NumPy, Blender4.3.2, .NET SDK10.0.402, and
CUE4Parse1.2.2 commit `2b8901c3ee9818558ad33e2496a58d50b82e99db` under
`/workspace/tools/CUE4Parse`. Third-party source and dependencies remain unchanged.
The existing Microsoft.Bcl.Memory9.0.0 NU1903 warning remains visible in builds.

The original reference input and decoded data are retained under
`/workspace/mod-work`; source model assets are not included in this repository.
The existing retoc pipeline stays under `mod-work/mesh-write-stage/scripts`.

```bash
export DOTNET_ROOT=/workspace/toolchains/dotnet
export DOTNET_CLI_HOME=/workspace/toolchains/dotnet-home
export NUGET_PACKAGES=/workspace/toolchains/nuget
cd /workspace/Grounded2Skins
/workspace/toolchains/dotnet/dotnet build \
  pipeline/native-buffer-probe/NativeBufferProbe.csproj \
  -c Release -p:CUE4PARSE_SKIP_NATIVE=true -m:2
```

For another location, set `-p:Cue4ParseRoot=/absolute/path/to/CUE4Parse`.

## Read the measured reference components

```bash
/workspace/toolchains/dotnet/dotnet \
  pipeline/native-buffer-probe/bin/Release/net10.0/NativeBufferProbe.dll \
  extract-reference \
  /workspace/mod-work/retoc-raw/chunks/cd809abc483f179000000001 \
  /workspace/mod-work/variable-mesh-stage/new-reference-extraction
```

This mode requires the exact original body SHA-256, extracts the five consecutive
buffer records using CUE4Parse readers, decodes their values, and independently
reads the bounds and full native LOD. All outputs must be new directories.
The test runner uses the already extracted `variable-mesh-stage/reference-native`.

## Run actual writer/read-back tests

```bash
python pipeline/test_native_buffers.py \
  /workspace/mod-work/variable-mesh-stage/new-encoder-test
```

This requires the retained original buffers under `mesh-stage/body`, native
tangents under `variable-mesh-stage/reference-native`, and the original reference
skeleton JSON. Four cases are encoded, decoded by the unchanged CUE4Parse native
constructors, and compared. Ten invalid-input cases must be rejected. The report
is `validation.json`; per-case logs and decoded data are retained.

## Interchange NPZ

`native_buffers.py` accepts a NumPy NPZ loaded with `allow_pickle=False`:

| Field | Shape / meaning |
| --- | --- |
| `positions` | N×3, Unreal-local centimeters |
| `normals`, `tangents` | N×3, perpendicular unit vectors, already split at seams |
| `signs` | N, tangent-frame handedness, +/-1 |
| `uv0` | N×2, finite values representable as float16 |
| `colors` | N×4, RGBA uint8; encoder writes native BGRA |
| `indices` | T×3, integer triangle indices, Unreal clockwise convention |
| `materials` | T, integer material slot IDs |
| `material_count` | Scalar number of source material slots; not material assets |
| `joints`, `weights` | N×K, K=1..8; global bone IDs0..229 and normalized nonnegative weights |
| `skeleton_signature` | Scalar string: hash of all230 reference bone names/parents/native rest transforms |

The compiler partitions sections and duplicates render vertices across their
boundaries. It does not silently prune influences over eight, replace bones,
drop invalid triangles, or accept unweighted source data. UNORM8 quantization
may zero very small influences; that count and maximum quantization error are
reported explicitly. The reference profile uses one float16 UV channel and
8-bit packed tangent frames; extra channels/precision modes remain unsupported.

```bash
python pipeline/native_buffers.py source-mesh.npz \
  /workspace/mod-work/global-stage/reports/reference-skeletons.json \
  /workspace/mod-work/variable-mesh-stage/new-native-records
```

The five `.bin` records and JSON section plan are **not installable mod files**.
The encoder does not create a `.uasset`, `.utoc`, or `.ucas`.

## Local Buzz preparation

The supplied OBJ, textures, and scene remain in `/workspace/mod-work/buzz-stage`.
The imported, initially aligned scene is
`final-inspection/Buzz-source-and-reference-skeleton.blend`. All eight referenced
textures are packed. Reference rest matrices remain unchanged.

```bash
blender --background \
  /workspace/mod-work/global-stage/exports/Commander101-reference-skeleton.blend \
  --python-exit-code 1 --python pipeline/inspect_buzz_blender.py -- \
  /workspace/mod-work/buzz-stage/obj-source/G7CVEC4O394HM1IJOEOC66LNO.obj \
  /workspace/mod-work/buzz-stage/new-inspection
blender --background \
  /workspace/mod-work/buzz-stage/new-inspection/Buzz-source-and-reference-skeleton.blend \
  --python-exit-code 1 --python pipeline/export_buzz_geometry.py -- \
  /workspace/mod-work/global-stage/reports/reference-skeletons.json \
  /workspace/mod-work/buzz-stage/new-inspection/blender-inspection.json \
  /workspace/mod-work/buzz-stage/new-geometry
```

The second command reopens the scene and checks mesh counts, packed images and
the reference rest-matrix hash. It exports the real geometry with UV/normal/
tangent seam splitting, reports any degenerate-face removal, and retains source
vertex IDs for later skin transfer. Its joint/weight arrays have zero influence
columns on purpose. Geometry checks pass; skinned checks must reject that file
until actual weights are created. No placeholder skin or substitute Buzz model
is generated.

See [the current roadmap](../docs/mesh-writer-roadmap.md) for completed full-package work and remaining Unreal material/texture integration and Windows tests.
