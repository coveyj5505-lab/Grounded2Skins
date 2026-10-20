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
