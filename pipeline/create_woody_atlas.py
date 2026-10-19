"""Six supplied diffuse sheets + original-art eye composite, originals intact."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
src,out=map(Path,sys.argv[1:]);out.mkdir(exist_ok=False)
atlas=Image.new('RGBA',(4096,4096),(245,245,238,255));layout={'size':4096,'tiles':{}}
for i,part in enumerate(['Hat','Boots','Clothes','Shirt','Hair','Head']):
 p=src/f'Woody_{part}_D.tga.png';im=Image.open(p).convert('RGBA');assert im.size==(2048,2048)
 x,y=(i%3)*1360+16,(i//3)*1360+16;tile=im.resize((1328,1328),Image.Resampling.LANCZOS);atlas.paste(tile,(x,y));layout['tiles'][part]=[x,y,1328,1328]
head=Image.open(src/'Woody_Head_D.tga.png').convert('RGBA');eye=Image.new('RGBA',(1024,1024),head.getpixel((150,550)));iris=head.crop((1536,0,1712,180)).resize((360,360),Image.Resampling.LANCZOS);mask=Image.new('L',(360,360));ImageDraw.Draw(mask).ellipse((24,24,336,336),fill=255);eye.paste(iris,(332,332),mask);eye.save(out/'Woody-original-art-eye-composite.png');atlas.paste(eye,(16,2752));layout['tiles']['Eyes']=[16,2752,1024,1024];layout['tiles']['White']=[1100,2800,16,16]
layout['eye_method']='Supplied Head diffuse brown iris crop, circular mask on supplied white pixel; planar UVs on existing eye geometry. Source art unchanged.'
layout['original_iris_crop_xyxy']=[1536,0,1712,180];atlas.save(out/'Woody-basecolor-atlas.png');(out/'atlas-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
