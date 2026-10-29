import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from native_svg import export_png, validate_source, validate_pair

spec=importlib.util.spec_from_file_location('native_queue',Path(__file__).resolve().parents[1]/'queue.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
SOURCE='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" fill="none"><g stroke="#202123" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="25" y="25" width="78" height="78" rx="8"/><circle cx="64" cy="64" r="18" stroke="#C31E25"/></g></svg>'''
class NativeSvgTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.svg=self.root/'source.svg';self.svg.write_text(SOURCE)
 def test_native_pair_and_unchanged_source(self):
  png=self.root/'rendered.png';original=self.svg.read_bytes()
  normalized=export_png(self.svg,png,256);svg=self.root/'normalized.svg';svg.write_bytes(normalized)
  validate_pair(svg,png);self.assertEqual(original,self.svg.read_bytes())
  with Image.open(png) as im:self.assertEqual(im.size,(256,256));self.assertEqual(im.getpixel((0,0))[3],0)
  with Image.open(png) as im:
   im.putpixel((128,128),(255,0,0,255));im.save(png)
  with self.assertRaisesRegex(ValueError,'directly'):validate_pair(svg,png)
 def test_rejects_inconsistent_strokes_and_external_content(self):
  for invalid in [SOURCE.replace('r="18"','r="18" stroke-width="4"'),SOURCE.replace('</svg>','<image href="https://example.com/test.png"/></svg>'),SOURCE.replace('round','miter'),SOURCE.replace('#C31E25','#ffffff')]:
   self.svg.write_text(invalid)
   with self.assertRaises(ValueError):validate_source(self.svg)
 def test_queue_completes_only_valid_pairs_and_bundles_native(self):
  with patch.object(q,'ROOT',self.root):
   (self.root/'services.txt').write_text('Example service\n');q.init()
   self.svg.write_text(SOURCE.replace('round','miter'))
   with self.assertRaises(ValueError):q.accept_svg(1,self.svg)
   self.assertEqual(q.export()[0]['status'],'pending')
   self.svg.write_text(SOURCE);q.accept_svg(1,self.svg,256);self.assertEqual(q.export()[0]['status'],'complete')
   before=(self.root/'output/batch-001/Example-service.png').read_bytes()
   q.accept_svg(1,self.root/'nonexistent.svg');self.assertEqual(before,(self.root/'output/batch-001/Example-service.png').read_bytes())
   q.bundle(1)
   import zipfile
   with zipfile.ZipFile(self.root/'deliverables/FWS-Icons-Batch-001.zip') as z:self.assertEqual(len(z.namelist()),2)
