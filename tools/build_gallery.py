"""Build the static gallery index from saved queue state, never from prompts."""
import json,sqlite3
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def category(title):
 t=title.lower()
 for label,words in [('Technology',('software','development','data','cloud','cyber','xml','ai ','machine','app ',' .net','network','digital','it ')),('Finance',('account','billing','tax','bank','insurance','financial','mortgage','bookkeeping','payroll','loan')),('Design & media',('design','image','photo','video','animation','creative','publishing','visual')),('Customer support',('call','support','customer','contact','answering','receptionist')),('Marketing',('marketing','lead','sales','seo','advertising','campaign')),('Healthcare',('health','medical','clinical','patient','dental','pediatric'))]:
  if any(w in ' '+t for w in words):return label
 return 'Business services'
def collection(root,name,ready_only=False):
 c=sqlite3.connect(f'file:{root}/progress.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row;items=[]
 for r in c.execute('select * from icons order by id'):
  if ready_only and r['status']!='complete':continue
  path=root/'output'/f"batch-{r['batch']:03d}"/r['filename'];ready=r['status']=='complete' and path.is_file() and path.with_suffix('.svg').is_file()
  items.append({'id':f"{name}-{r['id']}",'number':r['id'],'title':r['title'],'category':category(r['title']),'status':'ready' if ready else 'pending','png':path.relative_to(BASE).as_posix() if ready else None,'svg':path.with_suffix('.svg').relative_to(BASE).as_posix() if ready else None})
 c.close();return items
def build():
 data={'master':collection(BASE/'catalog','master'),'legacy':collection(BASE,'legacy',True)}
 target=BASE/'web/catalog.json';temporary=target.with_suffix('.json.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');temporary.replace(target);print(f'Gallery: {len(data["master"])} master entries, {sum(x["status"]=="ready" for x in data["master"])} ready, {len(data["legacy"])} previous icons')
 return data
if __name__=='__main__':build()
