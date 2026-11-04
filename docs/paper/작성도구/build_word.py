"""Build the Korean draft from the retained ICIoTC template, then render in Word.
Requires lxml, Pillow, pywin32 and PyMuPDF on Windows with Microsoft Word.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import hashlib, json
from lxml import etree as E
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'템플릿'/'ICIot_Template.docx'
OUTPUT=ROOT/'스마트팜_논문_통합초안.docx'
QA=ROOT/'검수'
QA.mkdir(exist_ok=True)
content=json.loads((ROOT/'원고'/'원고.json').read_text(encoding='utf-8'))
d=content['draft']; parts=content['methods']
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R}
def q(n):return '{'+W+'}'+n
def el(n,**attrs):return E.Element(q(n),{q(k):str(v) for k,v in attrs.items()})
with ZipFile(TEMPLATE) as z: files={i.filename:z.read(i.filename) for i in z.infolist()}
doc=E.fromstring(files['word/document.xml']); body=doc.find('w:body',NS)
sect_model=deepcopy(doc.xpath('//w:sectPr',namespaces=NS)[0])
body.clear()

def run(text,size=10,bold=False,italic=False):
    r=el('r');rp=el('rPr');rp.append(el('rFonts',ascii='Times New Roman',hAnsi='Times New Roman',eastAsia='바탕',cs='Times New Roman'))
    if bold:rp.append(el('b'))
    if italic:rp.append(el('i'))
    rp.append(el('color',val='000000'));rp.append(el('sz',val=int(size*2)));rp.append(el('szCs',val=int(size*2)))
    r.append(rp)
    for i,line in enumerate(text.split('\n')):
        if i:r.append(el('br'))
        t=el('t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=line;r.append(t)
    return r
def para(text='',size=10,bold=False,italic=False,align='both',indent=True,before=0,after=0,keep=False,style=None):
    p=el('p');pp=el('pPr')
    if style:pp.append(el('pStyle',val=style))
    if keep:pp.append(el('keepNext'))
    pp.append(el('widowControl'));pp.append(el('snapToGrid',val=0))
    pp.append(el('spacing',before=before,after=after,line=240,lineRule='auto'))
    pp.append(el('ind',firstLine=244 if indent else 0));pp.append(el('jc',val=align))
    p.append(pp);p.append(run(text,size,bold,italic));return p
def add(text='',**kw):p=para(text,**kw);body.append(p);return p
def heading(text,level=1):return add(text,size=12 if level==1 else 10,bold=True,indent=False,align='left',before=180 if level==1 else 120,after=70,keep=True)
def section(cols=2,kind='continuous'):
    s=deepcopy(sect_model)
    for c in list(s):
        if E.QName(c).localname not in ['pgSz','pgMar']:s.remove(c)
    s.insert(0,el('type',val=kind));s.append(el('cols',num=cols,space=720));return s
def endsection(cols=2,kind='continuous'):
    p=para('',size=1,indent=False,align='left');p.find('w:pPr',NS).append(section(cols,kind));body.append(p)
def pagebreak():
    p=para('',size=1,indent=False);p.find('w:r',NS).append(el('br',type='page'));body.append(p)

# One full-width title block, as in the supplied template.
title=d['title'].split('\n')[0]
add(title,size=13,bold=True,align='center',indent=False,after=140,style='Title')
add('¹HyoungSuk Park',size=11,italic=True,align='center',indent=False,after=120)
add('*¹ First Author / Corresponding Author,\nDepartment of Computer Information, VISION COLLEGE OF JEONJU,\nRepublic of Korea, youqlrqod@gmail.com',size=10,italic=True,align='center',indent=False,after=180)
endsection(1)
heading('Abstract',1)
add(d['abstract'],italic=True)
add('Keywords: '+d['keywords'],italic=True,indent=False,before=120,after=140)
heading('1. 서론')
for p in d['intro'].split('\n\n'):add(p)
heading('2. 재료 및 방법')
heading(parts[0]['title'],2)
for p in parts[0]['paragraphs']:add(p)
endsection(2)

rels=E.fromstring(files['word/_rels/document.xml.rels'])
relNS='http://schemas.openxmlformats.org/package/2006/relationships'
ct=E.fromstring(files['[Content_Types].xml'])
ctNS='http://schemas.openxmlformats.org/package/2006/content-types'
if not ct.xpath('*[@Extension="png"]'):
    E.SubElement(ct,'{'+ctNS+'}Default',Extension='png',ContentType='image/png')
def picture(name,caption,index,width_mm=159.2):
    img=ROOT/'절별자료'/(name+'.png');w,h=Image.open(img).size
    # Captions are already included at the bottom of the supplied diagrams.
    cx=int(width_mm*36000);cy=int(cx*h/w)
    relid='rIdPaperImage'+str(index)
    E.SubElement(rels,'{'+relNS+'}Relationship',Id=relid,Type=R+'/image',Target='media/paper'+str(index)+'.png')
    files['word/media/paper'+str(index)+'.png']=img.read_bytes()
    p=para('',indent=False,align='center',after=90)
    r=p.find('w:r',NS)
    drawing=E.fromstring(f'''<w:drawing xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{100+index}" name="그림 {index}" descr="{caption}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{index}" name="{name}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{relid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>''')
    r.append(drawing);body.append(p)
picture(parts[0]['figure'],content['captions'][0],1)
endsection(1)
heading(parts[1]['title'],2)
for p in parts[1]['paragraphs']:add(p)
endsection(2)
picture(parts[1]['figure'],content['captions'][1],2)
endsection(1)
heading(parts[2]['title'],2)
add(parts[2]['paragraphs'][0])
for m in parts[2]['modules']:
    heading(m['title'],2);add(m['text'])
heading(parts[3]['title'],2)
for p in parts[3]['paragraphs']:add(p)
endsection(2)

add('표 1. 시스템 개발 환경',indent=False,before=120,after=90,keep=True)
table=el('tbl');props=el('tblPr');props.append(el('tblW',w=9026,type='dxa'));props.append(el('tblLayout',type='fixed'))
borders=el('tblBorders')
for n in ['top','left','bottom','right','insideH','insideV']:borders.append(el(n,val='single',sz=4,color='B9B9B9'))
props.append(borders);marg=el('tblCellMar')
for n,v in [('top',70),('left',85),('bottom',70),('right',85)]:marg.append(el(n,w=v,type='dxa'))
props.append(marg);table.append(props)
widths=[1080,1150,3540,3256];grid=el('tblGrid')
for w in widths:grid.append(el('gridCol',w=w))
table.append(grid)
allrows=[['구분','항목','사양 및 버전','주요 역할']]+content['environment_rows']
for i,row in enumerate(allrows):
    tr=el('tr');trpr=el('trPr');trpr.append(el('cantSplit'))
    if i==0:trpr.append(el('tblHeader'))
    tr.append(trpr)
    for j,txt in enumerate(row):
        tc=el('tc');tcp=el('tcPr');tcp.append(el('tcW',w=widths[j],type='dxa'));tcp.append(el('vAlign',val='center'))
        if i==0:tcp.append(el('shd',fill='EEEEEE',val='clear'))
        tc.append(tcp);tc.append(para(txt,size=9,bold=i==0,align='center' if j<2 else 'left',indent=False));tr.append(tc)
    table.append(tr)
body.append(table);add('',size=2,indent=False)
endsection(1)
for t in ['3. 결과','4. 논의','5. 결론']:
    heading(t);add('[작성 예정]',indent=False)
heading('References')
add(d['references'],indent=False,align='left')
body.append(section(2))

# Use the retained style definitions, with Korean fallback for this draft.
files['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
files['word/_rels/document.xml.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
files['[Content_Types].xml']=E.tostring(ct,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(OUTPUT,'w',ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
print('Created',OUTPUT,flush=True)

def render_word(path,target):
    import win32com.client
    import fitz
    target.mkdir(parents=True,exist_ok=True)
    app=win32com.client.DispatchEx('Word.Application')
    app.Visible=False;app.DisplayAlerts=0
    document=None
    try:
        document=app.Documents.Open(str(path),ReadOnly=True,AddToRecentFiles=False)
        document.Repaginate()
        pdf=target/'document.pdf'
        document.ExportAsFixedFormat(str(pdf),17)
        print('Word pages',document.ComputeStatistics(2),flush=True)
        p=fitz.open(pdf)
        for i,page in enumerate(p):
            page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(target/f'page-{i+1}.png')
        (target/'text.txt').write_text('\n\n'.join(page.get_text() for page in p),encoding='utf-8')
        return len(p)
    finally:
        if document:document.Close(False)
        app.Quit()

if __name__=='__main__':
    pages=render_word(OUTPUT,QA/'word')
    if not (QA/'reference'/'document.pdf').exists():render_word(TEMPLATE,QA/'reference')
    (QA/'artifact.md').write_text(f'''# Template contract and QA
Reference: ../템플릿/ICIot_Template.docx
Reference SHA256: {hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()}
Output: ../스마트팜_논문_통합초안.docx
Retained A4 size 11906 × 16838 twips; margins top 1701, others 1440; 720 twip column gap.
Retained template style definitions. Full-width author block; body in two columns. Diagrams and native environment table span both columns to remain readable.
Times New Roman 10 pt body; Korean draft fallback 바탕. Title 13 pt; headings 12/10 pt; table 9 pt.
User-authorized draft is Korean; results/discussion/conclusion remain explicit placeholders. No invented measured results.
Accepted tutorial/solver detail is retained in both 2.1 and 2.3 per user request.
Environment is a native editable 10-row, 4-column Word table; hardware/software specification content comes from confirmed local data.
Draft page count: {pages}; final 3-page English limit still requires later editing.
Packaged renderer unavailable on this Windows host (pdf2image missing; no LibreOffice). Rendered with installed Microsoft Word COM ExportAsFixedFormat and PyMuPDF PNGs instead.
''',encoding='utf-8')
    print('Rendered draft pages:',pages,flush=True)
