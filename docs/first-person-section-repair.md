TOY STORY: ALL FOUR FIRST-PERSON SECTION TEST

OFFLINE VALIDATED. WINDOWS FIRST-PERSON FIX NOT YET CONFIRMED.
Target Grounded 2 PC Game Pass / WinGDK build 0.316.9020.0.
No UE4SS script, camera setting change or game-file overwrite required.

INSTALL ALL FOUR
1. CLOSE Grounded 2.
2. Move the OLD Toy Story mod trios completely OUTSIDE Augusta/Content/Paks, for example into a Desktop backup folder. Do NOT leave them in a subfolder of Paks. Keep them as fallbacks.
   Buzz: zBuzzAtlasV2_P.pak/.utoc/.ucas
   Woody: zWoodyTest_P.pak/.utoc/.ucas
   Bo Peep: zBoPeepV2_P.pak/.utoc/.ucas (or zBoPeepTest_P if V1 is still installed)
   Jessie: zJessieV2_P.pak/.utoc/.ucas
   Move any older versions of these character replacements out too; do not stack two versions for one character.
3. Copy ALL TWELVE files from mod directly into Augusta/Content/Paks:
   zBuzzFP_P.pak/.utoc/.ucas      -> Max
   zWoodyFP_P.pak/.utoc/.ucas     -> Pete
   zBoPeepFP_P.pak/.utoc/.ucas    -> Willow
   zJessieFP_P.pak/.utoc/.ucas    -> Hoops
4. Start the game and test each character as below.

TEST / REPORT
For EACH character:
- In third person, confirm the full head/face/hat/hair is visible.
- Use your normal camera toggle to enter first person. Check that the view is clear and hands are visible.
- Walk, look around, punch and equip a weapon; check aiming and hands/equipment.
- Toggle back to third person and confirm the full head returns. Repeat a few times.
- If a co-op partner is available, check that they see the normal full character while you use first person. Multiplayer visibility is not yet tested.
Please report clear/obstructed view, visible/missing hands and third-person head visibility separately for all four. If it fails, include which character and which older mod files remain in Paks.

REMOVE / REVERT
Close the game, remove the twelve FP files and restore the saved original trios. The existing fallback ZIPs are untouched.

WHY THIS TEST
The native stock meshes separate head materials from body/hands. Our skins put everything in one material slot. For Max/Pete/Willow that was a body slot, leaving head geometry in the camera; for Hoops it was the head slot, consistent with a clear view but missing hands.
These updates split head triangles from body/hands using the stock head slot and the same private atlas material on both. Buzz also restores the used stock Max material-slot names. Jessie keeps her head in head slot0 and moves the body/hands to ArmsLegs slot5.
This is a strong explanation of the four observed symptoms, but the native runtime hide calls have NOT been observed. The Windows test must establish that this repair actually uses the game's first-person visibility mechanism. If it does not, the next step is a targeted read-only UE4SS camera/mesh visibility probe using the already-confirmed v3.0.1 Beta installation.

PRESERVED
Every original triangle, position, normal/tangent/sign, UV, color and skin-weight value is independently checked against the existing build. Full heads are retained, not deleted. Bone tables/rest transforms, original animation/physics dependencies, textures and shaders are preserved. No camera offsets, input, movement, damage, collision or replication code changes. Each update changes only the two main/body-backpack mesh chunks plus its new container identity.
Bo Peep includes V2's accepted finger appearance. Her glove fit and seated clothing clipping remain separate known visual issues; this package does not reshape them. Existing simplified hand articulation/materials and other model limitations remain. Buzz's six original wing panels and Bo Peep's crook remain preserved in the private source projects and are not added to gameplay.

CROOK / WINGS
Accessory development remains paused until these first-person behaviors are validated.

REPRODUCIBLE TECHNICAL WORK
- audit_first_person_assets.py /workspace/mod-work NEW_REPORT independently compares stock/replacement native head/hand weights, section slots and first-person named bones. This proves the section mismatch, not which runtime function hides them. Stock Max/Pete/Willow canonical head slots are5/3/3; Hoops head0 and ArmsLegs5. Original FPSpine bones generally have no weighted vertices; attaching geometry to them without evidence is not warranted.
- NativeLodProbe now traces FSkeletalMaterial record extents with the original CUE4Parse reader, allowing package-index and FName changes at measured offsets.
- build_first_person_sections.py CHARACTER NEW_STAGE uses the accepted source geometry/atlas and baseline UVs, assigns whole head-influenced triangles to the canonical head slot (any vertex >25% head-subtree weight), and encodes material/palette sections with the existing native buffer serializer. All other source arrays are retained. It writes measured LOD extents, export sizes and empty-Nanite bulk offsets. Buzz FName additions relocate ALL Zen summary offsets, including UE5.6 cell import/export maps at summary words13/14. They are necessary for correct export-map bounds; the full retoc legacy conversion verifies them.
- repackage_iostore.py writes separate container identities and verifies/unpacks byte-exact staging. validate_first_person_sections.py performs fresh native reads and compares attributes PER ORIGINAL TRIANGLE CORNER despite material sorting/section-seam duplication. It compares actual packed tangent/normal/handedness bytes in the serialized streams too. Every head/body material resolves to the same accepted private atlas dependency. Native skeleton tables are exact, no triangles removed, every LOD read. All other shader/material/texture/hair/menu chunks are hash-exact baseline. Full legacy conversion must yield each expected UEXP payload byte-exact; a retoc exit0 alone is insufficient because it can report skipped assets.
- Final private stages: /workspace/mod-work/first-person-stage/{buzz-v4,woody-v1,bopeep-v1,jessie-v1}. Earlier Buzz candidate stages are REJECTED diagnostics, not distributed. The first caught a source UV/atlas ordering mismatch; the subsequent header diagnostic caught missing cell-map relocation. Final Buzz uses atlas/Buzz-atlas-SKINNED.npz and complete header relocation; all checks pass.
- Actual offline coverage:8 changed mesh packages and26 LODs across four mods. Only8 body chunks change; all other character/package chunks retain baseline hashes apart from four unique header identities. The previous release ZIPs remain byte-exact.

RUNTIME BOUNDARY
We have not observed native ShowMaterialSection/HiddenMaterials calls in the Windows game. The matched layout and four symptoms support this candidate; they do not prove it. Full head retention and lack of camera/network changes are offline facts. Owner-specific first-person hiding/restoration, hands, equipment/aiming and multiplayer visibility still require Windows validation. No Lua visibility patch or new animation selector is included, and there is no need to reprobe basic UE4SS loading.
