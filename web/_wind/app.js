(function () {
  'use strict';
  var KEYS = Object.keys(SCENE).sort();
  var cur = SCENE['05_F3'] ? '05_F3' : KEYS[0];
  var VMAX = 1.6, LO = 0.3, HI = 1.0;
  var BEDZ = [0.55, 1.35], CANOPY = 0.25, MID = 0.125;
  // 본 점수는 베드 전체다 - src/judge.py 와 같은 범위라야 docs/FAN-RESULTS.md 와 어긋나지 않는다.
  // MARGIN 은 보조로만 쓴다: 프레임·기둥이 있어 실제로는 모종이 안 앉는 테두리 폭(m).
  var MARGIN = 0.10;
  // three.js 는 CDN 에서 온다. 인터넷이 없으면 3D 만 빠지고 나머지는 그대로 보여 준다.
  var HAS3D = (typeof THREE !== 'undefined');

  // ── 색 ────────────────────────────────────────────────────────────────
  var STOPS = [[0, 27, 58, 92], [0.2, 44, 110, 143], [0.42, 70, 160, 106],
               [0.62, 216, 192, 74], [0.8, 201, 112, 44], [1, 155, 45, 45]];
  function col(v) {
    if (v === null || v === undefined) return [90, 90, 90];
    var t = Math.max(0, Math.min(1, v / VMAX));
    for (var i = 0; i < STOPS.length - 1; i++) {
      var a = STOPS[i], b = STOPS[i + 1];
      if (t >= a[0] && t <= b[0]) {
        var f = (t - a[0]) / (b[0] - a[0]);
        return [Math.round(a[1] + (b[1] - a[1]) * f),
                Math.round(a[2] + (b[2] - a[2]) * f),
                Math.round(a[3] + (b[3] - a[3]) * f)];
      }
    }
    return [155, 45, 45];
  }

  function imageOf(t) {
    var c = document.createElement('canvas');
    c.width = t.nx; c.height = t.ny;
    var g = c.getContext('2d'), im = g.createImageData(t.nx, t.ny);
    for (var j = 0; j < t.ny; j++) {
      for (var i = 0; i < t.nx; i++) {
        var v = t.g[t.ny - 1 - j][i], c3 = col(v), o = (j * t.nx + i) * 4;
        im.data[o] = c3[0]; im.data[o + 1] = c3[1]; im.data[o + 2] = c3[2]; im.data[o + 3] = 255;
      }
    }
    g.putImageData(im, 0, 0);
    return c;
  }

  // ── 3D 무대 ───────────────────────────────────────────────────────────
  var canvas = document.getElementById('gl');
  var renderer, scene, camera, lineMat, acMat, retMat, rackMat;
  var gRoom, gAC, gCanopy, gFan, gGrid, gField, gRack;

  function P(x, y, z) { return new THREE.Vector3(x, z, -y); }   // CFD -> three

  function ellipsePts(z) {
    var pts = [];
    for (var k = 0; k <= 60; k++) {
      var th = Math.PI * k / 60;
      pts.push(P(4 * Math.cos(th), 5.7 * Math.sin(th), z));
    }
    return pts;
  }
  function init3D() {
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, 2, 0.1, 100);
    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    var dl = new THREE.DirectionalLight(0xffffff, 0.55);
    dl.position.set(4, 8, 5); scene.add(dl);

    gRoom = new THREE.Group(); gAC = new THREE.Group(); gCanopy = new THREE.Group();
    gFan = new THREE.Group(); gGrid = new THREE.Group(); gField = new THREE.Group();
    gRack = new THREE.Group();
    [gRoom, gAC, gCanopy, gFan, gGrid, gField, gRack].forEach(function (g) { scene.add(g); });

    lineMat = new THREE.LineBasicMaterial({ color: 0x5b6f66 });
    [0, 2.7].forEach(function (z) {
      gRoom.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ellipsePts(z)), lineMat));
      gRoom.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(
        [P(-4, 0, z), P(4, 0, z)]), lineMat));
    });
    [[-4, 0], [4, 0], [0, 5.7], [2.65, 4.27], [-2.65, 4.27]].forEach(function (p) {
      gRoom.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(
        [P(p[0], p[1], 0), P(p[0], p[1], 2.7)]), lineMat));
    });

    var gridHelper = new THREE.GridHelper(10, 20, 0x3a4a43, 0x263029);
    gridHelper.position.set(0, 0.001, -2.85);
    gGrid.add(gridHelper);

    rackMat = new THREE.MeshLambertMaterial({ color: 0x8a9a92 });
    BEDZ.forEach(function (z) {
      var m = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.05, 0.8), rackMat);
      m.position.copy(P(0, 2.0, z - 0.025)); gRack.add(m);
    });
    [[-1.2, 1.6], [1.2, 1.6], [-1.2, 2.4], [1.2, 2.4]].forEach(function (p) {
      var m = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.6, 0.06), rackMat);
      m.position.copy(P(p[0], p[1], 0.8)); gRack.add(m);
    });

    // 에어컨은 케이스마다 자리가 달라 build 에서 다시 놓는다
    acMat = new THREE.MeshLambertMaterial({ color: 0xcfd8cf });
    retMat = new THREE.MeshLambertMaterial({ color: 0x2C6E8F });
  }

  function clear(g) { while (g.children.length) { g.remove(g.children[0]); } }

  function buildAC(d) {
    clear(gAC);
    var c = (d.ac && d.ac.length === 2) ? d.ac : [0, 2.0];
    var body = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.08, 0.95), acMat);
    body.position.copy(P(c[0], c[1], 2.66)); gAC.add(body);
    var ret = new THREE.Mesh(new THREE.BoxGeometry(0.57, 0.05, 0.57), retMat);
    ret.position.copy(P(c[0], c[1], 2.63)); gAC.add(ret);
    [[0.45, 0], [-0.45, 0], [0, 0.45], [0, -0.45]].forEach(function (o) {
      gAC.add(new THREE.ArrowHelper(new THREE.Vector3(0, -1, 0),
        P(c[0] + o[0], c[1] + o[1], 2.6), 0.55, 0x9ec9dd, 0.16, 0.1));
    });
  }

  var fieldPlanes = [];                       // [아래 단, 위 단] 바닥 텍스처 면
  function build(id) {
    if (!HAS3D) return;
    var d = SCENE[id];
    clear(gField); clear(gCanopy); clear(gFan);
    fieldPlanes = [];
    buildAC(d);
    ['t0', 't1'].forEach(function (tk, ti) {
      var t = d.tiers[tk], z = BEDZ[ti];
      var tex = new THREE.CanvasTexture(imageOf(t));
      tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearFilter;
      var pl = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.8),
        new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide }));
      pl.rotation.x = -Math.PI / 2;
      pl.position.copy(P(0, 2.0, z + MID));
      gField.add(pl);
      fieldPlanes.push(pl);

      var box = new THREE.Mesh(new THREE.BoxGeometry(2.4, CANOPY, 0.8),
        new THREE.MeshLambertMaterial({ color: 0x4f7f57, transparent: true, opacity: 0.16 }));
      box.position.copy(P(0, 2.0, z + CANOPY / 2));
      gCanopy.add(box);
      var eg = new THREE.LineSegments(new THREE.EdgesGeometry(box.geometry),
        new THREE.LineBasicMaterial({ color: 0x6fa87a }));
      eg.position.copy(box.position); gCanopy.add(eg);

      (d.fans || []).forEach(function (f) {
        var fz = z + f.dz;
        var dir = new THREE.Vector3(f.dir[0], f.dir[2], -f.dir[1]).normalize();
        var fan = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.08, 20),
          new THREE.MeshLambertMaterial({ color: 0xe8e8e8 }));
        fan.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        fan.position.copy(P(f.x, f.y, fz));
        gFan.add(fan);
        gFan.add(new THREE.ArrowHelper(dir, P(f.x, f.y, fz), 0.75, 0xffb26b, 0.2, 0.12));
      });
    });
  }

  // ── 카메라 ────────────────────────────────────────────────────────────
  var tgt = new THREE.Vector3(0, 1.0, -2.0);
  var rot = { th: -0.62, ph: 0.92, r: 7.4 };
  function place() {
    if (!HAS3D) return;
    camera.position.set(
      tgt.x + rot.r * Math.sin(rot.ph) * Math.sin(rot.th),
      tgt.y + rot.r * Math.cos(rot.ph),
      tgt.z + rot.r * Math.sin(rot.ph) * Math.cos(rot.th));
    camera.lookAt(tgt);
  }
  var drag = null;
  canvas.addEventListener('pointerdown', function (e) {
    drag = { x: e.clientX, y: e.clientY, b: e.button };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointerup', function () { drag = null; });
  canvas.addEventListener('pointermove', function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.b === 2) { tgt.x -= dx * 0.006; tgt.y += dy * 0.006; }
    else {
      rot.th -= dx * 0.008;
      rot.ph = Math.max(0.12, Math.min(1.56, rot.ph - dy * 0.006));
    }
    place(); render();
  });
  canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    rot.r = Math.max(2.2, Math.min(20, rot.r * (1 + Math.sign(e.deltaY) * 0.1)));
    place(); render();
  }, { passive: false });

  function resize() {
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== w || canvas.height !== h) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h; camera.updateProjectionMatrix();
    }
  }
  function render() { if (!HAS3D) return; resize(); renderer.render(scene, camera); }

  // ── 위에서 본 지도 ─────────────────────────────────────────────────────
  function drawMap(cv, t) {
    var W = 520, H = Math.round(W * 0.8 / 2.4);
    cv.width = W; cv.height = H;
    var g = cv.getContext('2d');
    g.imageSmoothingEnabled = true;
    g.drawImage(imageOf(t), 0, 0, W, H);
    var mx = MARGIN / 2.4 * W, my = MARGIN / 0.8 * H;
    g.strokeStyle = 'rgba(255,255,255,.85)';
    g.lineWidth = 1.5;
    g.setLineDash([5, 4]);
    g.strokeRect(mx, my, W - 2 * mx, H - 2 * my);
    g.setLineDash([]);
  }

  // ── 고르기 프로파일 ────────────────────────────────────────────────────
  function profiles(t) {
    var mi = 0, mj = 0;                    // 베드 전체. 테두리를 빼면 본 점수와 어긋난다.
    var px = [], py = [], i, j, s, n;
    for (i = mi; i < t.nx - mi; i++) {
      s = 0; n = 0;
      for (j = mj; j < t.ny - mj; j++) { if (t.g[j][i] != null) { s += t.g[j][i]; n++; } }
      px.push(n ? s / n : null);
    }
    for (j = mj; j < t.ny - mj; j++) {
      s = 0; n = 0;
      for (i = mi; i < t.nx - mi; i++) { if (t.g[j][i] != null) { s += t.g[j][i]; n++; } }
      py.push(n ? s / n : null);
    }
    return { x: px, y: py };
  }

  function drawProfile(svg, series, axisLabel) {
    var W = 420, H = 210, L = 42, R = 10, T = 12, B = 30;
    var top = 0;
    series.forEach(function (s) {
      s.v.forEach(function (v) { if (v != null && v > top) top = v; });
    });
    top = Math.max(1.2, Math.ceil(top * 10) / 10);
    function X(i, n) { return L + (W - L - R) * (n > 1 ? i / (n - 1) : 0.5); }
    function Y(v) { return T + (H - T - B) * (1 - v / top); }
    var out = [];
    out.push('<rect x="' + L + '" y="' + Y(HI) + '" width="' + (W - L - R) +
             '" height="' + (Y(LO) - Y(HI)) + '" fill="#2F6B48" opacity="0.13"/>');
    [LO, HI].forEach(function (v) {
      out.push('<line x1="' + L + '" y1="' + Y(v) + '" x2="' + (W - R) + '" y2="' + Y(v) +
               '" stroke="#2F6B48" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>');
      out.push('<text x="' + (L - 6) + '" y="' + (Y(v) + 4) + '" text-anchor="end" font-size="10" ' +
               'fill="currentColor" opacity="0.6" font-family="monospace">' + v.toFixed(1) + '</text>');
    });
    out.push('<line x1="' + L + '" y1="' + Y(0) + '" x2="' + (W - R) + '" y2="' + Y(0) +
             '" stroke="currentColor" opacity="0.25"/>');
    out.push('<text x="' + (L - 6) + '" y="' + (Y(top) + 4) + '" text-anchor="end" font-size="10" ' +
             'fill="currentColor" opacity="0.6" font-family="monospace">' + top.toFixed(1) + '</text>');
    series.forEach(function (s) {
      var pts = [];
      s.v.forEach(function (v, i) { if (v != null) pts.push(X(i, s.v.length) + ',' + Y(v)); });
      out.push('<polyline points="' + pts.join(' ') + '" fill="none" stroke="' + s.c +
               '" stroke-width="2.1" stroke-linejoin="round" stroke-dasharray="' +
               (s.d || 'none') + '"/>');
    });
    out.push('<text x="' + ((L + W - R) / 2) + '" y="' + (H - 8) + '" text-anchor="middle" ' +
             'font-size="10.5" fill="currentColor" opacity="0.55">' + axisLabel + '</text>');
    var lx = L + 6;
    series.forEach(function (s) {
      out.push('<rect x="' + lx + '" y="' + (T + 2) + '" width="12" height="3" fill="' + s.c + '"/>');
      out.push('<text x="' + (lx + 16) + '" y="' + (T + 8) + '" font-size="10" ' +
               'fill="currentColor" opacity="0.7">' + s.n + '</text>');
      lx += 62;
    });
    svg.innerHTML = out.join('');
  }

  // ── 표·설명 ───────────────────────────────────────────────────────────
  function cond(d) {
    if (!d.cmm) return d.layout === 'none' ? '팬 없음' : '팬 꺼짐';
    var n = (d.fans || []).length * 2;      // fans 는 한 단 몫이라 2단이면 두 배
    var s = d.cmm.toFixed(1) + ' CMM × ' + n + '대';
    if (d.layout === 'top') return s + ' · 상부 하방';
    return s + ' · ' + d.tilt + '° · 선반 +' + d.h.toFixed(2) + ' m';
  }

  function verdict(t) {
    if (t.p10 >= LO && t.p90 <= HI) return ['통과', 'ok'];
    if (t.p10 < LO) return ['하한 미달', 'bad'];
    return ['상한 초과', 'bad'];
  }

  function paintTable() {
    var rows = KEYS.slice().sort(function (a, b) {
      return SCENE[b].tiers.t0.band - SCENE[a].tiers.t0.band;
    });
    document.getElementById('rows').innerHTML = rows.map(function (k) {
      var d = SCENE[k], t = d.tiers.t0;
      return '<tr class="clk' + (k === cur ? ' sel' : '') + '" data-k="' + k + '">' +
        '<td><b>' + k.replace('_', ' ') + '</b>' +
          (d.snaps < 6 ? ' <span style="color:var(--warn);font-size:11px">' + d.snaps +
                         '장</span>' : '') +
        '</td><td style="color:var(--ink-soft)">' + cond(d) + '</td>' +
        '<td class="' + (t.p10 < LO ? 'bad' : 'ok') + '">' + t.p10.toFixed(3) + '</td>' +
        '<td>' + t.p50.toFixed(3) + '</td>' +
        '<td class="' + (t.p90 > HI ? 'bad' : 'ok') + '">' + t.p90.toFixed(3) + '</td>' +
        '<td><div style="display:flex;align-items:center;gap:8px"><div class="barcell">' +
          '<i style="width:' + t.band + '%"></i></div><span>' + t.band + '%</span></div></td>' +
        '<td>' + t.cv + '%</td></tr>';
    }).join('');
    Array.prototype.forEach.call(document.querySelectorAll('tr.clk'), function (tr) {
      tr.addEventListener('click', function () { select(tr.getAttribute('data-k')); });
    });
  }

  function paintBar() {
    var groups = {};
    KEYS.forEach(function (k) {
      var g = SCENE[k].group || '기타';
      (groups[g] = groups[g] || []).push(k);
    });
    document.getElementById('grpbar').innerHTML = Object.keys(groups).sort().map(function (g) {
      return '<div class="grow"><span class="glab">' + g.replace(/^G\d\s*/, '') + '</span>' +
        groups[g].map(function (k) {
          return '<button data-k="' + k + '" aria-pressed="' + (k === cur) + '">' +
                 k.split('_')[1] + '</button>';
        }).join('') + '</div>';
    }).join('');
    Array.prototype.forEach.call(document.querySelectorAll('#grpbar button'), function (b) {
      b.addEventListener('click', function () { select(b.getAttribute('data-k')); });
    });
  }

  // ── 시각별 재생 ────────────────────────────────────────────────────────
  // 슬라이더 눈금 = 그 케이스에 있는 시각(30 초 간격) + 마지막 "평균".
  // 점수 상자·표는 공식 채점값(평균) 그대로 두고, 그림 넷과 이 시각 P10 만 바꾼다.
  var tlRange = document.getElementById('tlRange'), tlPlay = document.getElementById('tlPlay'),
      tlLabel = document.getElementById('tlLabel');
  var tlTimes = [], tlTimer = null;

  function frameOf(t, key) {                 // key 가 null 이면 평균 장
    return key === null ? t : { nx: t.nx, ny: t.ny, g: t.frames[key] };
  }
  function p10Of(g) {
    var v = [];
    g.forEach(function (row) { row.forEach(function (x) { if (x != null) v.push(x); }); });
    if (!v.length) return null;
    v.sort(function (a, b) { return a - b; });
    return v[Math.floor((v.length - 1) * 0.1)];
  }
  function paintFrames(k, key) {
    var d = SCENE[k], f0 = frameOf(d.tiers.t0, key), f1 = frameOf(d.tiers.t1, key);
    if (HAS3D && fieldPlanes.length === 2) {
      [f0, f1].forEach(function (f, i) {
        var tex = new THREE.CanvasTexture(imageOf(f));
        tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearFilter;
        fieldPlanes[i].material.map.dispose();
        fieldPlanes[i].material.map = tex;
        fieldPlanes[i].material.needsUpdate = true;
      });
      render();
    }
    drawMap(document.getElementById('m0'), f0);
    drawMap(document.getElementById('m1'), f1);
    var p0 = profiles(f0), p1 = profiles(f1);
    drawProfile(document.getElementById('px'),
      [{ v: p0.x, c: '#2C6E8F', n: '아래 단' }, { v: p1.x, c: '#A8501F', n: '위 단', d: '5 3' }],
      '← 베드 길이 2.4 m →');
    drawProfile(document.getElementById('py'),
      [{ v: p0.y, c: '#2C6E8F', n: '아래 단' }, { v: p1.y, c: '#A8501F', n: '위 단', d: '5 3' }],
      '← 베드 깊이 0.8 m →');
    if (key === null) {
      tlLabel.textContent = '평균 300 ~ 450 s';
    } else {
      var p = p10Of(f0.g);
      tlLabel.textContent = 't = ' + key + ' s · 이 시각 P10 아래 ' + (p === null ? '-' : p.toFixed(2));
    }
  }
  function tlKey() {                          // 슬라이더 위치 -> 시각 문자열 또는 null(평균)
    var i = +tlRange.value;
    return i < tlTimes.length ? tlTimes[i] : null;
  }
  function tlStop() {
    if (tlTimer) { clearInterval(tlTimer); tlTimer = null; }
    tlPlay.textContent = '▶';
  }
  function tlSetup(k) {
    tlStop();
    var fr = SCENE[k].tiers.t0.frames || {};
    tlTimes = Object.keys(fr).sort(function (a, b) { return a - b; });
    tlRange.max = tlTimes.length;             // 마지막 눈금 = 평균
    tlRange.value = tlTimes.length;
    var has = tlTimes.length > 0;
    tlRange.disabled = !has; tlPlay.disabled = !has;
    tlLabel.textContent = has ? '평균 300 ~ 450 s' : '시간별 원본 없음 — 평균 한 장만';
  }
  tlRange.addEventListener('input', function () { tlStop(); paintFrames(cur, tlKey()); });
  tlPlay.addEventListener('click', function () {
    if (tlTimer) { tlStop(); return; }
    if (+tlRange.value >= tlTimes.length) tlRange.value = 0;
    paintFrames(cur, tlKey());
    tlPlay.textContent = '❚❚';
    tlTimer = setInterval(function () {
      var i = +tlRange.value + 1;
      if (i >= tlTimes.length) i = 0;         // 평균 눈금은 건너뛰고 처음으로
      tlRange.value = i;
      paintFrames(cur, tlKey());
    }, 500);
  });

  function select(k) {
    if (!SCENE[k]) return;
    cur = k;
    Array.prototype.forEach.call(document.querySelectorAll('#grpbar button'), function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-k') === k));
    });
    Array.prototype.forEach.call(document.querySelectorAll('tr.clk'), function (tr) {
      tr.classList.toggle('sel', tr.getAttribute('data-k') === k);
    });
    var d = SCENE[k], t0 = d.tiers.t0, t1 = d.tiers.t1;

    build(k); render();
    tlSetup(k);

    document.getElementById('caption').textContent =
      k.replace('_', ' ') + ' — ' + cond(d) + ' · ' + d.label;

    document.getElementById('stats').innerHTML = [
      ['P10 아래', t0.p10.toFixed(2), t0.p10 < LO ? 'bad' : 'good'],
      ['P50 아래', t0.p50.toFixed(2), ''],
      ['P90 아래', t0.p90.toFixed(2), t0.p90 > HI ? 'bad' : 'good'],
      ['P10 위', t1.p10.toFixed(2), t1.p10 < LO ? 'bad' : 'good'],
      ['적정 비율', t0.band + '%', ''],
      ['고르기', t0.cv + '%', '']
    ].map(function (c) {
      return '<div class="stat ' + c[2] + '"><div class="k">' + c[0] + '</div><div class="v">' +
             c[1] + '</div></div>';
    }).join('');

    var vd = verdict(t0);
    var note = document.getElementById('casenote');
    note.className = 'note ' + (vd[1] === 'ok' ? 'good' : 'warn');
    note.innerHTML = '<b>' + vd[0] + '</b> — 아래 단에서 모자란 자리가 ' + t0.lo +
      ' %, 넘치는 자리가 ' + t0.hi + ' % 다. ' +
      (d.snaps < 6 ? '이 케이스는 300 초까지만 돌아 <b>스냅샷 한 장</b>만 들어갔다. 시간평균이 아니다.'
                   : '300 ~ 450 초 여섯 장을 시간평균한 값이다.');

    drawMap(document.getElementById('m0'), t0);
    drawMap(document.getElementById('m1'), t1);
    function sub(t) {
      var i = t.inner || {};
      return '베드 전체  P10 ' + t.p10.toFixed(2) + ' · P50 ' + t.p50.toFixed(2) +
             ' · P90 ' + t.p90.toFixed(2) + ' · 적정 ' + t.band + '%' +
             (i.p10 === undefined ? '' :
               '\n점선 안쪽  P10 ' + i.p10.toFixed(2) + ' · P50 ' + i.p50.toFixed(2) +
               ' · P90 ' + i.p90.toFixed(2) + ' · 적정 ' + i.band + '%');
    }
    document.getElementById('s0').textContent = sub(t0);
    document.getElementById('s1').textContent = sub(t1);

    var p0 = profiles(t0), p1 = profiles(t1);
    drawProfile(document.getElementById('px'),
      [{ v: p0.x, c: '#2C6E8F', n: '아래 단' }, { v: p1.x, c: '#A8501F', n: '위 단', d: '5 3' }],
      '← 베드 길이 2.4 m →');
    drawProfile(document.getElementById('py'),
      [{ v: p0.y, c: '#2C6E8F', n: '아래 단' }, { v: p1.y, c: '#A8501F', n: '위 단', d: '5 3' }],
      '← 베드 깊이 0.8 m →');

    function span(a) {
      var v = a.filter(function (x) { return x != null; });
      return v.length ? Math.max.apply(null, v) / Math.max(0.001, Math.min.apply(null, v)) : 0;
    }
    var rx = span(p0.x), ry = span(p0.y);
    var un = document.getElementById('unote');
    un.className = 'note ' + (t0.cv <= 35 ? 'good' : 'warn');
    un.innerHTML = '<b>변동계수 ' + t0.cv + ' %.</b> 길이 방향으로는 가장 센 줄이 가장 약한 줄의 ' +
      rx.toFixed(1) + ' 배, 깊이 방향으로는 ' + ry.toFixed(1) + ' 배다. ' +
      (ry > rx ? '<b>깊이 방향</b>이 더 심하다 — 제트가 가운데 한 줄로만 지나가고 앞뒤가 남는다.'
               : '<b>길이 방향</b>이 더 심하다 — 팬 앞이 세고 반대쪽 끝이 죽는다.');
  }

  if (HAS3D) {
    init3D();
    [['tRoom', gRoom], ['tAC', gAC], ['tCanopy', gCanopy], ['tFan', gFan], ['tGrid', gGrid]]
      .forEach(function (p) {
        var el = document.getElementById(p[0]);
        el.addEventListener('change', function () { p[1].visible = el.checked; render(); });
      });
  } else {
    // three.js 를 못 받았다. 3D 자리만 접고 지도·고르기·표는 그대로 쓴다.
    var stage = canvas.parentNode;
    stage.innerHTML = '<div style="padding:34px 20px;text-align:center;color:#c9d4cd;' +
      'font-size:14px;line-height:1.8">3D 는 three.js 를 인터넷에서 받아 그린다.<br>' +
      '지금은 못 받아 접었다 — 아래 <b>지도</b>와 <b>고르기</b>, 표는 그대로 볼 수 있다.</div>';
    document.querySelector('.toggles').style.display = 'none';
  }

  paintBar(); paintTable(); place(); select(cur);
  addEventListener('resize', render);
})();
