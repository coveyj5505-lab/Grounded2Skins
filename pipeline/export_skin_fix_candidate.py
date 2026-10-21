"""Run the existing character exporter on an isolated fixed scene."""
import sys
from pathlib import Path
character,reference,output=sys.argv[sys.argv.index('--')+1:];source=Path(__file__).with_name('export_'+character.lower()+'_geometry.py');sys.argv=[str(source),'--',reference,'unused',output,'--skinned'];exec(compile(source.read_text(),str(source),'exec'),{'__name__':'__main__','__file__':str(source)})
