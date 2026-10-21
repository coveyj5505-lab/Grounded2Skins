"""Frozen model sources for the remaining5.7.4 skin-only migrations."""
from pathlib import Path
ROOT=Path('/workspace/mod-work');STAGE=ROOT/'ue57-migration'
CONFIG={
 'Woody':dict(stock='Pete',old=ROOT/'anatomy-corrections/woody-package-v1/unpacked',namespace='_Woody00',tag='Wdy',slots=(0,3),atlas=ROOT/'woody-stage/atlas-v1/Woody-basecolor-atlas.png',mod='zWoodyUE57_P'),
 'BoPeep':dict(stock='Willow',old=ROOT/'refinement-next/bopeep-cape-v4h/package/unpacked',namespace='_BoPeep0',tag='Bop',slots=(0,3),atlas=ROOT/'bopeep-stage/bopeep-atlas.png',mod='zBoPeepUE57_P'),
 'Buzz':dict(stock='Max',old=ROOT/'refinement-next/buzz-arms-v1/package/unpacked',namespace='_BuzzMod',tag='Buz',slots=(0,5),atlas=ROOT/'buzz-v2-stage/atlas/Buzz-basecolor-atlas.png',mod='zBuzzUE57_P')}
