from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "dayflow.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)
def make_icon(size):
    k=size/256
    im=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(im)
    def box(v): return tuple(round(x*k) for x in v)
    d.rounded_rectangle(box((8,8,248,248)),radius=round(70*k),fill="#172B43")
    d.rounded_rectangle(box((48,48,208,208)),radius=round(38*k),fill="#EAF2FF")
    d.rounded_rectangle(box((72,78,184,180)),radius=round(13*k),fill="#F7FAFF")
    d.line([box((72,105)),box((184,105))],fill="#5F8FCB",width=max(2,round(12*k)))
    d.line([box((96,66)),box((96,91))],fill="#5F8FCB",width=max(2,round(10*k)))
    d.line([box((160,66)),box((160,91))],fill="#5F8FCB",width=max(2,round(10*k)))
    d.line([box((91,142)),box((109,160)),box((161,112))],fill="#69D3C8",width=max(3,round(13*k)),joint="curve")
    d.ellipse(box((168,166,192,190)),fill="#69D3C8")
    return im
base=make_icon(256)
base.save(OUT,format="ICO",sizes=[(n,n) for n in (256,128,64,48,32,16)])
base.save(OUT.with_suffix(".png"),format="PNG")
print("Created",OUT)
