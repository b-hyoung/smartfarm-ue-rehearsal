from pathlib import Path
from zipfile import ZipFile
from urllib.parse import urlsplit,unquote
import json
from lxml import etree as E, html
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'검수';QA.mkdir(exist_ok=True)
bad=[]
for path in ROOT.rglob('*.html'):
    if '검수' in path.parts:continue
    tree=html.fromstring(path.read_text(encoding='utf-8-sig'))
    for ref in tree.xpath('//@src|//@href'):
        u=urlsplit(ref)
        if u.scheme or ref.startswith('#') or not u.path:continue
        dest=path.parent/unquote(u.path)
        if not dest.exists():bad.append((str(path.relative_to(ROOT)),ref))
assert not bad,bad
with ZipFile(ROOT/'스마트팜_논문_통합초안.docx') as z:
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    x=E.fromstring(z.read('word/document.xml'))
    tables=x.xpath('//w:tbl',namespaces=ns)
    assert len(tables)==1
    assert len(tables[0].findall('w:tr',ns))==10
    text=''.join(x.xpath('//w:t/text()',namespaces=ns))
    for term in ['PINO','comfortHotRoom','buoyantPimpleFoam','재학습','2.11.0','VISION COLLEGE OF JEONJU','youqlrqod@gmail.com']:
        assert term in text,term
    assert len(x.xpath('//w:drawing',namespaces=ns))==2
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1550,'height':1050})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'작성용_HTML'/'index.html').as_uri())
    page.wait_for_function('typeof manuscriptSeed !== "undefined"')
    assert page.locator('#draft').input_value().startswith('2.1 시스템 구성')
    assert page.locator('[data-go="methods"] img').count()==2
    assert page.locator('[data-go="methods"] tbody tr').count()==9
    page.locator('#draft').fill(page.locator('#draft').input_value()+'\n\n지속 저장 확인')
    page.reload()
    assert page.locator('#draft').input_value().endswith('지속 저장 확인')
    page.evaluate('data.methods=manuscriptSeed.methods;localStorage.setItem(key,JSON.stringify(data));render()')
    page.screenshot(path=str(QA/'editor.png'),full_page=False)
    page.goto((ROOT/'논문_전체보기.html').as_uri())
    assert page.locator('figure img').count()==2
    assert page.locator('table tbody tr').count()==9
    assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
    assert page.locator('body').evaluate('(e)=>e.scrollWidth<=innerWidth')
    page.screenshot(path=str(QA/'full-preview.png'),full_page=False)
    page.locator('table').screenshot(path=str(QA/'table.png'))
    assert not errors,errors
    browser.close()
print('PASS: local HTML links, 2 figures, 9 environment rows, native Word table, key text, editor persistence, no JS errors')
