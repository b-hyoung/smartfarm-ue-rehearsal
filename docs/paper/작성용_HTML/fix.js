// Restore Korean text and show the meaning of each English example.
const analysisLink = document.createElement('a');
analysisLink.href = 'analysis.html';
analysisLink.textContent = '📚 실제 논문 3편 분석 보기 →';
analysisLink.style.cssText = 'display:block;margin:0 0 22px;padding:15px 18px;border-radius:9px;background:#dfeee3;color:#245d49;font-weight:700;text-decoration:none';
document.querySelector('main').prepend(analysisLink);
const smartfarmLink = document.createElement('a');
smartfarmLink.href = 'smartfarm-flow.html';
smartfarmLink.textContent = '🌿 스마트팜 논문 전체 흐름과 구성도 보기 →';
smartfarmLink.style.cssText = 'display:block;margin:0 0 10px;padding:15px 18px;border-radius:9px;background:#245d49;color:white;font-weight:700;text-decoration:none';
document.querySelector('main').prepend(smartfarmLink);
const correctFormats = {
  title: ['논문 맨 위에 제목, 저자, 소속을 배치합니다.', '저자는 순서대로 번호를 붙이고 교신저자와 이메일을 표시합니다.', '제목과 저자의 글꼴 크기는 원본 Word 서식을 유지하세요.'],
  abstract: ['제목과 저자 다음에 배치합니다.', 'Abstract 제목은 Times New Roman 12pt, 굵게 표시합니다.', '초록 본문은 Times New Roman 10pt, 이탤릭체로 작성합니다.'],
  keywords: ['초록 뒤에 Keywords:로 시작합니다.', '영어 키워드를 쉼표로 구분해 최소 3개 작성합니다.'],
  intro: ['두 단으로 된 본문의 왼쪽 단에서 시작합니다.', '본문은 Times New Roman 10pt, 단일 줄 간격입니다.', '인용은 마침표 앞에 [1]처럼 표시합니다.'],
  methods: ['서론 다음에 배치하며, 필요하면 2.1, 2.2 등으로 나눕니다.', '본문은 Times New Roman 10pt이며 문단 첫 줄을 약 0.43cm 들여씁니다.'],
  results: ['방법 다음에 결과를 배치합니다.', '그림 캡션은 그림 아래, 표 제목은 표 위에 두고 각각 번호를 매깁니다.', '그림과 표도 영어로 작성하고 캡션은 Times New Roman 10pt를 사용합니다.'],
  discussion: ['결과 다음에 배치하고 결과의 의미와 한계를 설명합니다.', '본문은 Times New Roman 10pt, 단일 줄 간격입니다.'],
  conclusion: ['마지막 본문 섹션에 결론을 포함합니다.', '템플릿 예시에는 별도의 결론이 없지만 지침은 결론 포함을 요구합니다.'],
  ack: ['결론 뒤, 참고문헌 앞에 둡니다.', '감사의 글이 없으면 이 섹션을 삭제합니다.'],
  references: ['본문에서 처음 인용한 순서대로 최소 3개를 작성합니다.', '모든 참고문헌을 본문에서 인용하고 번호를 맞춥니다.', '원본은 IEEE 형식과 DOI 삭제를 안내합니다.']
};
const examples = {
  title: [['Paper title', '논문 제목'], ['First Author / Corresponding author', '제1저자 / 교신저자'], ['Department, Organization, Country, Email', '부서, 기관, 국가, 이메일']],
  abstract: [['This study addresses ...', '이 연구는 ... 문제를 다룹니다.'], ['We propose / investigate ...', '우리는 ...을 제안하거나 연구합니다.'], ['The results show ...', '결과는 ...을 보여줍니다.']],
  keywords: [['Keyword 1, Keyword 2, Keyword 3', '핵심 단어 1, 핵심 단어 2, 핵심 단어 3']],
  intro: [['Recently, ...', '최근 ...'], ['However, existing approaches ... [1].', '그러나 기존 방법은 ... [1].'], ['This study aims to ...', '이 연구의 목적은 ...입니다.']],
  methods: [['We collected / used ...', '우리는 ...을 수집하거나 사용했습니다.'], ['The procedure consisted of ...', '연구 절차는 ...으로 구성되었습니다.'], ['Performance was evaluated using ...', '성능은 ...을 사용해 평가했습니다.']],
  results: [['The results showed ...', '결과는 ...을 보여주었습니다.'], ['As shown in Figure 1, ...', '그림 1에서 보이듯이 ...'], ['Table 1. Summary of results', '표 1. 결과 요약']],
  discussion: [['These findings suggest ...', '이 결과는 ...을 시사합니다.'], ['Compared with previous work [2], ...', '기존 연구 [2]와 비교하면 ...'], ['A limitation of this study is ...', '이 연구의 한계는 ...입니다.']],
  conclusion: [['In this study, ...', '이 연구에서는 ...'], ['The main finding is ...', '주요 발견은 ...입니다.'], ['Future work will ...', '향후 연구에서는 ...']],
  ack: [['This work was supported by ...', '이 연구는 ...의 지원을 받았습니다.']],
  references: [['Author, “Title,” Journal, vol. ..., no. ..., pp. ..., year.', '저자, 「제목」, 학술지, 권, 호, 쪽, 연도.']]
};
const previewNames = { title: '제목 · 저자 · 소속', abstract: 'Abstract · 초록', keywords: 'Keywords · 키워드', intro: '1. Introduction · 서론', methods: '2. Materials and Methods · 재료 및 방법', results: '3. Results · 결과', discussion: '4. Discussion · 논의', conclusion: '5. Conclusion · 결론', ack: 'Acknowledgment · 감사의 글', references: 'References · 참고문헌' };
const guide = document.querySelector('.paper-guide');
guide.querySelector('.eyebrow').textContent = '실시간 미리보기';
guide.querySelector('h2').textContent = '논문은 이렇게 배치돼요';
guide.querySelector('p').textContent = '오른쪽에 글을 쓰면 이곳에 바로 표시됩니다. 초록색 테두리는 지금 작성 중인 부분입니다.';
guide.querySelector('.flow').textContent = '왼쪽 단을 위에서 아래로 읽은 뒤 오른쪽 단으로 이어집니다 →';
guide.querySelector('.note').textContent = '이 미리보기는 배치와 내용의 흐름을 보여주는 예시입니다. 실제 Word의 페이지 수와 줄바꿈은 계산하지 않습니다.';
const details = guide.querySelector('details');
details.querySelector('summary').textContent = '원본 템플릿의 전체 형식 자세히 보기';
details.querySelector('ul').replaceChildren(...[
  'A4, 최대 3페이지, 본문 2단입니다. 여백은 위 3cm, 아래·왼쪽·오른쪽 2.54cm이며 변경하지 않습니다.',
  '본문은 Times New Roman 10pt, 단일 줄 간격입니다. 문단 사이는 빈 줄 없이 첫 줄을 약 0.43cm 들여쓰고, 섹션 사이는 구분합니다.',
  'Abstract 제목은 Times New Roman 12pt 굵게, 초록 본문은 10pt 이탤릭체입니다. 최종 내용은 영어로 작성합니다.',
  '본문 인용은 마침표 앞에 [1], [1, 2], [1-5]처럼 표시합니다. 참고문헌은 최소 3개이며 본문에서 모두 인용하고 처음 등장한 순서로 배열합니다.',
  '그림과 표는 각각 번호를 매기고 그림 설명은 아래, 표 제목은 위에 둡니다. 그림과 표도 영어로 작성합니다.',
  '수식은 가운데에 두고 번호를 괄호로 묶어 오른쪽에 둡니다. 최종 원본 Word 파일을 제출합니다.'
].map(t => { const li = document.createElement('li'); li.textContent = t; return li; }));
details.querySelector('p').textContent = '최신 학회 지침과 원본 양식도 함께 확인하세요.';
document.querySelector('.card > .eyebrow').textContent = '논문 작성';
document.querySelector('.format-box h3').textContent = '이 부분의 위치와 형식';
const exampleBox = document.createElement('div');
exampleBox.className = 'hint example-translations';
document.querySelector('#draft').before(exampleBox);
const oldPaperUpdate = updatePaper;
updatePaper = function () {
  oldPaperUpdate();
  document.querySelectorAll('[data-go]').forEach(button => {
    const id = button.dataset.go;
    button.querySelector('strong').textContent = previewNames[id];
    const content = button.querySelector('.paper-content');
    if (content.classList.contains('empty')) content.textContent = '여기에 작성한 내용이 표시됩니다';
    if (id === 'title' && !content.classList.contains('empty')) {
      // Do not show accidental numbered-list markers as part of the title block.
      // This changes only the preview; the user's saved draft remains untouched.
      content.textContent = content.textContent
        .replace(/^\s*1\.\s*$/gm, '')
        .replace(/^(\s*)1\.\s*(?=Hyoung\s*Suk\s+Park\b)/gim, '$1¹')
        .replace(/\n{3,}/g, '\n\n');
    }
    button.setAttribute('aria-label', previewNames[id] + ' 작성 칸으로 이동');
  });
};
const oldRenderWithFormats = render;
render = function () {
  oldRenderWithFormats();
  const id = sections[active].id;
  $('hintTitle').textContent = '무엇을 쓰면 좋을까요?';
  $('formatRules').replaceChildren(...correctFormats[id].map(t => { const li = document.createElement('li'); li.textContent = t; return li; }));
  exampleBox.replaceChildren();
  const heading = document.createElement('strong'); heading.textContent = '영어 표현 예시와 한국어 뜻'; exampleBox.append(heading);
  const note = document.createElement('p'); note.textContent = '예시는 참고용입니다. 먼저 한국어로 초안을 써도 괜찮아요.'; exampleBox.append(note);
  examples[id].forEach(([en, ko]) => { const p = document.createElement('p'); const b = document.createElement('b'); b.textContent = en; p.append(b, document.createElement('br'), document.createTextNode(ko)); exampleBox.append(p); });
  updatePaper();
};
const authorInfo = '¹HyoungSuk Park\n*¹ First Author / Corresponding Author, Department of Computer Information, [대학교 공식 영문명 확인], Republic of Korea, youqlrqod@gmail.com';
const oldAuthorInfo = '1 HyoungSuk Park\n1 Department of Computer Information, [비전대학교 공식 영문명 확인], Republic of Korea\nE-mail: youqlrqod@gmail.com\n[교신저자 여부 확인]';
if ((data.title || '').includes(oldAuthorInfo)) {
  data.title = data.title.replace(oldAuthorInfo, authorInfo);
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {}
}
const previousAuthorInfo = '¹HyoungSuk Park\n¹ First Author, Department of Computer Information, [대학교 공식 영문명 확인], Republic of Korea, youqlrqod@gmail.com';
if ((data.title || '').includes(previousAuthorInfo)) {
  data.title = data.title.replace(previousAuthorInfo, authorInfo);
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {}
}
if (!(data.title || '').includes('youqlrqod@gmail.com')) {
  data.title = [data.title, authorInfo].filter(Boolean).join('\n\n');
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {
    $('status').textContent = '저장할 수 없습니다. 초안을 백업해 주세요.';
  }
}
if ((data.title || '').includes('youqlrqod@gmail.com') && data.title.includes('[대학교 공식 영문명 확인]')) {
  data.title = data.title.replace('[대학교 공식 영문명 확인]', 'VISION COLLEGE OF JEONJU');
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {}
}
const oldAffiliation = '*¹ First Author / Corresponding Author, Department of Computer Information, VISION COLLEGE OF JEONJU, Republic of Korea, youqlrqod@gmail.com';
const formattedAffiliation = '*¹ First Author / Corresponding Author,\nDepartment of Computer Information, VISION COLLEGE OF JEONJU,\nRepublic of Korea, youqlrqod@gmail.com';
if ((data.title || '').includes(oldAffiliation)) {
  data.title = data.title.replace(oldAffiliation, formattedAffiliation);
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) {}
}
try {
  const titleAppliedKey = 'iciot-selected-korean-title-v1';
  if (!localStorage.getItem(titleAppliedKey)) {
    const selectedTitle = '디지털 트윈을 활용한 스마트팜 기류 예측 및 시각화';
    const current = data.title || '';
    const lines = current.split('\n');
    const first = lines.findIndex(line => line.trim());
    if (first < 0) {
      data.title = selectedTitle;
    } else if (/^(?:[¹*]|1(?:\.|\s))\s*Hyoung\s*Suk\s+Park/i.test(lines[first].trim())) {
      data.title = selectedTitle + '\n\n' + current;
    } else if (lines[first].trim() !== selectedTitle) {
      lines[first] = selectedTitle;
      data.title = lines.join('\n');
    }
    localStorage.setItem(key, JSON.stringify(data));
    localStorage.setItem(titleAppliedKey, '1');
  }
} catch (e) {
  $('status').textContent = '제목 자동 저장을 확인하지 못했습니다. 초안을 백업해 주세요.';
}
active = 0;
render();

// Offer the agreed Korean abstract without replacing a draft the user has written.
const agreedAbstract = '스마트팜 재배 공간에서는 냉난방기와 팬의 운전 조건에 따라 상·하단 재배단 간 기류 차이가 발생할 수 있어, 재배 환경과 설비의 전력 사용을 함께 고려한 운전 조건 탐색이 필요하다. 그러나 전산유체역학(CFD) 기반 수치해석은 운전 조건이 바뀔 때마다 계산을 반복해야 하므로 다양한 조건을 검토하는 데 시간과 연산 비용이 소요된다. 본 연구에서는 OpenFOAM으로 생성한 기류 해석 데이터를 이용해 물리정보 신경망(PINN) 기반 예측 모델을 학습하고, 팬 운전 조건에 따른 기류 예측 결과를 학습에 사용하지 않은 조건의 CFD 결과와 비교·평가하였다. 또한 언리얼 엔진을 활용해 가상의 스마트팜 공간을 구현하고, 작업자가 운전 조건을 변경하며 예측된 기류 분포와 예상 전력 사용을 3차원 화면에서 확인할 수 있는 시각화 시스템 구조를 제안한다. 이를 통해 재배단별 기류와 전력 사용을 함께 살펴보며 적절한 공조 운전 조건을 효율적으로 탐색할 수 있는 기반을 제공한다.';
try {
  const abstractAppliedKey = 'iciot-korean-abstract-v1';
  if (!localStorage.getItem(abstractAppliedKey)) {
    if (!(data.abstract || '').trim()) {
      data.abstract = agreedAbstract;
      localStorage.setItem(key, JSON.stringify(data));
      active = sections.findIndex(section => section.id === 'abstract');
      render();
    }
    localStorage.setItem(abstractAppliedKey, '1');
  }
} catch (e) {
  $('status').textContent = '초안 자동 저장을 확인하지 못했습니다. 백업을 확인해 주세요.';
}

// Save the chosen keyword draft once, preserving any existing user text.
try {
  const keywordsAppliedKey = 'iciot-keywords-v1';
  if (!localStorage.getItem(keywordsAppliedKey)) {
    if (!(data.keywords || '').trim()) {
      data.keywords = 'Smart Farm, Computational Fluid Dynamics (CFD), Physics-Informed Neural Network (PINN), Unreal Engine, Airflow Distribution';
      localStorage.setItem(key, JSON.stringify(data));
      active = sections.findIndex(section => section.id === 'keywords');
      render();
    }
    localStorage.setItem(keywordsAppliedKey, '1');
  }
} catch (e) {
  $('status').textContent = '키워드 자동 저장을 확인하지 못했습니다. 초안을 백업해 주세요.';
}

// Apply the user's selected introduction once and retain the previous draft.
try {
  const introAppliedKey = 'iciot-introduction-2026-v1';
  if (!localStorage.getItem(introAppliedKey)) {
    localStorage.setItem('iciot-guide-backup-before-introduction-v1', JSON.stringify(data));
    data.intro = '스마트팜 재배 공간에서는 냉난방기와 팬의 배치 및 운전 조건에 따라 재배 위치별 기류가 달라질 수 있다. 선행연구에서는 수직농장의 공기 유입·배출 위치에 따라 공간 내 온도와 기류의 균일성이 달라지는 것을 확인하였다 [1]. 따라서 재배단별 기류 분포를 균일하게 관리하면서도, 설비 운전에 필요한 전력 소비를 함께 고려할 필요가 있다. 이를 위해 전산유체역학(CFD)을 사용하여 다양한 운전 조건의 기류를 분석할 수 있지만, 조건이 바뀔 때마다 수치해석을 반복하는 데에는 시간과 연산 비용이 소요된다.\n\n본 연구에서는 스마트팜 공간의 기류 예측과 시각화를 위한 시스템을 제안한다. OpenFOAM으로 생성한 CFD 데이터를 이용해 물리정보 신경망(PINN) 기반 예측 모델을 학습하고, 학습에 사용하지 않은 팬 운전 조건의 예측 결과를 동일한 조건의 CFD 결과와 비교하여 예측 오차를 평가하였다. 또한 언리얼 엔진을 활용하여 가상의 스마트팜 공간을 구현하고, 사용자가 운전 조건에 따른 기류 분포와 예상 전력 사용을 3차원 화면에서 살펴볼 수 있는 구조를 제시한다.\n\n이를 통해 상·하단 재배단의 기류와 전력 사용을 함께 고려하여 공조 운전 조건을 탐색할 수 있는 기반을 마련하고자 한다.';
    const reference = '[1] 김경민, 정효혁, 이인복, “전산유체역학을 이용한 수직농장 내부 미기상 환경의 균일도 분석,” 생물환경조절학회지, 제35권, 제3호, pp. 262–273, 2026.';
    const existingRefs = data.references || '';
    if (!existingRefs.includes('전산유체역학을 이용한 수직농장 내부 미기상 환경의 균일도 분석')) {
      if (!existingRefs.trim()) data.references = reference;
      else if (!/^\s*\[1\]/m.test(existingRefs)) data.references = reference + '\n' + existingRefs;
    }
    localStorage.setItem(key, JSON.stringify(data));
    localStorage.setItem(introAppliedKey, '1');
    active = sections.findIndex(section => section.id === 'intro');
    render();
  }
} catch (e) {
  $('status').textContent = '서론 저장을 확인하지 못했습니다. 브라우저 저장 상태를 확인해 주세요.';
}
