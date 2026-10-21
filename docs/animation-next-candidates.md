# Isolated animation preparation after v0.3

The released ToyStory-Buzz-BoPeep-Test-v0.3.zip and runtime Lua files remain frozen. None of the work here is installed by the separate Woody update. Current SDK headers describe an older build: names/signatures are leads, not proof of availability in the running game. No memory offsets are used.

## Buzz flight visual target

A separate Blender candidate reuses the v0.3 arm-corrected body, original 230-bone rest skeleton, and preserved extended wing geometry. It pitches the body forward 65 degrees, counter-rotates the neck 55 degrees, and brings the arms forward with slight outward clearance. Body geometry, UVs, weights and rest matrices are unchanged. Standing with manually extended wings remains upright. A fresh offline reset restores the original pose; this is not a test of the native glide animation or a runtime implementation.

The target scene and pose matrices are private in /workspace/mod-work/woody-polish-next/buzz-flight-candidate-v1. Reproduce with prepare_buzz_flight_pose_candidate.py on Buzz-Arms-Cooked-Verified.blend. Public previews show the target, not gameplay.

The confirmed game-side signal remains IsGliding(), including reusable-trinket gliding. Flight pose must depend on actual gliding only; the manual wing preference must not enter its activation condition. Landing, pawn replacement, mod shutdown and any failure must restore the normal visual presentation.

The smallest promising isolated runtime experiment is a collision-free, third-person-only visual proxy, with a poseable component and the original game mesh still providing animation/gameplay state. Engine.PoseableMeshComponent declares CopyPoseFromSkeletalComponent, GetBoneTransformByName and SetBoneTransformByName in the downloaded SDK. These are generic Unreal functions; none is yet verified through UE4SS in this game. All bone-space enum values and UFunction signatures must be resolved live before use. The saved target can be applied to the proxy without changing the pawn, capsule, movement component or camera transforms.

This approach still needs careful native-render visibility restoration, always-updated source animation, alignment of the independent wing component to the posed chest, and first-person isolation. Keep the native component and camera hierarchy unrotated. Do not rotate the player actor or the existing body component merely to get the flying silhouette. If a post-process AnimBP route is used instead, its cooked serialization and socket/camera consequences must be established first. No new Windows probe is needed just to view the offline candidate; runtime integration follows v0.3 wing-loading results.

## Bo Peep native spear animation

Existing successful Windows recordings already establish the montage for normal and charged spear attacks, both spear-only and spear-plus-shield:

/Game/_Augusta/Art/Characters/Player_Male01/Animation/Combat/AM_Player_Character_Attack_Spear_01_Augusta.AM_Player_Character_Attack_Spear_01_Augusta

Do not repeat the earlier action sequence to rediscover this path. Actual hand-slot contents are established; bHasMainHand/bHasOffHand are unsuitable occupancy signals.

The downloaded Grounded 2 SDK supplies concrete reasons not to blindly swap a montage on the gameplay AnimInstance:

- Maine.Attack exposes GetAnimMontage, GetAttackDataRowHandle and ConsumesStaminaOnHitFrame. Its public declarations do not expose a cosmetic SetAnimMontage override.
- Maine.AttackData contains AttackAnim, WeaponAnim, damage/range/stamina fields and charge behavior in the same gameplay data structure. Replacing an attack row is outside the cosmetic requirement.
- Maine.AnimNotify_HitFrame, AnimNotifyState_HitActive and AnimNotifyState_MultiHitFrame carry hit-resolution information. AnimNotifyState_AttackRootMotion and AnimNotifyState_CurrentAttackPlayRateModifier also exist.
- Engine.AnimInstance exposes montage playback and notify queues. Montage_Play is generic playback, not proof that combat notifies or root motion are harmless.

These declarations establish coupling risks, NOT that the recorded spear montage contains every listed notify. The actual current-build cooked spear montage and its sequence dependencies have not been extracted in the existing character-only artifacts. Sections, hit/contact frames, charge loops, notifies, root-motion tracks and FP/TP slot tracks still need direct asset inspection. The exact montage above is the minimum starting asset; follow only dependencies named by its actual export, rather than guessing package names. No additional gameplay test is requested now.

Do not call attack RPCs, equip a spear, overwrite shared attack data, or play an uninspected native spear montage on the gameplay animation instance. Even a notify-free replacement can move sockets used for traces, altering effective hit behavior. A visual-only proxy or a separately verified cosmetic animation layer is the safer candidate for preserving native unarmed hit timing and reach. It should follow the existing unarmed attack phase while the original game animation executes untouched, use native spear pose tracks, and attach the crook to the visual hand. It must return to upright carrying and hide on either occupied slot, leaving damage/stamina/timing/trace execution unchanged.

This is a targeted implementation boundary, not a claim that animation substitution is finished. Keep v0.3's simpler cosmetic hook-first crook motion until the pose/notify separation is verified. Spear motions are not assumed to require two hands.

## Cape

Leave the released v0.3 neckline unchanged until its Windows results arrive. The remaining small collar/lining artifact stays on the active checklist. No further proportions pass or lower-cape rebuild is justified while larger features are pending.

## Further preparation completed without Windows input

The forward target now also has a separate baked full-body-plus-wings cosmetic asset, /Game/_BzFlit1/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01. It uses the proven accessory layout with192 reference bones and root0-only weights; the native player body keeps its original230-bone animated skeleton. The fixed target matches Blender's evaluated body to3.72e-7m. This is a static cosmetic flight pose, not a replacement native animation.

The first cooked preview exposed a real material-layout mismatch: the wing-only atlas uses different repeat bounds from the body's atlas. That candidate was rejected even though its native buffers parsed correctly. The accepted preparation remaps body UVs into the left half and wing UVs into the right half of a new private4096x4096 atlas in /Game/_BzFMat1. This halves horizontal texel resolution for this optional flight visual, preserving recognizable color placement. Original body/wing atlases and all eight original textures remain unchanged. New albedo mip records are encoded into measured native payload ranges; the remaining three texture chains remain exact.

The prepared files are private under /workspace/mod-work/woody-polish-next/buzz-flight-baked-v2, buzz-flight-native-v2, buzz-flight-package-v2 and buzz-flight-check-v2. Reproduction adds bake_buzz_flight_visual.py, build_buzz_flight_visual_asset.py, the existing retoc pack/read-back helpers, validate_buzz_flight_visual_asset.py and render_buzz_flight_visual_readback.py. The public cooked preview is an offline asset preview, not gameplay proof.

An isolated adapter is staged in experiments/BuzzFlightVisual/Scripts. It is DISABLED by default, has no default key, no enabled.txt and is not in any playable ZIP. It uses the existing validated soft-object loading and UObject access approach. In a future test it will show the cosmetic only for actual third-person gliding, temporarily suppress native Buzz render components and upright wing components, and restore their previous visibility on landing or entering first-person. The real pawn/capsule/camera transforms and movement functions are untouched. Hidden native source meshes retain animation updates using a live-reflected VisibilityBasedAnimTickOption enum; the exact prior value is restored. This new property access still requires Windows validation.

Fifteen real-Lua controller fault-injection groups and ten adapter fixture groups pass. They cover glide/landing, manual preference independence, first-person restoration, failed loading/signatures/field types, partial suppression rollback, policy restoration, missing/destroyed components and retries. These are mocked objects, not evidence of native UE4SS execution. No advanced flight feature is installed. Keep the original tuft visual until its separate cosmetic visibility route is verified.

For spear inspection, extract_animation_dependencies.py reuses the existing pinned retoc listing and Zen header reader. Its default target is the exact Windows-recorded spear montage; it follows only actual indexed animation imports and imported skeletons, bounded to32packages/64MiB. Local validation on a real existing container recovered5packages/9chunks exactly, retained a usable partial report at the budget boundary, and reported missing targets without guessing. It never changed source file sizes or modification times. This helper is prepared for the minimum additional asset collection when convenient; no additional gameplay sequence or Windows action is requested now.

The small upper-cover-only cape adjustment was rejected: the white shoulder seam persisted in the preview. No source skin was recolored and no lower-cape changes were made. Keep that minor artifact on the checklist instead of shipping a speculative repair.


## Current-build collection now received (2026-10-21)

The targeted spear collection is complete:1 AnimMontage,14 AnimSequence packages and1 Skeleton. Actual Zen export tables resolved against current global script objects contain HitFrame notify instances in FP and TP normal swing and charged end clips. Missing source payloads are no longer the blocker. The next step is decoding actual montage wiring, animation tracks/timing and notify/root-motion properties, then separating cosmetic pose playback from gameplay execution. No claim of native spear substitution, safe native Montage_Play, or decoded notify timing is made. No new collection requested. The released tests remain frozen.
