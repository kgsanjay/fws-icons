import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cairosvg
from PIL import Image, ImageDraw
from vectorize import convert, validate_svg

spec = importlib.util.spec_from_file_location('icon_queue', Path(__file__).resolve().parents[1]/'queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class VectorDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.png = self.root/'source.png'
        image = Image.new('RGBA', (256, 256))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((45, 45, 210, 210), radius=20, outline='#202123', width=10)
        draw.ellipse((100, 100, 155, 155), outline='#C31E25', width=8)
        image.save(self.png)
        self.svg = self.root/'source.svg'

    def test_trace_preserves_holes_and_is_repeatable(self):
        report = convert(self.png, self.svg)
        original = self.svg.read_bytes()
        self.assertGreaterEqual(min(report['layer_iou'].values()), .95)
        rendered = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=original))).convert('RGBA')
        self.assertEqual(rendered.getpixel((128, 128))[3], 0)
        self.assertEqual(rendered.getpixel((0, 0))[3], 0)
        convert(self.png, self.svg)
        self.assertEqual(original, self.svg.read_bytes())

    def test_rejects_embedded_raster_and_wrong_geometry(self):
        convert(self.png, self.svg)
        original = self.svg.read_text()
        self.svg.write_text(original.replace('</svg>', '<image href="remote.png"/></svg>'))
        with self.assertRaises(ValueError):
            validate_svg(self.svg, self.png)
        self.svg.write_text(original)
        Image.new('RGBA', (256, 256)).save(self.png)
        with self.assertRaises(ValueError):
            validate_svg(self.svg, self.png)

    def test_accept_failure_does_not_complete_and_bundle_requires_pair(self):
        with patch.object(queue, 'ROOT', self.root):
            (self.root/'services.txt').write_text('Example Service\n')
            queue.init()
            with patch('vectorize.convert', side_effect=ValueError('trace failed')):
                with self.assertRaisesRegex(ValueError, 'trace failed'):
                    queue.accept(1, self.png)
            self.assertEqual(queue.export()[0]['status'], 'pending')
            queue.accept(1, self.png)
            row = queue.export()[0]
            self.assertEqual(row['status'], 'complete')
            self.assertEqual(row['attempts'], 0)  # conversion never consumes generation attempts
            output = self.root/'output/batch-001/Example-Service.svg'
            self.assertTrue(output.exists())
            queue.bundle(1)
            import zipfile
            with zipfile.ZipFile(self.root/'deliverables/FWS-Icons-Batch-001.zip') as z:
                self.assertEqual(set(z.namelist()), {'Example-Service.png', 'Example-Service.svg'})
            output.unlink()
            with self.assertRaises(FileNotFoundError):
                queue.bundle(1)


if __name__ == '__main__':
    unittest.main()
