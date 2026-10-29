'use strict';
// Pure SVG transformation plus browser-native PNG rendering. Original files stay untouched.
window.FWSExport = {
  makeSvg(source, options) {
    const size=Number(options.size);
    if(!Number.isInteger(size)||size<16||size>4096)throw Error('Enter a whole-number size between 16 and 4096 px.');
    for(const color of [options.primary,options.accent,...(options.background?[options.background]:[])]) {
      if(!/^#[0-9a-f]{6}$/i.test(color))throw Error('Choose a valid six-digit hex color.');
    }
    const parsed=new DOMParser().parseFromString(source,'image/svg+xml');
    if(parsed.querySelector('parsererror')||parsed.documentElement.localName!=='svg')throw Error('This SVG could not be read.');
    // Recreate SVG nodes without XML prefixes for design-tool import/paste.
    const ns='http://www.w3.org/2000/svg',doc=document.implementation.createDocument(ns,'svg',null),root=doc.documentElement;
    function copySvg(from,to){
      if(from.namespaceURI!==ns)throw Error('Unsupported SVG namespace.');
      for(const attr of from.attributes){
        if(attr.namespaceURI==='http://www.w3.org/2000/xmlns/')continue;
        if(attr.namespaceURI)throw Error('Unsupported SVG attribute namespace.');
        to.setAttribute(attr.localName,attr.value);
      }
      for(const child of from.childNodes){
        if(child.nodeType===Node.ELEMENT_NODE){const element=doc.createElementNS(ns,child.localName);copySvg(child,element);to.appendChild(element);}
        else if(child.nodeType===Node.TEXT_NODE)to.appendChild(doc.createTextNode(child.data));
      }
    }
    copySvg(parsed.documentElement,root);
    const box=(root.getAttribute('viewBox')||'').trim().split(/[\s,]+/).map(Number);
    if(box.length!==4||box.some(n=>!Number.isFinite(n))||box[2]<=0||box[3]<=0)throw Error('This SVG has no valid canvas.');
    root.setAttribute('width',String(size));root.setAttribute('height',String(size));
    for(const attribute of ['fill','stroke'])[root,...root.querySelectorAll('['+attribute+']')].forEach(element=>{
      if(!element.hasAttribute(attribute))return;
      const value=element.getAttribute(attribute).toLowerCase();
      if(value==='#202123')element.setAttribute(attribute,options.primary);
      if(value==='#c31e25')element.setAttribute(attribute,options.accent);
    });
    if(options.background){const rect=doc.createElementNS('http://www.w3.org/2000/svg','rect');
      ['x','y','width','height'].forEach((key,i)=>rect.setAttribute(key,String(box[i])));
      rect.setAttribute('fill',options.background);root.insertBefore(rect,root.firstChild);
    }
    return new XMLSerializer().serializeToString(root);
  },
  pngBlob(source,size){
    return new Promise((resolve,reject)=>{
      const url=URL.createObjectURL(new Blob([source],{type:'image/svg+xml'})),image=new Image();
      image.onload=()=>{try{const canvas=document.createElement('canvas');canvas.width=size;canvas.height=size;
        const context=canvas.getContext('2d');if(!context)throw Error('PNG export is unavailable in this browser.');
        context.drawImage(image,0,0,size,size);
        canvas.toBlob(blob=>{URL.revokeObjectURL(url);blob?resolve(blob):reject(Error('PNG export failed.'));},'image/png');
      }catch(error){URL.revokeObjectURL(url);reject(error);}};
      image.onerror=()=>{URL.revokeObjectURL(url);reject(Error('The SVG could not be rendered.'));};image.src=url;
    });
  }
};
