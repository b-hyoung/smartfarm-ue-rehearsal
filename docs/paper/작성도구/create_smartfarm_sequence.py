from pathlib import Path
from html import escape
from playwright.sync_api import sync_playwright

desktop = Path(__file__).resolve().parents[1] / '절별자료'
width, height = 1400, 1450
pieces = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">팬 운전 조건 탐색 및 모델 재학습 시퀀스 다이어그램</title>
<desc id="desc">사용자, 언리얼 엔진, AI 예측 모델, 볼륨 변환 모듈, OpenFOAM 사이의 제안 처리 순서. 사용자 조작에 따른 예측과 화면 갱신, 별도로 선정한 조건의 CFD 비교 검증과 데이터 추가 재학습을 표시한다.</desc>
<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#344f64"/></marker>
<marker id="return" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="#344f64" stroke-width="1.5"/></marker>
</defs><rect width="1400" height="1450" fill="white"/>
<g font-family="Malgun Gothic, sans-serif" fill="#203848">
<rect x="40" y="165" width="1320" height="665" rx="12" fill="#f8fafc" stroke="#cbd5df" stroke-width="2"/>
<rect x="40" y="870" width="1320" height="430" rx="12" fill="#fffaf2" stroke="#c8ae8c" stroke-width="2"/>
<text x="62" y="204" font-size="24" font-weight="bold">(a) 팬 운전 조건 탐색 — AI·시각화 연계를 위한 제안 동작</text>
<text x="62" y="909" font-size="24" font-weight="bold" fill="#725331">(b) 별도 CFD 검증·재학습 — 선정한 조건에 대해 반복</text>
''']

actors = [(130, '사용자', '', '#f2f7fb'), (400, '언리얼 엔진 5', '(UE5)', '#eef8f2'),
          (670, 'AI 기류 예측 모델', '(PINN / PINO)', '#f4f2fa'),
          (940, '볼륨 변환 모듈', '(OpenVDB)', '#eef8f2'),
          (1210, 'CFD 해석', '(OpenFOAM)', '#fff8ee')]
for x, name, sub, color in actors:
    pieces.append(f'<line x1="{x}" y1="137" x2="{x}" y2="1330" stroke="#a5b5c1" stroke-width="1.6" stroke-dasharray="7 7"/>')
    pieces.append(f'<rect x="{x-115}" y="50" width="230" height="87" rx="11" fill="{color}" stroke="#607889" stroke-width="2"/>')
    pieces.append(f'<text x="{x}" y="86" text-anchor="middle" font-size="24" font-weight="bold">{escape(name)}</text>')
    pieces.append(f'<text x="{x}" y="116" text-anchor="middle" font-size="21">{escape(sub)}</text>')

def message(x1, x2, y, label, reply=False, size=22):
    marker = 'return' if reply else 'arrow'
    dash = ' stroke-dasharray="9 6"' if reply else ''
    pieces.append(f'<path d="M{x1} {y} L{x2} {y}" fill="none" stroke="#344f64" stroke-width="2.5"{dash} marker-end="url(#{marker})"/>')
    pieces.append(f'<text x="{(x1+x2)/2}" y="{y-13}" text-anchor="middle" font-size="{size}">{escape(label)}</text>')

def self_call(x, y, lines, text_left=False):
    pieces.append(f'<path d="M{x} {y} H{x+56} V{y+37} H{x+3}" fill="none" stroke="#344f64" stroke-width="2.5" marker-end="url(#arrow)"/>')
    tx = x-24 if text_left else x+72
    anchor = 'end' if text_left else 'start'
    for i, line in enumerate(lines):
        pieces.append(f'<text x="{tx}" y="{y+13+i*28}" text-anchor="{anchor}" font-size="22">{escape(line)}</text>')

message(130, 400, 270, '1. 팬 조건 조작', size=21)
message(400, 670, 335, '2. 변경된 조건 전달', size=21)
self_call(670, 367, ['3. 기류 예측'])
message(670, 400, 450, '4. 예측 결과 반환', reply=True, size=21)
message(400, 940, 510, '5. 예측 기류 데이터 전달 · 변환 요청', size=21)
self_call(940, 545, ['볼륨 데이터', '변환'])
message(940, 400, 635, '시각화 데이터 반환', reply=True)
self_call(400, 670, ['화면 갱신'])
message(400, 130, 785, '6. 기류·예상 전력 확인', reply=True, size=20)

message(670, 1210, 977, '선정한 추천 조건으로 추가 해석 요청')
self_call(1210, 1005, ['동일 조건 CFD 계산'], text_left=True)
message(1210, 670, 1100, 'CFD 해석 결과 반환', reply=True)
self_call(670, 1135, ['재학습 전 예측값과 비교'])
self_call(670, 1210, ['CFD 데이터 누적 · 모델 재학습'])
pieces.append('<text x="700" y="1280" font-size="20" fill="#725331">갱신된 모델을 이후 기류 예측에 사용</text>')
pieces.append('<text x="700" y="1400" text-anchor="middle" font-size="25" font-weight="bold">그림 2. 팬 운전 조건 탐색 및 모델 재학습 시퀀스 다이어그램</text></g></svg>')
svg = ''.join(pieces)

paragraphs = [
    '그림 2(a)는 사용자의 팬 운전 조건 변경에 따른 기류 예측 및 시각화의 제안 처리 순서를 나타낸다. 사용자가 언리얼 엔진 5 인터페이스에서 팬의 배치, 가동 대수 및 풍량을 변경하면 해당 조건을 AI 기류 예측 모델에 전달한다. 언리얼 엔진은 예측 결과를 반환받아 볼륨 변환 모듈에 전달하고, 변환된 데이터를 받아 화면을 갱신한다. 사용자는 기류 분포와 운전 조건에 따른 예상 전력 지표를 바탕으로 조건을 비교한다.',
    '그림 2(b)와 같이 CFD 검증 및 재학습은 사용자 조작에 따른 예측·시각화와 별도의 절차로 구성한다. 모델이 제안한 조건 중 추가 검증 대상을 선정하여 동일 조건의 CFD 해석을 수행하고, 추가 학습 이전 모델의 예측 결과와 CFD 결과를 비교한다. 이후 해당 CFD 데이터를 학습 데이터에 누적하여 모델을 재학습하며, 선정한 조건에 대해 이 과정을 반복한다. 갱신된 모델은 이후의 기류 예측에 사용한다.',
]
svg_path = desktop / '스마트팜_시퀀스_다이어그램.svg'
svg_path.write_text(svg, encoding='utf-8')
html = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>스마트팜 논문 — 시퀀스 다이어그램</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:#172a3b;font-family:"Malgun Gothic",sans-serif}
main{max-width:1120px;margin:32px auto;padding:40px 44px;background:white;box-shadow:0 8px 32px #21394d12}
h1{font-size:23px;margin:0 0 20px;letter-spacing:-.5px}figure{margin:0 auto 30px}svg{display:block;width:100%;height:auto}
p{font-size:16px;line-height:1.95;word-break:keep-all;margin:0 0 16px;text-indent:1em}
@media(max-width:650px){main{margin:0;padding:20px 12px}h1{font-size:20px}p{font-size:15px}figure{overflow-x:auto}svg{min-width:900px}}
@media print{body{background:white}main{margin:0;padding:0;box-shadow:none}h1{font-size:15pt}p{font-size:10.5pt;line-height:1.6}@page{size:A4;margin:16mm}}
</style><main><h1>시스템 동작 순서</h1><figure>'''+svg+'</figure>'+''.join('<p>'+escape(p)+'</p>' for p in paragraphs)+'</main></html>'
html_path = desktop / '스마트팜_시퀀스_본문.html'
html_path.write_text(html, encoding='utf-8')
(desktop/'스마트팜_시퀀스_본문.txt').write_text('시스템 동작 순서\n\n그림 2. 팬 운전 조건 탐색 및 모델 재학습 시퀀스 다이어그램\n\n'+'\n\n'.join(paragraphs), encoding='utf-8-sig')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width':1200,'height':1100}, device_scale_factor=1)
    page.goto(html_path.as_uri())
    page.evaluate('document.fonts.ready')
    assert page.locator('main p').all_text_contents() == paragraphs
    assert page.locator('svg').count() == 1
    page.screenshot(path=str(desktop/'스마트팜_시퀀스_미리보기.png'), full_page=True, timeout=10000)
    export = browser.new_page(viewport={'width':width,'height':height}, device_scale_factor=2)
    export.set_content('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}svg{display:block}</style>'+svg)
    export.evaluate('document.fonts.ready')
    export.screenshot(path=str(desktop/'스마트팜_시퀀스_다이어그램.png'), full_page=True, timeout=10000)
    print('Created SVG, high-resolution PNG, HTML and text. Diagram and two paragraphs verified.')
    browser.close()
