# Bo Peep first gameplay feedback and focused diagnosis

The user confirmed walking, running, jumping and crouching. Screenshots also show the character textured while seated and from behind, with malformed hands/fingers and visible upper-cape gaps. Do not infer punching, backpack toggling or exhaustive crash-free animation coverage. The original tested ZIP, source Blender scene and cooked stages remain unchanged.

Read-only inspection of the actual source/fitted scene identifies two concrete issues in `rig_bopeep_blender.py`:

- Terminal middle/index finger groups and the final thumb groups use identity fit rotations because their specification has no next segment. Their preceding segments receive directional alignment. This gives inconsistent geometry fitting across the same finger. The source also has only three deform finger chains per side; mapping those by name alone does not establish correct ring/pinky motion. The original controlled arm/head pose test did not exercise finger curls. Any correction must add dedicated hand/finger tests and preserve native bone rest tables.
- Among the 936 vertices with source cape influence, 54 also have shoulder/scapula/arm influence. Mapping `e_cape*` to the torso alone does not remove these other source influences, so upper cape vertices can follow different transforms. This is a plausible source of shoulder-region distortion, not proof that every screenshot gap has the same cause. Winding/backface culling and cape/body intersections still need targeted inspection before adding geometry or changing materials.

Audit log: `/workspace/mod-work/bopeep-stage/hands-cape-audit.log`. The original source back render shows an intact upper cape. No new physics, cloth, input or movement mechanics are warranted. Make any corrected rig/package in new stages; do not replace the known working ZIP. Jessie preparation continues independently against stock Hoops data.
