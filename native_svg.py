"""Validate authored SVG geometry and export a matching transparent PNG (no tracing)."""
import io
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image, ImageChops

NS = 'http://www.w3.org/2000/svg'
PALETTE = {'#202123', '#c31e25'}
GEOMETRY = {'path', 'circle', 'ellipse', 'rect', 'line', 'polyline', 'polygon'}
ATTRS = {'svg': {'viewBox','width','height','version'}, 'g': set(),
         'path': {'d'}, 'circle': {'cx','cy','r'}, 'ellipse': {'cx','cy','rx','ry'},
         'rect': {'x','y','width','height','rx','ry'}, 'line': {'x1','y1','x2','y2'},
         'polyline': {'points'}, 'polygon': {'points'}, 'title': set(), 'desc': set()}
PRESENTATION = {'fill','stroke','stroke-width','stroke-linecap','stroke-linejoin'}


def validate_source(source):
    data = Path(source).read_bytes()
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('SVG entity declarations are not supported')
    root = ET.fromstring(data)
    if root.tag != f'{{{NS}}}svg':
        raise ValueError('Expected a native SVG document')
    try:
        box = [float(x) for x in root.get('viewBox','').replace(',',' ').split()]
        if len(box)!=4 or not all(math.isfinite(x) for x in box) or box[2]<=0 or box[2]!=box[3]:
            raise ValueError()
    except ValueError:
        raise ValueError('SVG requires a square, finite viewBox') from None
    widths = set(); colors = set(); strokes = 0
    def walk(element, inherited):
        nonlocal strokes
        tag = element.tag.removeprefix(f'{{{NS}}}')
        if element.tag != f'{{{NS}}}{tag}' or tag not in ATTRS:
            raise ValueError('Only native vector geometry is allowed; no raster, scripts or external content')
        if set(element.attrib) - ATTRS[tag] - PRESENTATION:
            raise ValueError('Unsupported SVG attribute; use explicit geometry without CSS or transforms')
        state = dict(inherited)
        state.update({k:v for k,v in element.attrib.items() if k in PRESENTATION})
        for key in ['fill','stroke']:
            value = state.get(key,'none').lower()
            if value!='none' and value not in PALETTE:
                raise ValueError('Use only charcoal #202123 and crimson #C31E25')
        if tag in GEOMETRY:
            if list(element):raise ValueError('Geometry cannot contain nested elements')
            for key in ['fill','stroke']:
                if state[key].lower()!='none':colors.add(state[key].lower())
            if state['stroke'].lower()!='none':
                try:width=float(state.get('stroke-width','0'))
                except ValueError:raise ValueError('Stroke width must be a positive number') from None
                if not math.isfinite(width) or width<=0:raise ValueError('Stroke width must be a positive number')
                if state.get('stroke-linecap')!='round' or state.get('stroke-linejoin')!='round':
                    raise ValueError('Native strokes must use round caps and joins')
                widths.add(width);strokes+=1
        for child in element:walk(child,state)
    walk(root,{'fill':'#000000','stroke':'none'})
    if len(widths)!=1 or not strokes:raise ValueError('Use one consistent native stroke width')
    if colors!=PALETTE:raise ValueError('Both palette colors must be visible in the SVG')
    return root


def export_png(source, destination, size=1024):
    if isinstance(size,bool) or not isinstance(size,int) or not 16<=size<=4096:
        raise ValueError('PNG size must be an integer from 16 to 4096')
    root=validate_source(source)
    root.set('width',str(size));root.set('height',str(size))
    data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    cairosvg.svg2png(bytestring=data,write_to=str(destination),output_width=size,output_height=size)
    return data


def validate_pair(svg, png):
    validate_source(svg)
    with Image.open(png) as im:
        source=im.convert('RGBA');size=im.size
    rendered=Image.open(io.BytesIO(cairosvg.svg2png(url=str(svg),output_width=size[0],output_height=size[1]))).convert('RGBA')
    if any(high for low,high in ImageChops.difference(source,rendered).getextrema()):
        raise ValueError('PNG must be exported directly from its SVG without edits')
    return {'source':Path(svg).name,'size':list(size),'workflow':'svg-first'}
