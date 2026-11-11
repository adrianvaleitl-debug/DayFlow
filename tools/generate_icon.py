from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "dayflow.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)
def make_icon(size):
    k=size/256
    im=Image.new("RGBA",(size,size),(15,23,39,255)); d=ImageDraw.Draw(im)
    def box(v): return tuple(round(x*k) for x in v)
    d.rounded_rectangle(box((12,12,244,244)),radius=round(58*k),fill="#17243A")
    d.arc(box((54,52,202,200)),start=42,end=318,fill="#7FA8FF",width=max(3,round(19*k)))
    d.line([box((86,132)),box((116,160)),box((174,98))],fill="#F4F7FF",width=max(4,round(17*k)),joint="curve")
    d.ellipse(box((164,54,202,92)),fill="#73D8C7")
    return im
base=make_icon(256)
base.save(OUT,format="ICO",sizes=[(n,n) for n in (256,128,64,48,32,16)])
base.save(OUT.with_suffix(".png"),format="PNG")
print("Created",OUT)
