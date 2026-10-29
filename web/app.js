'use strict';
const $=id=>document.getElementById(id), SIZE=48;
let data,available=[],items=[],page=1,category='All icons',current=null,svgSource='',detailToken=0;
const params=new URLSearchParams(location.search);
if(params.get('collection')==='master')$('collection').value='master';
$('search').value=params.get('q')||'';
function node(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;}
function toast(message){$('toast').textContent=message;$('toast').style.display='block';setTimeout(()=>$('toast').style.display='none',2300);}
function sourceItems(){return $('collection').value==='master'?data.master:available;}
function categories(){const names=['All icons',...new Set(sourceItems().map(x=>x.category))];if(!names.includes(category))category='All icons';$('categories').replaceChildren(...names.map(name=>{const b=node('button',name===category?'selected':'',name);b.setAttribute('aria-pressed',String(name===category));b.onclick=()=>{category=name;page=1;categories();render();};return b;}));}
function render(){if(!data)return;const q=$('search').value.trim().toLowerCase(),tokens=q.split(/\s+/).filter(Boolean),status=$('status').value;
items=sourceItems().filter(x=>(category==='All icons'||x.category===category)&&(status==='all'||x.status===status)&&tokens.every(t=>(x.title+' '+x.category).toLowerCase().includes(t)));
const pages=Math.max(1,Math.ceil(items.length/SIZE));page=Math.min(page,pages);const list=items.slice((page-1)*SIZE,page*SIZE);
$('results').textContent=items.length?`${items.length.toLocaleString()} icons · Showing ${(page-1)*SIZE+1}–${Math.min(page*SIZE,items.length)}`:'0 icons match your search';
$('icon-grid').replaceChildren(...list.map(icon=>{const card=node('button','icon-card');card.setAttribute('aria-label',`${icon.title} — ${icon.status==='ready'?'download PNG or SVG':'in the queue'}`);const art=node('div','card-art');if(icon.svg){const im=node('img');im.src=icon.svg;im.alt='';im.loading='lazy';art.append(im,node('span','status-dot'));}else{const placeholder=node('span','pending-art','+');placeholder.setAttribute('aria-hidden','true');art.append(placeholder);}const info=node('div','card-info');info.append(node('span','card-title',icon.title),node('span','card-subtitle '+icon.status,icon.status==='ready'?'SVG + PNG  ↗':'IN THE QUEUE'));card.append(art,info);card.onclick=()=>openDetail(icon);return card;}));
$('empty').hidden=items.length>0;$('previous').disabled=page===1;$('next').disabled=page===pages;$('page-label').textContent=`Page ${page} of ${pages}`;
const u=new URL(location.href);u.searchParams.set('collection',$('collection').value);if(q)u.searchParams.set('q',$('search').value);else u.searchParams.delete('q');history.replaceState(null,'',u);
}
async function openDetail(icon){current=icon;svgSource='';const token=++detailToken;$('detail-title').textContent=icon.title;$('detail-category').textContent=icon.category;$('detail-status').textContent=icon.status==='ready'?'READY TO DOWNLOAD':'IN THE QUEUE';$('detail-status').className='badge '+icon.status;const ready=icon.status==='ready';$('detail-description').textContent=ready?'Custom FWS artwork. Download a transparent PNG or a scalable SVG with editable vector paths.':'This subject is part of the master list. Its artwork has not been generated yet.';
for(const id of ['detail-downloads','format-switch','code-area'])$(id).hidden=!ready;
$('detail-preview').replaceChildren();$('svg-code').textContent='Loading SVG source…';$('copy-code').disabled=true;
if(ready){preview('svg');for(const format of ['svg','png']){const a=$('download-'+format);a.href=icon[format];a.download=icon[format].split('/').pop();}}else $('detail-preview').append(node('span','', 'Artwork coming soon'));
if(!$('detail').open)$('detail').showModal();
if(ready){try{const r=await fetch(icon.svg);if(!r.ok)throw Error();const text=await r.text();if(token!==detailToken)return;svgSource=text;$('svg-code').textContent=text;$('copy-code').disabled=false;}catch{if(token===detailToken)$('svg-code').textContent='Source could not be loaded. Try downloading the SVG.';}}
}
function preview(format){const im=node('img');im.src=current[format];im.alt=current.title;$('detail-preview').replaceChildren(im);document.querySelectorAll('[data-format]').forEach(b=>b.classList.toggle('selected',b.dataset.format===format));}
$('close-detail').onclick=()=>$('detail').close();$('detail').addEventListener('click',e=>{if(e.target===$('detail')){const r=$('detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('detail').close();}});
document.querySelectorAll('[data-format]').forEach(b=>b.onclick=()=>preview(b.dataset.format));
$('copy-code').onclick=async()=>{try{await navigator.clipboard.writeText(svgSource);toast('SVG source copied');}catch{toast('Copy unavailable. Select the SVG source or download the file.');}};
$('search').oninput=()=>{page=1;render();};$('collection').onchange=()=>{page=1;category='All icons';$('status').value='all';categories();render();};$('status').onchange=()=>{page=1;render();};$('background').onchange=()=>{$('icon-grid').className='icon-grid '+$('background').value;};
$('previous').onclick=()=>{page--;render();$('library').scrollIntoView();};$('next').onclick=()=>{page++;render();$('library').scrollIntoView();};$('reset').onclick=()=>{$('search').value='';$('status').value='all';category='All icons';page=1;categories();render();};
document.addEventListener('keydown',e=>{if(e.key==='/'&&!$('detail').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}});
(async()=>{try{const r=await fetch('web/catalog.json');if(!r.ok)throw Error();data=await r.json();const seen=new Set();available=[...data.master,...data.legacy].filter(x=>{const key=x.title.toLowerCase().trim();if(x.status!=='ready'||seen.has(key))return false;seen.add(key);return true;});const done=data.master.filter(x=>x.status==='ready').length;$('available-count').textContent=available.length.toLocaleString();$('master-count').textContent=data.master.length.toLocaleString();$('progress-note').textContent=`${done.toLocaleString()} of ${data.master.length.toLocaleString()} master subjects ready.`;
const samples=[...data.legacy.slice(0,5),...data.master.filter(x=>x.status==='ready')].slice(0,6);$('hero-icons').replaceChildren(...samples.map(x=>{const tile=node('div','hero-tile'),im=node('img');im.src=x.svg;im.alt=x.title;tile.append(im);return tile;}));categories();render();}catch(e){$('error').hidden=false;$('results').textContent='Collection unavailable';$('previous').disabled=true;$('next').disabled=true;}})();
