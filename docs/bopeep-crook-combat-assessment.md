# Deferred Bo Peep cosmetic crook combat assessment

User priority: finish Jessie and current Bo Peep hand/cape fixes first. This is an initial feasibility assessment, not an implemented feature or confirmed game hook. Preserve the separate original crook mesh, textures, source weights/transforms and authored prop pivot in the Bo Peep project. Do not embed it permanently in the playable body.

## Simplest architecture

Use one separately rendered, cosmetic crook component attached to the character's existing right-hand bone, with a fitted local translation/rotation. `r_hand_JNT` is actually present at mesh-local index 147 in the verified stock Willow table; `l_hand_JNT` is index 53. Attach by bone name rather than assuming a custom socket or altering the shared game skeleton. The source `e_stick` pivot is an authoring candidate, not a verified game hand attachment transform.

Keep the original animation blueprint, locomotion and punch animations. A hand attachment follows those animations automatically; no custom animation system is required for the basic visual test. Walking/running will use the original empty-hand motion, and punches will move the crook along the fist's existing short arc. This does **not** turn a punch into a convincing full staff swing. Long ends can clip the body/environment and look detached from the expected impact. Reusing an actual weapon animation would need a game-specific animation/equipment binding investigation; it is not the simplest initial option and could affect pose/timing. Do not change attack damage, traces, collisions, reach or timing to match the crook's visible length.

The crook component must have collision, physics simulation, hit/overlap generation and damage participation disabled. Character capsule, movement and unarmed combat remain original. Hide it conservatively in seating, climbing, swimming or other interaction states where clearance is poor; exact game state accessors are not yet established.

## Mesh replacement alone cannot implement the requested visibility

Our current pipeline writes cooked skeletal render buffers, static skin weights, textures/material references and IoStore metadata. It has no event handlers and does not observe inventory, shields, interactions or gliding. Skinning crook vertices rigidly to a hand would make them always present wherever the body mesh renders. A new mesh section or fixed material does not create an equipment-state controller. Do not claim the current skin ZIP can already implement the requested behavior.

The visibility rule needs equipment/state logic, preferably on a separate accessory component:

| State | Hand crook |
| --- | --- |
| Bo Peep, unarmed, ordinary walking/running/idle/punching | Visible |
| Any weapon equipped | Hidden |
| Any shield equipped, even if the weapon hand is otherwise empty | Hidden |
| Sitting/climbing/interaction states with major clipping | Hidden |
| Gliding | Hidden; reserve the future parasol representation |
| Another character or unknown/unsupported state | Hidden |

React to equipment changes and interaction transitions; returning to an eligible unarmed state restores visibility. A one-time spawn check is insufficient. Scope the condition to Bo Peep/Willow's skin context rather than globally replacing an unarmed mesh for every character. Account for death, respawn, character switching and equipment changes during interactions before shipping.

## What is and is not verified

Verified local evidence: stock Willow hand bone names; preserved separate crook geometry; working skin loading; no equipment-controller/character Blueprint assets in the skin package. Existing selected stock data is skeletal/physics data, not a decoded character equipment graph.

Unverified: whether Grounded 2 already exposes a separate unarmed held-item visual component that disappears automatically for *both* weapons and shields, whether an existing data asset can assign its mesh per character, and the exact equipment/interaction/glide signals. If such a component/data path exists and can be scoped to Willow, reusing it would be the smallest content-based solution. Do not invent the package path or assume empty-hand attacks have a rendered weapon asset.

Otherwise, the smallest implementation is accessory attachment + visibility logic through a verified game Blueprint entry point or a supported runtime mod hook. An Animation Blueprint change is not inherently required to follow a hand or toggle a component; prefer leaving it intact. Merely adding a newly cooked Blueprint to a PAK will not make the game spawn or run it: a compatible reference/loading entry point must exist. An arbitrary UE5.6 cook, UE4SS compatibility or Game Pass runtime access is **not verified** by the successful mesh pipeline. No injection framework or loader is being installed for this assessment.

## Bounded next investigation, after current work

First inspect the matching game's actual character/equipment definitions or a supported runtime inspection facility for an existing held-item visual and equipment events. Only request exact additional package paths after discovering them; no full UCAS upload or speculative Blueprint filename list. Then test one cosmetic attachment with collision disabled and a debug visibility switch, before connecting real equipment/shield/interaction state. Retain stock punch animations first; evaluate staff clipping in walking, running and attack poses. Do not author new combat animations or change gameplay as a prerequisite.

## Future glider coexistence

Keep one shared accessory-state policy: when not gliding, the eligible unarmed hand crook may be shown; while gliding, hide the hand copy and let the future crook/parasol representation take ownership. Do not independently spawn two visible copies. The original separate source object/pivot and optional distinct future parasol mesh can be reused without rebuilding the Bo Peep body or changing its proven packaging. This is a design boundary, not an implemented gliding feature.
