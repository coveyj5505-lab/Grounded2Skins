# Original Max comparison, 2026-10-18

All four supplied raw chunks match the size and SHA-256 recorded by the read-only Windows extraction. Total: 5,252,227 bytes. The absent fifth package does not invalidate the four supplied packages. The comparer now processes partial extractions while retaining original-container provenance and per-package integrity checks.

Stock body and backpack meshes contain exactly matching 188-bone native reference skeletons. The original USkeleton contains 195 bones. Commander101 contains 230; it is not the stock reference skeleton. Shared bone parent names match, but ordering, extra bones and several local rest transforms differ. See stock-max-comparison.json for per-bone local differences and material imports. Each extracted table passed unique names, parent ordering, normalized quaternion, pose count and name-to-index-map validation.

Accumulating parent-local transforms shows the large pelvis/hip differences largely compensate. All 52 bones with positive Buzz weights occur in stock Max. Their accumulated positions differ by less than 0.01 cm. Two weighted pinky bones have accumulated angular differences above one degree: LeftHandPinky3_JNT 6.924 degrees (146 influenced render vertices), RightHandPinky3_JNT 27.338 degrees (147 influenced render vertices). These are orientation comparisons, not predicted deformation errors or animation playback. Other local differences include camera, cloth, finger-end and auxiliary bones. Additional unweighted bones must not simply be removed without checking sockets and required-bone dependencies.

Recommendation: retain the current 230-bone Buzz authoring project and proven Commander-compatible cooked template as an unchanged baseline. Do not replace its bone table/index order with stock data. It already uses the game's original USkeleton and animation blueprint imports, and Commander101 animated in the user's game. That evidence does not prove every Buzz pose. Before a major rebind, compare controlled pinky poses against a separate stock-frame reference and investigate retarget settings. A stock-bound variant, if warranted, should be a separate project with name-based weight remapping and bind-matrix correction, not a rebuild of geometry, materials or the package encoder. No rig or original mod bytes were changed during this assessment.

The stock meshes import /Game/Art/Characters/Player_Male01/Mesh/SK_Male_Kid_01_PhysicsAsset. Both import tables resolve to this path and negative object-reference candidates occur in the pre-skeleton bytes; UObject property labels are not mapped. The formerly requested _Augusta/.../SK_Male_Teen_01_w_BackPack_PhysicsAsset is a Commander101 dependency absent from the stock index. Stock-Max-Physics-Only-Extractor.zip requests only the stock dependency. The corrected extraction has now been supplied and validated; see the physics follow-up below. No complete re-extraction is needed.

The original Apparel01 MI imports MM_Character and the four T_Max_Apparel_01_C/N/RMA/SSS textures used by atlas staging. This verifies dependency presence, not the base-color parameter/shader sampling binding or exclusive ownership. Final material isolation, modified mip read-back, final atlas packaging and Windows Buzz gameplay validation remain pending.

Reproduce (new output folders required):

```sh
python pipeline/compare_stock_max.py STOCK_FOLDER /workspace/mod-work/global-stage/reports/reference-skeletons.json NEW_COMPARISON
# Place NEW_COMPARISON at STOCK_FOLDER/comparison for the diagnostic below:
python pipeline/analyze_stock_max_weights.py STOCK_FOLDER /workspace/mod-work/global-stage/reports/reference-skeletons.json /workspace/mod-work/rig-stage/skinned-export-v9/Buzz-geometry-SKINNED.npz NEW_ANALYSIS.json
```

The diagnostic was independently rerun and its JSON matched the initial result exactly. No full UObject, retarget-settings, physics-shape or material shader deserialization is claimed. These reports do not establish Buzz runtime compatibility.

## Physics follow-up

The corrected read-only extraction succeeded: 1 package, no missing targets, 7,961 bytes. Its SHA-256 is e2ad544b2dda555de5387d293903ef2029493209e3ca6aaf666da698fee63005. The report records original source size/mtime unchanged. SHA-256 verifies uploaded transport against the report; original TOC BLAKE3 validation was not performed by the Windows helper.

Actual class-index export inventories:

| Setup | PhysicsAsset | SkeletalBodySetup | PhysicsConstraintTemplate |
| --- | ---: | ---: | ---: |
| Stock Max | 1 | 15 | 14 |
| Commander101 backpack physics | 1 | 18 | 17 |

Class IDs are the same global ScriptObjects IDs already resolved in the Commander provenance audit. Every export payload is bounds checked and hashed. A guarded identical 114-byte body-record layout provides structural FName candidates and a hash of the preceding numeric region. These candidate names suggest different bone coverage, but they are not claimed as mapped BoneName properties. Export counts and payload differences already establish that the two serialized physics setups differ. See stock-max-physics-comparison.json.

No mapping exists in this workflow for full PhysicsAsset/SkeletalBodySetup/ConstraintInstance property deserialization. Collision shapes, mass, responses and angular limits are not independently decoded here; this report does not claim physical equivalence or runtime behavior. The supplied package is sufficient to establish the non-stock provenance and inventory differences. No further original asset upload is requested for this assessment.

Safest next step: preserve the existing 230-bone rig and Commander-compatible staging baseline. Complete separate controlled finger-pose checks and the isolated atlas/material validation before the first Buzz ZIP. If stock physics is adopted, explicitly remap the cooked mesh's physics object import and validate that revision; simply dropping the custom physics package would leave a missing game dependency. Do not overwrite the stock USkeleton with Commander101's mesh-local skeleton. The known Windows test validates the existing reference mod's basic launch/animation, not Buzz or every stock animation/physics interaction. No major rig or package changes were made during this assessment.

Reproduce:

```sh
python pipeline/compare_stock_physics.py STOCK_PHYSICS_FOLDER /workspace/mod-work/retoc-raw/chunks/3f6f64a4f37953eb00000001 NEW_REPORT.json
```

The diagnostic was rerun to a separate output and compared byte for byte successfully.
