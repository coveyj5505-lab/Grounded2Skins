# Independent Bo Peep crook carry test

Current script: **0.1.1**, Windows pending. The 0.1 log confirms loading and F9 callbacks, but a silent eligibility return prevented any attachment attempt. The log cannot distinguish a missing local pawn from the guessed Blueprint class mismatch. The corrected script checks the actual verified Willow skeletal mesh path (including backpack variant), logs the actual pawn/mesh identity or missing-pawn condition, and has seven passing carry regression groups. Existing v0.1 ZIP is preserved as historical; install the script-only `BoPeep-Crook-Update-v0.1.1.zip` over it. No assets change.

First Windows attachment test. Native placement, visibility, component API marshalling and registration remain unverified until the user runs it. Local-client cosmetic only, not replicated to other clients.

Reuses the independently decoded four-LOD private crook package and the Windows-confirmed no-Reflection UObject access path. Native UFunction parameter names/types and receiver ancestry are checked before calls. All required signatures, enums, asset availability and the right-hand bone are checked before component creation. A missing/changed API stops with a specific log entry, without guessing offsets or retrying native mutations.

The local pawn using the verified Willow Female01 skeletal mesh receives a deferred SkeletalMeshComponent through AddComponentByClass. Before assigning the asset or finishing registration, it is hidden, collision/simulation disabled, post-process BP disabled, animation disabled and cloth disabled. Only this new component gets visibility and owner-view flags. It attaches to r_hand_JNT; inverse socket-world rotation establishes an upright grip offset at activation. Stand upright, empty hands, F9 once. F9 again destroys only this component. Pawn replacement cleans it up; a Lua failure stops and attempts component removal. Lua protection cannot contain a native access violation.

Actual GetItemInSlot(MainHand/OffHand) identities control visibility. Slot enum values are resolved from the running game, not copied from the SDK. Neither bHas flag is read by the carry update. Both first- and third-person views remain eligible; no native body/head/camera settings are changed. GetIsFirstPerson is logged only when it changes. Visibility polling is 200 ms.

Attack substitution is deliberately absent in this first attachment test: native unarmed attacks remain unchanged. No equipment, damage, stamina, reach, collision, movement, save or attack RPC changes. Interaction-specific hiding, final FP grip offsets and multiplayer replication are future work. All four skin ZIPs and their packages remain unchanged. The private crook still imports the installed Bo Peep atlas/skeleton; it is not a standalone skin.

## Reproduce

```sh
python pipeline/test_crook_carry.py
python pipeline/test_accessory_check.py
/workspace/mod-work/bin/retoc verify /workspace/mod-work/crook-stage/package-v1/mod/zBoCrookAsset_P.utoc
python pipeline/package_crook_carry.py --assets /workspace/mod-work/crook-stage/package-v1/mod
```

Five carry lifecycle/visibility/error-path Lua mock groups and seven existing recorder mock groups pass. They execute Lua 5.4 through liblua, not UE4SS or Unreal. Retoc verifies the original isolated asset; the ZIP builder independently reads every archive entry back and compares it to source bytes. No PowerShell or native Unreal runtime is available here, so the installer and attachment still require Windows validation.

Install.cmd selects the existing Paks and UE4SS Mods directories and refuses to overwrite any crook files. It writes a per-file hash receipt. Uninstall.cmd removes only matching installed files and empty accessory directories, preserving modified files. Keep the extracted folder for rollback. Disable earlier F9 probes before use; the installer does not change their configuration.
