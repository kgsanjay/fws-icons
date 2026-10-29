from playwright.sync_api import sync_playwright
from pathlib import Path
import json
data=json.loads((Path(__file__).resolve().parents[1]/'web/catalog.json').read_text())
ready=len({x['title'].casefold() for x in data['master']+data['legacy'] if x['status']=='ready'})
master_ready=sum(x['status']=='ready' for x in data['master'])
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8080');page.wait_for_selector('.icon-card')
 assert page.locator('.icon-card').count()==min(48,ready)
 assert f'{ready} icons' in page.locator('#results').inner_text()
 page.locator('#search').fill(next(x['title'] for x in data['master'] if x['status']=='ready'));assert page.locator('.icon-card').count()>0
 page.locator('.icon-card').first.click();page.wait_for_function("!document.getElementById('customize').disabled")
 assert page.locator('#download-svg').get_attribute('href').startswith('blob:')
 assert page.locator('#original-svg').get_attribute('href').split('?')[0].endswith('.svg')
 page.locator('[data-format="png"]').click();page.wait_for_function("document.querySelector('#detail-preview img').src.startsWith('blob:')")
 with page.expect_download() as d:page.locator('#download-svg').click()
 assert d.value.suggested_filename.endswith('.svg')
 page.keyboard.press('Escape');assert not page.locator('#detail').evaluate('(e)=>e.open')
 page.locator('#search').fill('zzzz-no-results');assert page.locator('#empty').is_visible()
 page.locator('#reset').click();page.locator('#collection').select_option('master')
 assert '4,176 icons' in page.locator('#results').inner_text()
 page.locator('#status').select_option('ready');assert page.locator('.icon-card').count()==min(48,master_ready)
 page.locator('#status').select_option('pending');page.locator('.icon-card').first.click()
 assert page.locator('#detail-downloads').is_hidden();page.keyboard.press('Escape')
 page.locator('#collection').select_option('available')
 if ready>48:
  page.locator('#next').click();assert 'Page 2' in page.locator('#page-label').inner_text()
 else:assert page.locator('#next').is_disabled()
 page.get_by_role('button',name='Customer support',exact=True).click();assert page.get_by_role('button',name='Customer support',exact=True).get_attribute('aria-pressed')=='true'
 page.get_by_role('button',name='All icons',exact=True).click()
 page.locator('#background').select_option('checker');assert 'checker' in page.locator('#icon-grid').get_attribute('class')
 page.locator('#background').select_option('light')
 page.screenshot(path=str(Path(__file__).resolve().parents[1]/'work/gallery-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(Path(__file__).resolve().parents[1]/'work/gallery-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 browser.close();print('PASS: search, empty state, 4176-entry master, ready/pending filters, modal, preview switching, SVG download, Escape, mobile width; no JS errors')
