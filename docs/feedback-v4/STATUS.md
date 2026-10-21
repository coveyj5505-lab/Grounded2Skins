# Buzz V3 Windows feedback — next candidate

V3 remains frozen. New files live in runtime-feedback-v4 and /tmp/toystory-feedback-v4.

## Confirmed from Windows log

Log SHA256 is recorded below. At 17:34:18.183 the forward proxy becomes active. BuzzWings replaces the retracted component with a deployed component at 17:34:18.216. At 17:34:18.377 the old flight controller destroys its proxy because the component set changed, then reports a visibility restoration mismatch and stays RESTORATION_PENDING throughout the remainder of that glide. Another glide begins at 17:36:07.892 while restoration is still pending; flight finally resumes at 17:36:12.971. This supports the user's intermittent flight observation. Old errors do not identify the individual failing component, so retirement of the discarded private wing is the targeted candidate, not a native-confirmed repair.

## Prepared changes

- Reconcile newly created wings and late tuft components into the existing flight suppression transaction. Do not rebuild a working flight proxy merely because the wing mod replaced its own component.
- Discard missing private wing components from restoration obligations; their owning mod handles destruction/recreation. UE4SS IsValid alone does not establish that a discarded component accepts visibility writes.
- Restore other removed components, including an item visual that outlives the active-glider query.
- Suppress the exact owned SK_SCAB wrist-device component only during flight. The screenshot shows a glove/device above the flying body; its disappearance remains to be confirmed in Windows.
- Leave ThirdPersonShadow components under native control. Continue preserving the original source body's animation-tick policy.
- Include component identity, purpose, and requested visibility in future mismatch errors.
- Preserve F1 manual OR actual-glide wing logic, native movement/camera/physics, and persistent Bo Peep lifecycle.

22 controller and 22 adapter mocked-Lua regression groups pass, including a still-valid discarded wing whose restoration fails. No native Windows acceptance yet.

## Arm geometry

The source/native weight audit confirms upper shells average 66–67% chest attachment mixed with upperArm; elbow and forearm pieces are already rigid lowerArm. Prepared a rigid upper-shell experiment preserving the controlled idle silhouette exactly, with unchanged skeleton, hand weights, textures, elbows, and forearms. This is an offline experiment pending posed render review, not a released skin or confirmed jump-animation correction.

Other three characters remain on V3 while the user collects results. No new Windows test is required yet.
4fe39ce37a6efe28cfc81b28524099511f79ec9b49eb2b6837381f2016041070  /workspace/attachments/6d0765b0-55cc-4114-9ded-3a31ddced01c/UE4SS.log

Controlled FK strain check: V3 upper-shell edge-length ratios reach4.76 on raised arms and2.72 on bent arms relative to controlled idle. The rigid candidate stays within0.003% of its idle edge lengths. This confirms deformation reduction, not shoulder/elbow fit or native-animation acceptance. See controlled-pose-strain.json.

## Render review: rigid upper-shell experiment rejected

Raised FK preview still moves the arm shells too close to the head; stopping edge stretch does not repair the mismatch between native narrow shoulder pivots and broad Buzz armor. Do NOT cook or ship Buzz-rigid-upper-candidate.npz. V3 Buzz skin remains installed. Further correction must address pivot/socket fit or use a practical geometry compromise, rather than repeat shell-only clearance changes. Preview arm-candidate-rejected.jpg records this decision.

## Bo Peep preference change

User accepts body/cape as good enough and explicitly requests no added FP hand/forearm. New runtime always selects existing FP_STAFF asset, keeps current projection/thickness and persistent FP/TP lifecycle, and retains cosmetic jab. Optional live-signature-checked PrimitiveComponent.SetCastShadow(false) applies only when creating the separate FP staff; missing API leaves carry working.31 mocked Lua carry/lifecycle/projection/shadow groups pass. No asset rebuild needed; user prefers spear animation work after skin finalization.
