# Native crook spear V1 — host test candidate

`BoPeep-Crook-Native-Spear-V1-UE57-Test.zip` is the first native-item integration test. Windows execution is **not confirmed**. The accepted skins, Teleport V2, FreeBuild, InvisibleArmor and prior crook releases are unchanged.

This version uses native equipment and combat rather than playing a cosmetic montage beside unarmed punches. The current native Spear BaseItemData is deep-copied through the installed UE4SS UDataTable API into our own cooked BaseItemData table. Only private attack references and throwing flags change. Ordinary spear rows are never overwritten.

The three native jabs reference private BoPkAttacks: base damage8, range275, ChargeTime0, charged/perfect damage0. No additional0.4 multiplier is applied. After native equipment initializes the owner-bound attack cache, the script verifies all three private row handles, range275, CanCharge=false and item damage modifier1; a mismatch removes the candidate item in the same game-thread operation.

The accepted root-rigid crook attaches to the actual native Spear02 static-mesh component. Native equipment supplies the grip, carry angle, first/third-person arm animation and thrust. Only native weapon rendering is suppressed; its collision and attack execution remain. Shaft cross-section is1.35 times the accepted mesh, length matches native cooked bounds. No added FP hand, camera offset, custom attack timer or registered skeletal-mesh reassignment.

## First test scope

Host/standalone Willow only. Empty both hands and press **F10** to create/equip the test crook; press F10 again to remove it. Automatic empty-hand equipment, client requests/replication and long-term save/inventory cleanup remain active work. This limited developer control is not the final behavior.

Remove the test item with F10 before changing gear, saving, leaving or uninstalling this candidate. Keep BoPeepCrook disabled during this isolated test. The candidate uses a real native item, so it must not be treated as an invisible cosmetic-only component. If an unexpected stop leaves it present, use normal equipment controls to remove the test item before saving. Do not test charging or throwing.

## Offline evidence

- Both private cooked tables independently deserialize with current UE5.7.4 mappings;425 attack rows and all three edited profiles checked.
- The empty private item table reads back as Maine.BaseItemData. Deterministic source rebuild is byte-exact.
- Retoc repack/re-extraction validates container/header identities and all chunk hashes.
-25 production-Lua fixture groups cover deep-copy isolation, unsupported row/schema rejection, cache validation and rollback, authority/equipment guards, deferred component assignment, view visibility, native component replacement and original render-state restoration. These do not prove Unreal rendering, animation, networking or saving.

Reproduction: `pipeline/spear-reference/build_private_crook_items.py`; Lua checks: `python pipeline/spear-reference/test_native_crook.py`. Native asset evidence is in `docs/native-spear-next/native-item-v1/`.
