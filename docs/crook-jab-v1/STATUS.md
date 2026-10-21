# Crook jab V1: isolated cosmetic animation test

The user accepted Buzz skin/arms as final and moved priority to crook animation. Woody/Jessie remain final. Bo Peep V4 body/cape/staff-only presentation is the accepted baseline.

This iteration animates only the existing separate crook component. It does not substitute the native spear montage or change Bo Peep's arm pose. The existing collected native spear clips contain AnimNotify_HitFrame objects; directly playing those on the gameplay instance is not an established way to preserve unarmed damage/timing. The16 current-build animation packages remain intact; no repeat collection is needed for this cosmetic pass.

## Motion

- Actual unarmed bIsAttacking rising edge starts a single cosmetic jab.
-70ms ease from upright into85-degree hook-first orientation and a small FP anticipation draw, then100ms forward FP thrust. TP shaft remains at the existing hand contact and follows the vanilla hand motion.
- Attack end starts160ms eased upright recovery. A new attack during recovery starts continuously from the current visible state.
- Held native attack flags do not invent additional gameplay attacks. Full combo-specific arm animation is not implemented.
- Read-only live-signature-checked GameplayStatics.GetTimeSeconds provides pause-aware/world-time motion. Missing/invalid clock falls back to the prior instantaneous cosmetic behavior and logs once; accepted carry remains available.
-33ms polling; startup diagnostics deduplicated to avoid multiplying per-frame log output.
- Current persistent TP/FP components, actual equipment gating, staff-only FP appearance, right-edge placement, thickness and optional FP shadow flag retained. No extra first-person hand.
- Native FP staff geometry checked at201 orientations and recoil/neutral/thrust extremes: minimum forward clearance16.85cm. During jab only, add22cm forward clearance proportional to tilt and12cm thrust; resting85/right72/down32 baseline unchanged (including existing right-edge calibration).

## Verification and limits

10 actual Lua motion groups and35 mocked adapter/lifecycle/projection groups pass. Added native call is only the read-only game clock. No montage/sequence playback, damage/stamina/reach/timing/hit-trace changes, equipment writes, actor/camera movement, new Paks, model edits, or cached camera-return lifecycle mutations.

Windows animation appearance and actual attack-state timing remain unverified. If the game holds bIsAttacking across an entire combo, this first pass holds one jab rather than inventing repeated attacks. User can review the useful crook motion now; full native spear-arm animation remains separate and incomplete.
