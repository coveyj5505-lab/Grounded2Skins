# Original Max comparison, 2026-10-18

All four supplied raw chunks match the size and SHA-256 recorded by the read-only Windows extraction. Total: 5,252,227 bytes. The absent fifth package does not invalidate the four supplied packages. The comparer now processes partial extractions while retaining original-container provenance and per-package integrity checks.

Stock body and backpack meshes contain exactly matching 188-bone native reference skeletons. The original USkeleton contains 195 bones. Commander101 contains 230; it is not the stock reference skeleton. Shared bone parent names match, but ordering, extra bones and several local rest transforms differ. See stock-max-comparison.json for per-bone local differences and material imports. Each extracted table passed unique names, parent ordering, normalized quaternion, pose count and name-to-index-map validation.

Accumulating parent-local transforms shows the large pelvis/hip differences largely compensate. All 52 bones with positive Buzz weights occur in stock Max. Their accumulated positions differ by less than 0.01 cm. Two weighted pinky bones have accumulated angular differences above one degree: LeftHandPinky3_JNT 6.924 degrees (146 influenced render vertices), RightHandPinky3_JNT 27.338 degrees (147 influenced render vertices). These are orientation comparisons, not predicted deformation errors or animation playback. Other local differences include camera, cloth, finger-end and auxiliary bones. Additional unweighted bones must not simply be removed without checking sockets and required-bone dependencies.

Recommendation: retain the current 230-bone Buzz authoring project and proven Commander-compatible cooked template as an unchanged baseline. Do not replace its bone table/index order with stock data. It already uses the game's original USkeleton and animation blueprint imports, and Commander101 animated in the user's game. That evidence does not prove every Buzz pose. Before a major rebind, compare controlled pinky poses against a separate stock-frame reference and investigate retarget settings. A stock-bound variant, if warranted, should be a separate project with name-based weight remapping and bind-matrix correction, not a rebuild of geometry, materials or the package encoder. No rig or original mod bytes were changed during this assessment.

The stock meshes import /Game/Art/Characters/Player_Male01/Mesh/SK_Male_Kid_01_PhysicsAsset. Both import tables resolve to this path and negative object-reference candidates occur in the pre-skeleton bytes; UObject property labels are not mapped. The formerly requested _Augusta/.../SK_Male_Teen_01_w_BackPack_PhysicsAsset is a Commander101 dependency absent from the stock index. Stock-Max-Physics-Only-Extractor.zip requests only the stock dependency. Actual stock physics shapes and constraints remain unavailable until it is supplied. No complete re-extraction is needed.

The original Apparel01 MI imports MM_Character and the four T_Max_Apparel_01_C/N/RMA/SSS textures used by atlas staging. This verifies dependency presence, not the base-color parameter/shader sampling binding or exclusive ownership. Final material isolation, modified mip read-back, final atlas packaging and Windows Buzz gameplay validation remain pending.

Reproduce (new output folders required):

```sh
python pipeline/compare_stock_max.py STOCK_FOLDER /workspace/mod-work/global-stage/reports/reference-skeletons.json NEW_COMPARISON
# Place NEW_COMPARISON at STOCK_FOLDER/comparison for the diagnostic below:
python pipeline/analyze_stock_max_weights.py STOCK_FOLDER /workspace/mod-work/global-stage/reports/reference-skeletons.json /workspace/mod-work/rig-stage/skinned-export-v9/Buzz-geometry-SKINNED.npz NEW_ANALYSIS.json
```

The diagnostic was independently rerun and its JSON matched the initial result exactly. No full UObject, retarget-settings, physics-shape or material shader deserialization is claimed. These reports do not establish Buzz runtime compatibility.
