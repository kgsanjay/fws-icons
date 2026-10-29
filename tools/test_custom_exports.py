"""Browser checks for actual customized SVG/PNG exports; run with gallery on :8080."""
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory() as folder, sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1100},permissions=['clipboard-read','clipboard-write'])
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8080');page.wait_for_selector('.icon-card');page.locator('.icon-card').first.click()
 page.wait_for_function("!document.getElementById('customize').disabled")
 # Native strokes (including inherited paint on the SVG root) must recolor too.
 native='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" fill="none" stroke="#202123" stroke-width="2.5"><circle cx="50" cy="50" r="20"/><path d="M20 80H100" stroke="#C31E25"/></svg>'
 transformed=page.evaluate("source=>FWSExport.makeSvg(source,{size:256,primary:'#0066ff',accent:'#00aa66',background:null})",native)
 assert transformed.startswith('<svg ') and 'ns0:' not in transformed
 prefixed=native.replace('<svg ','<ns0:svg ').replace('</svg>','</ns0:svg>').replace('xmlns=','xmlns:ns0=').replace('<circle ','<ns0:circle ').replace('<path ','<ns0:path ')
 normalized=page.evaluate("source=>FWSExport.makeSvg(source,{size:256,primary:'#0066ff',accent:'#00aa66',background:null})",prefixed)
 assert normalized.startswith('<svg ') and 'ns0:' not in normalized
 tree=ET.fromstring(transformed)
 assert tree.get('stroke')=='#0066ff' and tree.find('{http://www.w3.org/2000/svg}path').get('stroke')=='#00aa66'
 assert tree.get('viewBox')=='0 0 128 128' and tree.get('width')=='256'
 original=page.locator('#original-svg').get_attribute('href');original_text=page.request.get('http://127.0.0.1:8080/'+original).text()
 page.locator('#export-size').fill('128')
 for id,value in [('primary-color','#0066ff'),('accent-color','#00aa66'),('background-color','#fceedd')]:
  page.locator('#'+id).evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}));}',value)
 page.locator('#export-background').select_option('solid')
 with page.expect_download() as download:page.locator('#download-svg').click()
 svg=Path(folder)/'custom.svg';download.value.save_as(svg);root=ET.parse(svg).getroot()
 assert svg.read_text().startswith('<svg ') and 'ns0:' not in svg.read_text()
 assert root.get('width')=='128' and root.get('height')=='128'
 assert root.get('viewBox')==ET.fromstring(original_text).get('viewBox')
 ns={'s':'http://www.w3.org/2000/svg'}
 assert root.find('s:rect',ns).get('fill')=='#fceedd'
 assert {e.get(a) for e in root.iter() for a in ['stroke','fill'] if e.get(a) not in (None,'none')}=={'#0066ff','#00aa66','#fceedd'}
 assert len(root.findall('.//s:path',ns))==len(ET.fromstring(original_text).findall('.//s:path',ns))
 with page.expect_download() as download:page.locator('#download-png').click()
 png=Path(folder)/'custom.png';download.value.save_as(png)
 with Image.open(png) as im:
  assert im.size==(128,128);assert im.convert('RGBA').getpixel((0,0))==(252,238,221,255)
  colors=set(im.convert('RGB').getdata());assert (0,102,255) in colors and (0,170,102) in colors
 page.locator('#copy-code').click();copied=page.evaluate('navigator.clipboard.readText()');assert 'width="128"' in copied and copied.startswith('<svg ') and 'ns0:' not in copied
 page.locator('#export-background').select_option('transparent')
 with page.expect_download() as download:page.locator('#download-png').click()
 download.value.save_as(png)
 with Image.open(png) as im:assert im.getchannel('A').getextrema()==(0,255) and im.getpixel((0,0))[3]==0
 page.locator('[data-format="png"]').click()
 page.wait_for_function("document.querySelector('#detail-preview img').src.startsWith('blob:')")
 page.wait_for_function("document.querySelector('#detail-preview img').complete")
 page.locator('#export-size').fill('4096');assert page.locator('#export-error').is_hidden()
 for size in ['0','4097','32.5','']:
  page.locator('#export-size').fill(size);assert page.locator('#export-error').is_visible()
  assert page.locator('#download-svg').get_attribute('aria-disabled')=='true';assert page.locator('#copy-code').is_disabled()
 page.locator('#reset-export').click();assert page.locator('#export-size').input_value()=='512'
 assert page.locator('#primary-color').input_value()=='#202123'
 assert page.locator('#export-background').input_value()=='transparent'
 assert page.locator('#download-png').get_attribute('aria-disabled')=='false'
 # Rectangular exports keep the artwork's proportions and fill all background corners.
 page.locator('#lock-ratio').uncheck()
 page.locator('#export-size').fill('320');page.locator('#export-height').fill('180')
 assert page.locator('#export-dimensions').inner_text()=='320 × 180 px'
 page.locator('#artwork-style').select_option('mono')
 assert page.locator('#accent-color').is_disabled()
 page.locator('#export-padding').fill('12');assert page.locator('#padding-value').inner_text()=='12%'
 page.locator('#export-background').select_option('solid')
 page.locator('#background-color').evaluate('(e)=>{e.value="#fceedd";e.dispatchEvent(new Event("input",{bubbles:true}));}')
 with page.expect_download() as download:page.locator('#download-svg').click()
 download.value.save_as(svg);rectangular=ET.parse(svg).getroot()
 assert (rectangular.get('width'),rectangular.get('height'))==('320','180')
 assert rectangular.get('preserveAspectRatio')=='xMidYMid meet'
 assert rectangular.get('viewBox')!=ET.fromstring(original_text).get('viewBox')
 assert '#c31e25' not in svg.read_text().lower()
 with page.expect_download() as download:page.locator('#download-png').click()
 assert '320x180' in download.value.suggested_filename
 download.value.save_as(png)
 with Image.open(png) as im:
  assert im.size==(320,180)
  assert all(im.convert('RGBA').getpixel(point)==(252,238,221,255) for point in [(0,0),(319,0),(0,179),(319,179)])
 for surface in ['dark','light','checker']:
  page.locator('[data-surface="'+surface+'"]').click()
  assert page.locator('#detail-preview').get_attribute('data-surface')==surface
 assert page.locator('#export-background').input_value()=='solid'  # canvas choice is independent
 page.locator('#export-height').fill('4097');assert page.locator('#export-error').is_visible()
 page.locator('#reset-export').click()
 assert page.locator('#lock-ratio').is_checked() and page.locator('#export-height').is_disabled()
 assert page.locator('#artwork-style').input_value()=='original' and page.locator('#export-padding').input_value()=='0'
 assert not page.locator('#source-disclosure').evaluate('(e)=>e.open')
 page.locator('[data-size="48"]').click();assert page.locator('#export-size').input_value()=='48'
 page.locator('[data-format="svg"]').click()
 page.screenshot(path='/workspace/fws-icons/work/gallery-customizer-desktop.png',full_page=False)
 page.set_viewport_size({'width':390,'height':844})
 assert page.locator('#detail').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 page.screenshot(path='/workspace/fws-icons/work/gallery-customizer-mobile.png',full_page=False)
 assert page.request.get('http://127.0.0.1:8080/'+original).text()==original_text
 page.keyboard.press('Escape');page.locator('.icon-card').nth(1).click()
 page.wait_for_function("!document.getElementById('customize').disabled")
 assert page.locator('#export-size').input_value()=='512'
 page.keyboard.press('Escape');page.locator('#collection').select_option('master');page.locator('#status').select_option('pending');page.locator('.icon-card').first.click()
 assert page.locator('#customize').is_hidden() and page.locator('#original-downloads').is_hidden()
 assert not errors,errors
 browser.close()
 print('PASS: square/rectangular SVG/PNG downloads, proportional fit, padding, single color, solid corners/alpha, canvas surfaces, copied SVG, input limits, reset, presets, icon switching, pending state, mobile fit; originals unchanged')
