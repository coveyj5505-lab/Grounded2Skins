# Independent Bo Peep crook carry test

Current script: **0.1.3**, Windows pending. Version 0.1.2 now successfully selects the actual Willow backpack mesh, validates all preflight signatures and confirms the hand bone. It stops at private asset loading, before component creation. The exact Beta UE4SS LoadAsset helper queries the asset registry, so it cannot establish whether an unregistered private IoStore asset is loadable. Version 0.1.3 uses native MakeSoftObjectPath, Conv_SoftObjPathToSoftObjRef and LoadAsset_Blocking through the KismetSystemLibrary CDO, with signature and receiver checks. UE4SS ca6f9b4c source confirms SoftObjectProperty get/set and local TSoftObjectPtr value ownership; Windows execution remains pending.

User preference: **drag and drop only; no installer/updater scripts or README in new downloads.** New file-only ZIP contains main.lua and the three unchanged crook Paks. Keep mods.txt and all four skins unchanged.

Fourteen carry Lua mock regression groups pass, including a forbidden registry-only helper, native soft-load chain, missing package, missing guessed properties, assetless base mesh fallback, wrong player, signature rejection, occupancy, both views and cleanup. These do not execute Unreal. The log now records separate path, loaded asset identity, component creation, hand attachment, visibility read-back and final success/error milestones, including exact asset path, phase and last native function on errors. Fresh retoc unpack independently confirms the Zen summary package name and top-level SkeletalMesh export match the Lua path exactly; see crook-object-path-validation.json.

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
python pipeline/package_crook_dragdrop.py --assets /workspace/mod-work/crook-stage/package-v1/mod
```

Five carry lifecycle/visibility/error-path Lua mock groups and seven existing recorder mock groups pass. They execute Lua 5.4 through liblua, not UE4SS or Unreal. Retoc verifies the original isolated asset; the ZIP builder independently reads every archive entry back and compares it to source bytes. No PowerShell or native Unreal runtime is available here, so the installer and attachment still require Windows validation.

Copy `BoPeepCrook/Scripts/main.lua` into the existing UE4SS mod and the three `Paks` files into Augusta/Content/Paks. Existing files with these crook-only names can be replaced; working character packages are untouched. Roll back by restoring the prior main.lua or disabling BoPeepCrook and removing only zBoCrookAsset_P files.
