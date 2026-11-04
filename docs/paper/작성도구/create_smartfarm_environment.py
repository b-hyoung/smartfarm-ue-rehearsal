from pathlib import Path
from html import escape
from datetime import datetime, timezone
import json
from playwright.sync_api import sync_playwright

desktop = Path(__file__).resolve().parents[1] / '절별자료'
title = '2.4 개발 환경'
intro = '본 연구에서 제안하는 시스템의 구현을 위한 주요 하드웨어와 소프트웨어 개발 환경은 표 1과 같다. CFD 수치해석과 AI 모델 학습, 3차원 볼륨 시각화를 위한 개발 장비는 12코어 CPU와 16GB VRAM을 갖춘 GPU로 구성하였다. OpenFOAM 해석 및 볼륨 데이터 가공에는 WSL 2 기반 Docker 환경을 사용하여 프로그램 버전과 실행 환경을 통일하였다.'
rows = [
    ('하드웨어', 'CPU', 'AMD Ryzen 9 9900X (12코어)', 'CFD 수치해석 연산'),
    ('하드웨어', 'GPU', 'NVIDIA GeForce RTX 5060 Ti (16GB)', 'AI 모델 학습 및 3D 렌더링'),
    ('하드웨어', 'RAM', '64GB', '학습·볼륨 데이터 처리'),
    ('소프트웨어', 'OS', 'Windows 11 Pro (64비트)', '개발 및 시각화 구동'),
    ('소프트웨어', '실행 환경', 'Docker Desktop / WSL 2', '해석·변환 프로그램의 버전과 실행 환경 통일'),
    ('소프트웨어', 'CFD', 'OpenFOAM v2512', '격자 생성 및 비정상 기류 해석'),
    ('소프트웨어', 'AI 개발', 'Python 3.11.4 / PyTorch 2.11.0', 'PINN/PINO 모델 학습·예측'),
    ('소프트웨어', '볼륨 가공', 'OpenVDB', '풍속·온도 데이터를 .vdb로 변환'),
    ('소프트웨어', '3D 엔진', 'Unreal Engine 5.8.3', '가상 공간 및 기류 시각화'),
]
notes = [
    '주: PC 사양과 설치 버전은 현재 확인값이다. 일부 CFD 해석은 Mac에서 수행되었으며, 실험별 환경은 최종 성능 비교 시 확인한다.',
]
sources = [
    ('프로젝트 엔진 설정', 'C:/Users/ACE/Desktop/smartfarm-ue-rehearsal/ue/SF_Rehearsal.uproject'),
    ('CFD 실행 환경 문서', 'C:/Users/ACE/Desktop/smartfarm-ue-rehearsal/docs/START-HERE.md'),
    ('OpenFOAM 실행 로그', 'C:/Users/ACE/Desktop/smartfarm-ue-rehearsal/data/runs/2026-09-23-fan-study-17-18/17_L3/log.decomposePar'),
    ('VDB 컨테이너 구성 코드', 'C:/Users/ACE/Desktop/smartfarm-ue-rehearsal/src/make_vdb.sh'),
    ('장비별 CFD 작업 기록', 'C:/Users/ACE/Desktop/smartfarm-ue-rehearsal/docs/FAN-RESULTS.md'),
]
def lines(text):
    return escape(text).replace('\n', '<br>')
table_rows = []
for i, (group, item, spec, role) in enumerate(rows):
    group_cell = ''
    if i == 0 or rows[i-1][0] != group:
        count = sum(1 for row in rows if row[0] == group)
        group_cell = f'<th class="group" scope="rowgroup" rowspan="{count}">{escape(group)}</th>'
    table_rows.append('<tr>'+group_cell+'<td>'+lines(item)+'</td><td>'+lines(spec)+'</td><td>'+lines(role)+'</td></tr>')
table = '<table><caption>표 1. 시스템 개발 환경</caption><thead><tr><th>구분</th><th>항목</th><th>사양 및 버전</th><th>주요 역할</th></tr></thead><tbody>'+''.join(table_rows)+'</tbody></table>'
html = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>스마트팜 논문 — 개발 환경</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:#172a3b;font-family:"Malgun Gothic",sans-serif}
main{max-width:1080px;margin:32px auto;padding:38px 46px;background:white;box-shadow:0 8px 32px #21394d12}
h1{font-size:23px;margin:0 0 22px}p{font-size:16px;line-height:1.85;word-break:keep-all;margin:0 0 22px}
table{width:100%;border-collapse:collapse;font-size:14px;table-layout:fixed;line-height:1.65}caption{text-align:left;font-weight:bold;font-size:16px;margin:0 0 10px}
th,td{padding:10px 13px;border:1px solid #cbd5df;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#edf4f9;font-weight:bold}
thead th:nth-child(1){width:12%}thead th:nth-child(2){width:13%}thead th:nth-child(3){width:40%}thead th:nth-child(4){width:35%}.group{vertical-align:middle;text-align:center;background:#f2f6fa;font-weight:600}tbody tr:nth-child(even){background:#fafcfd}
.notes{margin-top:16px;color:#536778}.notes p{font-size:12px;line-height:1.7;margin:0}
details{margin-top:20px;font-size:13px;line-height:1.9;color:#4d6274}details ul{padding-left:20px}a{color:#22649a}
@media(max-width:650px){main{margin:0;padding:22px 14px}table{font-size:12px}td,th{padding:8px}p{font-size:15px}}
@media print{body{background:white}main{margin:0;padding:0;box-shadow:none}h1{font-size:15pt}p{font-size:10pt}table{font-size:9pt}td,th{padding:6px}details{display:none}.notes p{font-size:8pt}@page{size:A4;margin:15mm}}
</style><main>'''+f'<h1>{escape(title)}</h1><p>{escape(intro)}</p>'+table+'<div class="notes">'+''.join('<p>'+escape(n)+'</p>' for n in notes)+'</div></main></html>'
page_path = desktop/'스마트팜_개발환경_본문.html'
page_path.write_text(html, encoding='utf-8')
(desktop/'스마트팜_개발환경_본문.txt').write_text(title+'\n\n'+intro+'\n\n표 1. 시스템 개발 환경 — 초안\n\n'+'\n'.join(' | '.join(v.replace('\n','; ') for v in row) for row in rows)+'\n\n'+'\n\n'.join(notes), encoding='utf-8-sig')
(desktop/'스마트팜_개발환경_확인기록.json').write_text(json.dumps({
    'observed_at_utc':datetime.now(timezone.utc).isoformat(),
    'current_environment_only':{'os':'Windows 11 Pro','os_build':'10.0.26200','cpu':'AMD Ryzen 9 9900X','physical_memory_GiB':64,'gpu':'NVIDIA GeForce RTX 5060 Ti','gpu_reported_memory_MiB':16311,'gpu_driver':'610.88','python':'3.11.4','torch':'2.11.0+cu128','unreal_installed':'5.8.3','docker_desktop':'4.52.0.210994','docker_cli':'29.0.1','docker_backend':'WSL 2','docker_daemon':'not running during inspection','git':'2.52.0.windows.1'},
    'project_evidence':{'unreal_association':'5.8','openfoam_execution_log':'2512','openfoam_image':'opencfd/openfoam-default:2512','vdb_build_image':'sf-openvdb:1','vdb_base_image':'debian:bookworm-slim'},
    'not_verified':['Exact hardware used for each historical run','Mac model and macOS version','Historical PyTorch version for each model experiment','Exact OpenVDB package version','Currently available Docker images while daemon is stopped'],
    'sources':sources
},ensure_ascii=False,indent=2),encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page=browser.new_page(viewport={'width':1180,'height':1100}, device_scale_factor=1)
    page.goto(page_path.as_uri())
    page.evaluate('document.fonts.ready')
    assert page.locator('tbody tr').count()==len(rows)
    assert page.locator('h1').inner_text()==title
    page.screenshot(path=str(desktop/'스마트팜_개발환경_미리보기.png'),full_page=True,timeout=10000)
    browser.close()
print(f'Saved simplified development-environment HTML and text. Verified {len(rows)} table rows.')
