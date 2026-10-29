"""Local, restartable icon queue. No network calls or API keys."""
import argparse,csv,hashlib,json,re,shutil,sqlite3,tempfile,unicodedata,zipfile
from pathlib import Path
from collections import Counter
BASE=Path(__file__).resolve().parent
ROOT=BASE/'catalog' if (BASE/'catalog').is_dir() else BASE
STYLE='''Create exactly ONE premium corporate website service icon for: {title}.
Understand the service and choose one recognizable primary object with at most two minimal supporting elements. Distinct compact visual metaphor, professional enterprise aesthetic.
Square canvas, centered icon occupying approximately 60–65%, generous equal margins. Clean flat 2D vector-style outlines, consistent medium-thin geometric strokes, rounded caps and joins. Mostly outline construction with tiny controlled fills only.
Use ONLY charcoal #202123 for dominant structure and crimson #C31E25 for purposeful functional accents. BOTH colors must be visible.
Genuine transparent alpha background, including enclosed negative spaces. No white fills, painted checkerboard, text, letters, numbers, logos, watermarks, gradients, shadows, textures, lighting, 3D, enclosing background cards or decoration. A single question mark may be used for FAQ subjects.
Use highest available native resolution; do not upscale. Match reference.png when available for style only. Never render the filename or title as text. Output a separate PNG.
'''
SVG_STYLE='Author one native SVG icon for: {title}.\nSVG FIRST: construct editable geometry directly; do not trace a PNG, embed a raster, or use the image-generation tool for the vector source. Use square viewBox="0 0 128 128", fill="none", a consistent 3-unit stroke-width with round caps/joins, and only #202123 and #C31E25. Use simple paths, circles, rectangles and symmetric curves. No CSS, transforms, external links, scripts, text, numbers, logos, white fills, gradients or shadows. Use filled dots only for small functional details. Keep generous transparent margins and clear spacing; prevent overlapping contours and crowded joins. Inspect at 48, 64 and 256 pixels; mathematical stroke consistency alone does not prove optical quality. Save source SVG, then use accept-svg ID SOURCE.svg --size 1024 to export and verify the matching transparent PNG. Do not regenerate completed artwork.\n'
def db():
 c=sqlite3.connect(ROOT/'progress.sqlite');c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS icons(id INTEGER PRIMARY KEY,title TEXT,filename TEXT UNIQUE,batch INTEGER,status TEXT DEFAULT "pending",attempts INTEGER DEFAULT 0,error TEXT DEFAULT "")')
 return c
def init():
 c=db()
 if c.execute('SELECT count(*) FROM icons').fetchone()[0]:return
 titles=[x.strip().removeprefix('[').removesuffix(']').strip() for x in (ROOT/'services.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
 used=set()
 for i,t in enumerate(titles,1):
  slug=re.sub(r'[^A-Za-z0-9]+','-',unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode()).strip('-')[:130] or 'Service'
  name=slug+'.png'
  if name.casefold() in used:name=f'{slug}-{i:04d}.png'
  used.add(name.casefold())
  c.execute('INSERT INTO icons(id,title,filename,batch) VALUES(?,?,?,?)',(i,t,name,(i-1)//10+1))
 c.commit();c.close();export()
def export():
 c=db();rows=c.execute('SELECT * FROM icons ORDER BY id').fetchall()
 with (ROOT/'progress.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['id','title','filename','batch','status','attempts','error']);w.writerows(tuple(r) for r in rows)
 return rows
def validate(path):
 from PIL import Image
 with Image.open(path) as im:
  im.load()
  if im.format!='PNG' or im.width!=im.height:raise ValueError('Must be a square PNG')
  if im.mode!='RGBA':raise ValueError('Must contain RGBA alpha transparency')
  alpha=im.getchannel('A')
  if alpha.getextrema()!=(0,255):raise ValueError('Must contain transparent and opaque pixels')
  box=alpha.getbbox()
  if not box or min(box[0],box[1],im.width-box[2],im.height-box[3])<im.width*.03:raise ValueError('Artwork empty or too near canvas edge')
  pixels=list(im.getdata());visible=[p for p in pixels if p[3]>200]
  if not any(r>g*1.6 and r>b*1.6 and r>90 for r,g,b,a in visible):raise ValueError('Missing crimson accent')
  if not any(max(r,g,b)<100 and max(r,g,b)-min(r,g,b)<35 for r,g,b,a in visible):raise ValueError('Missing charcoal outlines')
  if sum(min(r,g,b)>235 for r,g,b,a in visible)>len(visible)*.01:raise ValueError('Visible white fill detected')
 # This is technical validation, not proof of semantic or visual correctness.
def packet(batch):
 rows=[r for r in export() if r['batch']==batch]
 if not rows:raise ValueError('Unknown batch')
 d=ROOT/'work'/f'batch-{batch:03d}';d.mkdir(parents=True,exist_ok=True)
 jobs=[]
 for r in rows:
  if r['status']=='complete' or r['attempts']>=3:continue
  prompt=STYLE.format(title=r['title']);pf=d/f"{r['id']:04d}.txt";pf.write_text(prompt,encoding='utf-8')
  output=ROOT/'output'/f'batch-{batch:03d}'/r['filename']
  jobs.append(dict(id=r['id'],title=r['title'],prompt_file=str(pf),output=str(output),svg_output=str(output.with_suffix('.svg'))))
 return jobs
def accept(id,source):
 c=db();r=c.execute('SELECT * FROM icons WHERE id=?',(id,)).fetchone()
 if not r:raise ValueError('Unknown icon ID')
 if r['status']=='complete':return
 from vectorize import convert
 out=ROOT/'output'/f"batch-{r['batch']:03d}"/r['filename'];out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='fws-accept-') as folder:
  cleaned=Path(folder)/'cleaned.png'
  count=clean_alpha(source,cleaned)
  if count:
   original=ROOT/'work'/'originals'/f"{id:04d}-{hashlib.sha256(Path(source).read_bytes()).hexdigest()}.png"
   original.parent.mkdir(parents=True,exist_ok=True)
   if not original.exists():shutil.copy2(source,original)
   print(f'Preserved original: {original}; cleared {count} alpha=1 pixels')
   source=cleaned
  validate(source)
  traced=Path(folder)/out.with_suffix('.svg').name
  convert(source,traced)
  if Path(source).resolve()!=out.resolve():shutil.copy2(source,out)
  shutil.copy2(traced,out.with_suffix('.svg'))
 c.execute('UPDATE icons SET status="complete",error="" WHERE id=?',(id,));c.commit();c.close();export()
 if ROOT.resolve()==Path(__file__).resolve().parent/'catalog':
  from tools.build_gallery import build
  build()
def clean_alpha(source,destination):
 from PIL import Image
 with Image.open(source) as image:
  if image.format!='PNG' or image.mode!='RGBA':raise ValueError('Cleanup requires an RGBA PNG')
  alpha=image.getchannel('A');count=alpha.histogram()[1]
  if count:
   image.putalpha(alpha.point(lambda a:0 if a==1 else a))
   image.save(destination)
 return count
def vectorize_batch(batch):
 from vectorize import convert
 rows=[r for r in export() if r['batch']==batch]
 if not rows:raise ValueError('Unknown batch')
 reports=[]
 for r in rows:
  if r['status']!='complete':continue
  source=ROOT/'output'/f'batch-{batch:03d}'/r['filename'];validate(source)
  # This backfill command only creates missing SVGs; completed artwork is preserved.
  if source.with_suffix('.svg').exists():continue
  reports.append(convert(source,source.with_suffix('.svg')))
 report=ROOT/'work'/f'svg-validation-batch-{batch:03d}.json';report.parent.mkdir(exist_ok=True)
 report.write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
 if ROOT.resolve()==BASE/'catalog':
  from tools.build_gallery import build
  build()
 print(report)
def bundle(batch):
 from PIL import Image,ImageDraw
 from vectorize import validate_svg
 from native_svg import validate_pair
 import xml.etree.ElementTree as ET
 rows=[r for r in export() if r['batch']==batch];dest=ROOT/'deliverables';dest.mkdir(exist_ok=True)
 if not rows or any(r['status']!='complete' for r in rows):raise ValueError('Batch incomplete; do not export partial ZIP')
 zp=dest/f'FWS-Icons-Batch-{batch:03d}.zip';tmp=zp.with_suffix('.tmp')
 sheet=Image.new('RGB',(1200,((len(rows)+4)//5)*290),'white');draw=ImageDraw.Draw(sheet)
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
  for n,r in enumerate(rows):
   p=ROOT/'output'/f'batch-{batch:03d}'/r['filename'];validate(p)
   svg=p.with_suffix('.svg')
   if any(e.get('stroke','none')!='none' for e in ET.parse(svg).getroot().iter()):validate_pair(svg,p)
   else:validate_svg(svg,p)
   z.write(p,p.name);z.write(svg,svg.name)
   with Image.open(p) as im:
    im=im.convert('RGBA');im.thumbnail((210,210));x=n%5*240+(240-im.width)//2;y=n//5*290
    sheet.paste(im,(x,y),im)
   import textwrap
   draw.multiline_text((n%5*240+8,n//5*290+220),'\n'.join(textwrap.wrap(r['title'],31)[:4]),fill='#202123')
 with zipfile.ZipFile(tmp) as z:
  if z.testzip():raise ValueError('Corrupt archive')
 tmp.replace(zp);sheet.save(dest/f'FWS-Icons-Batch-{batch:03d}-Preview.jpg');print(zp)
def accept_svg(id,source,size=1024):
 from native_svg import export_png,validate_pair
 c=db();r=c.execute('SELECT * FROM icons WHERE id=?',(id,)).fetchone()
 if not r:raise ValueError('Unknown icon ID')
 if r['status']=='complete':return
 out=ROOT/'output'/f"batch-{r['batch']:03d}"/r['filename'];out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='fws-native-') as folder:
  png=Path(folder)/out.name;svg=png.with_suffix('.svg')
  svg.write_bytes(export_png(source,png,size));validate(png);validate_pair(svg,png)
  shutil.copy2(svg,out.with_suffix('.svg'));shutil.copy2(png,out)
 c.execute('UPDATE icons SET status="complete",error="" WHERE id=?',(id,));c.commit();c.close();export()
 if ROOT.resolve()==Path(__file__).resolve().parent/'catalog':
  from tools.build_gallery import build
  build()
def main():
 global ROOT
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT,help='Queue folder; use catalog for the 4,176-entry master list');s=p.add_subparsers(dest='cmd',required=True)
 for name in ['init','status','next']:s.add_parser(name)
 for name in ['packet','bundle','vectorize']:
  q=s.add_parser(name);q.add_argument('batch',type=int)
 q=s.add_parser('accept');q.add_argument('id',type=int);q.add_argument('source',type=Path)
 q=s.add_parser('accept-svg');q.add_argument('id',type=int);q.add_argument('source',type=Path);q.add_argument('--size',type=int,default=1024)
 q=s.add_parser('attempt');q.add_argument('id',type=int)
 q=s.add_parser('fail');q.add_argument('id',type=int);q.add_argument('reason')
 a=p.parse_args();ROOT=a.root.resolve();init()
 if a.cmd=='status':print(json.dumps(dict(Counter(r['status'] for r in export()))))
 elif a.cmd=='next':
  rows=[r for r in export() if r['status']!='complete' and r['attempts']<3];print(min((r['batch'] for r in rows),default=0))
 elif a.cmd=='packet':print(json.dumps(packet(a.batch),indent=2))
 elif a.cmd=='accept':accept(a.id,a.source)
 elif a.cmd=='accept-svg':accept_svg(a.id,a.source,a.size)
 elif a.cmd=='bundle':bundle(a.batch)
 elif a.cmd=='vectorize':vectorize_batch(a.batch)
 elif a.cmd in ['attempt','fail']:
  c=db()
  if a.cmd=='attempt':
   r=c.execute('SELECT status,attempts FROM icons WHERE id=?',(a.id,)).fetchone()
   if not r or r['status']=='complete' or r['attempts']>=3:raise ValueError('Not eligible for generation')
   c.execute('UPDATE icons SET attempts=attempts+1,status="in_progress" WHERE id=?',(a.id,))
  else:c.execute('UPDATE icons SET status="failed",error=? WHERE id=? AND status!="complete"',(a.reason,a.id))
  c.commit();c.close();export()
if __name__=='__main__':main()
