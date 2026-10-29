"""Create the new master queue without changing the legacy queue or artwork."""
import argparse,importlib.util,json,re,shutil,sqlite3,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('icons_queue',BASE/'queue.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
def normalized(title):return re.sub(r'\s+',' ',title).strip().casefold()
def import_catalog(source,destination):
 destination=Path(destination)
 if destination.exists() and any(destination.iterdir()):raise ValueError('Destination must be empty; refusing to overwrite progress')
 lines=[x.strip().removeprefix('[').removesuffix(']').strip() for x in Path(source).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
 if not lines or len({normalized(t) for t in lines})!=len(lines):raise ValueError('Empty or duplicate titles')
 destination.mkdir(parents=True,exist_ok=True);(destination/'services.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 shutil.copy2(source,destination/'original-icon-names.txt')
 old=sqlite3.connect(f'file:{BASE}/progress.sqlite?mode=ro',uri=True);old.row_factory=sqlite3.Row
 completed={normalized(r['title']):dict(r) for r in old.execute('select * from icons where status="complete"')};old.close()
 q.ROOT=destination;q.init();reused=[]
 from vectorize import validate_svg
 for row in q.export():
  previous=completed.get(normalized(row['title']))
  if not previous:continue
  source_png=BASE/'output'/f"batch-{previous['batch']:03d}"/previous['filename'];q.validate(source_png);validate_svg(source_png.with_suffix('.svg'),source_png)
  output=destination/'output'/f"batch-{row['batch']:03d}"/row['filename'];output.parent.mkdir(parents=True,exist_ok=True)
  for suffix in ['.png','.svg']:shutil.copy2(source_png.with_suffix(suffix),output.with_suffix(suffix))
  with q.db() as c:c.execute('update icons set status="complete" where id=?',(row['id'],))
  reused.append({'id':row['id'],'title':row['title'],'legacy_id':previous['id']})
 q.export();(destination/'migration.json').write_text(json.dumps({'total':len(lines),'reused':reused,'legacy_queue':'../progress.sqlite'},indent=2)+'\n')
 print(json.dumps({'total':len(lines),'reused':len(reused),'pending':len(lines)-len(reused)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--destination',type=Path,default=BASE/'catalog');a=p.parse_args();import_catalog(a.source,a.destination.resolve())
