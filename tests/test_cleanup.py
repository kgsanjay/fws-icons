import importlib.util,tempfile,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('icon_queue',Path(__file__).resolve().parents[1]/'queue.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class CleanupTests(unittest.TestCase):
 def test_only_alpha_one_changes_and_source_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.png';out=Path(d)/'clean.png'
   im=Image.new('RGBA',(5,1));im.putdata([(20,30,40,a) for a in [0,1,2,128,255]]);im.save(p)
   before=p.read_bytes();self.assertEqual(q.clean_alpha(p,out),1)
   self.assertEqual(p.read_bytes(),before)
   self.assertEqual(list(Image.open(out).getdata()),[(20,30,40,a) for a in [0,0,2,128,255]])
