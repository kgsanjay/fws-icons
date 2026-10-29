"""Publish only the explicitly requested 20-icon reference-style revision."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,sqlite3,tarfile,tempfile
BASE=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(BASE))
from native_svg import export_png,validate_pair
spec=importlib.util.spec_from_file_location('icons_queue',BASE/'queue.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
def publish():
 folder=BASE/'catalog/work/reference-revision';metadata=json.loads((folder/'revision.json').read_text())
 if not metadata.get('user_authorized_revision') or metadata['scope']!=list(range(11,31)):raise ValueError('This tool is limited to the authorized revision of IDs 11–30')
 if (folder/'published.json').exists():raise ValueError('Revision already published; refusing to increment revision attempts again')
 c=sqlite3.connect(BASE/'catalog/progress.sqlite');c.row_factory=sqlite3.Row
 rows=c.execute('select * from icons where status="complete" order by id').fetchall()
 if [r['id'] for r in rows]!=metadata['scope']:raise ValueError('Completed collection changed; recheck scope before publishing')
 with tarfile.open(metadata['backup']) as archive:
  for r in rows:
   for suffix in ['.png','.svg']:
    path=BASE/'catalog/output'/f"batch-{r['batch']:03d}"/Path(r['filename']).with_suffix(suffix)
    old=archive.extractfile(path.relative_to(BASE).as_posix()).read()
    if hashlib.sha256(old).digest()!=hashlib.sha256(path.read_bytes()).digest():raise ValueError('Original files changed since recovery backup')
 report=[]
 with tempfile.TemporaryDirectory(prefix='fws-reviewed-revision-') as tmp:
  tmp=Path(tmp)
  # Validate the entire group before touching any production artifact.
  for r in rows:
   png=tmp/r['filename'];svg=png.with_suffix('.svg');source=folder/f"{r['id']:04d}.svg"
   svg.write_bytes(export_png(source,png,1024));q.validate(png);validate_pair(svg,png)
   report.append({'id':r['id'],'title':r['title'],'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
  for r in rows:
   output=BASE/'catalog/output'/f"batch-{r['batch']:03d}"/r['filename']
   for suffix in ['.svg','.png']:
    target=output.with_suffix(suffix);temporary=target.with_suffix(suffix+'.tmp');shutil.copy2((tmp/r['filename']).with_suffix(suffix),temporary);temporary.replace(target)
   author=BASE/'catalog/work'/f"batch-{r['batch']:03d}"/f"{r['id']:04d}.svg";shutil.copy2(folder/f"{r['id']:04d}.svg",author)
  c.executemany('update icons set attempts=attempts+1 where id=?',[(r['id'],) for r in rows]);c.commit()
 c.close();q.ROOT=BASE/'catalog';q.export()
 (folder/'published.json').write_text(json.dumps({'scope':metadata['scope'],'basis':'User requested matching archived reference style; approved publishing 20 revised icons for live review','files':report},indent=2)+'\n')
 for batch in [2,3]:q.bundle(batch)
 from tools.build_gallery import build
 build();print('Published and validated 20 revised native SVG/PNG pairs; statuses preserved')
if __name__=='__main__':publish()
