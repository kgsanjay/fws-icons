"""Trace generated PNG artwork into two-color SVG paths and check raster fidelity."""
import io
import json
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

NS = 'http://www.w3.org/2000/svg'
PALETTE = ('#202123', '#C31E25')
ET.register_namespace('', NS)


def masks(image):
    """Ignore transparent RGB and antialiasing noise; classify the visible artwork."""
    image = image.convert('RGBA')
    dark, red = bytearray(), bytearray()
    for r, g, b, a in image.getdata():
        visible = a >= 128
        accent = r > 90 and r > g * 1.6 and r > b * 1.6
        dark.append(255 if visible and not accent else 0)
        red.append(255 if visible and accent else 0)
    return tuple(Image.frombytes('L', image.size, bytes(data)) for data in (dark, red))


def validate_svg(svg_path, png_path):
    """Allow only local path geometry, then compare each rendered color layer."""
    import cairosvg
    data = Path(svg_path).read_bytes()
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('SVG declarations are not permitted')
    root = ET.fromstring(data)
    with Image.open(png_path) as source:
        size = source.size
        source_masks = masks(source)
    if root.tag != f'{{{NS}}}svg' or root.get('viewBox') != f'0 0 {size[0]} {size[1]}':
        raise ValueError('SVG canvas must match the source PNG')
    if set(root.attrib) - {'width', 'height', 'viewBox', 'version'}:
        raise ValueError('Unexpected SVG root attributes')
    colors = set()
    for node in root.iter():
        if node is root:
            continue
        if node.tag != f'{{{NS}}}path' or list(node):
            raise ValueError('SVG must contain paths only; no raster images or active content')
        if set(node.attrib) - {'d', 'fill', 'transform', 'fill-rule'}:
            raise ValueError('Unexpected SVG path attributes')
        if not node.get('d', '').strip() or node.get('fill') not in PALETTE:
            raise ValueError('SVG paths require geometry and exact palette colors')
        colors.add(node.get('fill'))
    if colors != set(PALETTE):
        raise ValueError('SVG must include both palette colors')
    rendered = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data,
                           output_width=size[0], output_height=size[1]))).convert('RGBA')
    alpha = rendered.getchannel('A')
    box = alpha.getbbox()
    if alpha.getextrema() != (0, 255) or not box or min(box[0], box[1], size[0]-box[2], size[1]-box[3]) < size[0]*.03:
        raise ValueError('SVG must preserve transparent margins and visible artwork')
    scores = {}
    for color, original, result in zip(PALETTE, source_masks, masks(rendered)):
        intersection = sum(ImageChops.darker(original, result).getdata())
        union = sum(ImageChops.lighter(original, result).getdata())
        score = intersection / union if union else 0
        if score < .95:
            raise ValueError(f'SVG differs from source {color} layer: IoU {score:.4f} < 0.95')
        scores[color] = round(score, 6)
    return {'source': Path(png_path).name, 'svg': Path(svg_path).name,
            'size': list(size), 'layer_iou': scores}


def convert(png_path, svg_path, _mode="spline"):
    """Trace each binary color mask with VTracer; publish only validated output."""
    import vtracer
    png_path, svg_path = Path(png_path), Path(svg_path)
    with Image.open(png_path) as source:
        size = source.size
        layers = masks(source)
    root = ET.Element(f'{{{NS}}}svg', width=str(size[0]), height=str(size[1]),
                      viewBox=f'0 0 {size[0]} {size[1]}', version='1.1')
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fws-trace-') as folder:
        folder = Path(folder)
        for color, mask in zip(PALETTE, layers):
            raster, traced = folder/'mask.png', folder/'mask.svg'
            ImageChops.invert(mask).convert('RGB').save(raster)
            vtracer.convert_image_to_svg_py(str(raster), str(traced), colormode='binary',
                mode=_mode, filter_speckle=4, corner_threshold=60,
                length_threshold=4.0, splice_threshold=45, path_precision=3)
            for path in ET.parse(traced).getroot():
                if path.tag == f'{{{NS}}}path' and path.get('d', '').strip():
                    path.set('fill', color)
                    root.append(path)
        candidate = folder/'candidate.svg'
        ET.ElementTree(root).write(candidate, encoding='utf-8', xml_declaration=True)
        try:
            report = validate_svg(candidate, png_path)
        except ValueError:
            if _mode == 'spline':
                return convert(png_path, svg_path, _mode='none')
            raise
        # Same-directory temporary file makes replacement atomic.
        with tempfile.NamedTemporaryFile(dir=svg_path.parent, suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(candidate.read_bytes())
        try:
            temporary.replace(svg_path)
        finally:
            temporary.unlink(missing_ok=True)
    report['svg'] = svg_path.name
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('png', type=Path)
    parser.add_argument('svg', type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.png, args.svg), indent=2))
