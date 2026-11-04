from pathlib import Path
from html import escape
from playwright.sync_api import sync_playwright

desktop = Path(__file__).resolve().parents[1] / '절별자료'
figure = desktop / '스마트팜_시스템_구성도.svg'
svg = figure.read_text(encoding='utf-8-sig')

paragraphs = [
    '본 연구에서는 스마트팜 다단 재배 공간의 운전 조건에 따른 기류를 예측하고, 이를 3차원 가상 환경에서 검토하기 위한 시스템을 제안한다. 시스템은 그림 1과 같이 OpenFOAM 기반 CFD 기류 해석, AI 기류 예측 모델(PINN/PINO), 3차원 볼륨 변환, 언리얼 엔진 5(UE5) 기반 가상 환경의 네 모듈로 구성된다.',
    '해석 대상은 가로 8.0 m × 깊이 5.7 m × 높이 2.7 m 크기의 반타원형 스마트팜 공간이다. 공간 형상과 재배단 구조, 냉난방기 공급 조건을 기본 환경으로 고정하고, 순환 팬의 배치(높이·기울기)와 가동 대수, 풍량을 변경하여 운전 조건별 시간·공간 기류 해석 데이터를 생성하였다. 해석 환경은 OpenFOAM의 실내 기류 및 열전달 해석 예제인 comfortHotRoom을 기반으로 구성하였다. 대상 공간에 맞게 형상과 경계조건을 수정하고, 시간에 따른 기류 및 온도 변화를 확인하기 위해 buoyantPimpleFoam 솔버와 표준 k-ε 난류 모델을 이용한 비정상 수치해석을 수행하였다.',
    '생성된 CFD 데이터는 PINN 및 PINO 기반 기류 예측 모델의 학습에 활용된다. 특히 모델이 유망하다고 예측한 팬 운전 조건에 대해 동일 조건의 CFD 해석을 추가로 수행한 후, 예측 결과를 비교·검증하여 해당 CFD 해석 데이터를 학습 데이터에 누적하고 모델을 반복적으로 재학습하였다. 또한 CFD 해석 결과를 OpenVDB 형식으로 변환하여 공간 전체의 기류 및 온도 볼륨 데이터를 구축하고, 이를 언리얼 엔진 5 환경에서 3차원으로 시각화한다. 나아가 AI 예측 모델과 시각화 모듈의 연계를 통해, 사용자가 팬 운전 조건에 따른 기류 분포와 전력 지표를 3차원 화면에서 직관적으로 비교·검토할 수 있는 대화형 탐색 시스템 구조를 제시한다.',
]

html = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>스마트팜 논문 — 시스템 구성 및 CFD 해석</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:#172a3b;font-family:"Malgun Gothic",sans-serif}
main{max-width:940px;margin:32px auto;padding:42px 54px;background:white;box-shadow:0 8px 32px #21394d12}
h1{font-size:23px;margin:0 0 24px;letter-spacing:-.5px}figure{margin:0 auto 20px;max-width:640px}
svg{display:block;width:100%;height:auto}p{font-size:16px;line-height:1.95;text-align:justify;word-break:keep-all;margin:0 0 16px;text-indent:1em}
@media(max-width:650px){main{margin:0;padding:24px 18px}h1{font-size:20px}p{font-size:15px}}
@media print{body{background:white}main{margin:0;padding:0;max-width:none;box-shadow:none}figure{max-width:480px}p{font-size:10.5pt;line-height:1.65}h1{font-size:15pt}@page{size:A4;margin:16mm}}
</style><main><h1>시스템 구성 및 CFD 해석</h1><figure>'''+svg+'''</figure>'''+''.join('<p>'+escape(p)+'</p>' for p in paragraphs)+'''</main></html>'''
page_path = desktop / '스마트팜_시스템구성_본문.html'
page_path.write_text(html, encoding='utf-8')
text_path = desktop / '스마트팜_시스템구성_본문.txt'
text_path.write_text('시스템 구성 및 CFD 해석\n\n그림 1. 스마트팜 기류 예측 및 시각화 시스템 구성도\n\n'+'\n\n'.join(paragraphs), encoding='utf-8-sig')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width':1100,'height':1050},device_scale_factor=1)
    page.goto(page_path.as_uri())
    page.evaluate('document.fonts.ready')
    page.screenshot(path=str(desktop/'스마트팜_시스템구성_미리보기.png'), full_page=True)
    figure_page = browser.new_page(viewport={'width':1200,'height':1340}, device_scale_factor=2)
    # Render SVG inside HTML, matching the working preview capture path.
    figure_page.set_content('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}svg{display:block}</style>' + svg)
    figure_page.evaluate('document.fonts.ready')
    figure_page.screenshot(path=str(desktop/'스마트팜_시스템_구성도.png'), full_page=True, timeout=10000)
    assert page.locator('main p').count() == 3
    assert page.locator('svg').count() == 1
    assert page.locator('main p').all_text_contents() == paragraphs
    assert 'CFD 재검증 · 재학습' in page.locator('svg').text_content()
    print('Created HTML and text. Screenshot saved. Three paragraphs and one diagram verified.')
    browser.close()
