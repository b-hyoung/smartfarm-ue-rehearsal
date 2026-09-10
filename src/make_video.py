"""구운 프레임에 시간·범례를 얹고 GIF / MP4 로 묶는다.

왜 범례를 굽나
    색만 보고는 "파랗다 = 몇 도"인지 알 수 없다. 범례 없는 컬러맵은 그림일 뿐
    데이터가 아니다. 시간 표시도 마찬가지 — 프레임 번호로는 900초 중 어디인지 모른다.

입력
    out/anim/f_NN.png            ue/sf_bake_anim.py 가 구운 원본
    data/frames/manifest.json    프레임 -> 실제 시각(초)

출력
    out/anim/lab_NN.png          범례·시간 얹은 프레임
    out/smartfarm-flow.gif
    out/smartfarm-flow.mp4       (ffmpeg 있으면)

실행
    py -m src.make_video
"""
from __future__ import annotations

import csv
import json
import os
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIM = os.path.join(REPO, "out", "anim")
OUT = os.path.join(REPO, "out")

TMIN, TMAX = 20.4, 28.9     # ue/sf_geom.py 와 반드시 같아야 한다
# 재생 1초 = 실제 30초 (UE 시퀀스와 같은 배속). 900초 -> 30초.
# 프레임을 균등 간격으로 붙이면 (a) 5초짜리라 볼 시간이 없고
# (b) CFD 프레임 간격이 60~70초로 균일하지 않아 시간이 고르게 안 흐른다.
SPEEDUP = 30.0
FPS = 30


STOPS = [
    (0.00, (0.06, 0.09, 0.50)),   # 남색  — 제일 참 (20.4C)
    (0.28, (0.10, 0.40, 0.95)),   # 파랑
    (0.46, (0.15, 0.80, 0.85)),   # 청록
    (0.62, (0.65, 0.88, 0.22)),   # 연두
    (0.80, (0.98, 0.70, 0.10)),   # 호박
    (1.00, (0.88, 0.09, 0.06)),   # 빨강 — 제일 더움 (28.9C)
]
# ★ 파랑을 0.20 -> 0.28 로 늦추고 청록을 0.40 -> 0.46 으로 밀었다.
#   그 전에는 900초 시점(방 평균 23.5C = 램프의 36%)이 청록에 걸려서
#   "다 식었는데 왜 파랗지 않냐"가 됐다. 이제 아래쪽 1/3 이 확실히 파랑이다.


def _ramp(fr):
    """구간 선형보간. 파랑-흰-빨강 발산형은 중간이 흰색이라,
    방 평균온도 근처가 전부 흰색으로 뭉개져서 공간 차이가 안 보였다.
    가운데에도 색이 계속 바뀌는 램프로 바꾼다."""
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if fr <= b:
            t = (fr - a) / (b - a) if b > a else 0.0
            return tuple(ca[i] + (cb[i] - ca[i]) * t for i in range(3))
    return STOPS[-1][1]


def temp_rgb(tc, quantize=None):
    if quantize:
        tc = round(tc / quantize) * quantize
    fr = (tc - TMIN) / (TMAX - TMIN)
    fr = max(0.0, min(1.0, fr))
    c = _ramp(fr)
    # UE 는 리니어 색공간, PNG 는 sRGB → 감마를 씌워야 화면색과 같아 보인다
    return tuple(int(255 * (c[i] ** (1 / 2.2))) for i in range(3))


def font(size):
    for name in ("malgun.ttf", "malgunsl.ttf", "arial.ttf"):
        p = os.path.join(r"C:\Windows\Fonts", name)
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_probe_11():
    """A/B/C/D 의 1.1 m 온도 시계열. {지점: [(t, T), ...]}"""
    path = os.path.join(REPO, "data", "probes.csv")
    if not os.path.isfile(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if abs(float(r["z"]) - 1.1) > 1e-6:
                continue
            out.setdefault(r["point"], []).append((float(r["t_s"]),
                                                   float(r["T_C"])))
    for k in out:
        out[k].sort()
    return out


def draw_probe_chart(d, W, series, t_now):
    """A/B/C/D 온도 그래프 + 현재 시각 커서.

    숫자를 3D 장면 안에 박으면 눈이 거기로 쏠려 색 분포를 안 본다.
    장면은 색으로 보고, 정확한 값은 이 패널에서 읽는다 — 역할을 나눈다.

    선은 전부 회색 한 가지로 그리고 **현재 값 점만** 온도색으로 찍는다.
    선마다 다른 색을 주면 화면에 색 의미가 둘이 되어 서로 오독한다.
    """
    if not series:
        return
    f_mid, f_sm = font(22), font(19)
    PX, PY, PW, PH = W - 500, 40, 460, 250
    d.rectangle([PX, PY, PX + PW, PY + PH], fill=(0, 0, 0, 165))
    d.text((PX + 16, PY + 10), "A/B/C/D 온도 (높이 1.1 m)",
           font=f_mid, fill=(235, 238, 245))

    L, R = PX + 52, PX + PW - 108          # 그래프 좌우
    Tp, B = PY + 44, PY + PH - 34         # 그래프 상하
    tmax = 900.0
    vals = [v for s_ in series.values() for _, v in s_]
    lo, hi = min(vals), max(vals)
    lo, hi = math.floor(lo - 0.5), math.ceil(hi + 0.5)

    def sx(t):
        return L + (R - L) * min(t, tmax) / tmax

    def sy(v):
        return B - (B - Tp) * (v - lo) / float(hi - lo)

    # 눈금
    for v in range(int(lo), int(hi) + 1, 2):
        y = sy(v)
        d.line([(L, y), (R, y)], fill=(58, 62, 70))
        d.text((PX + 16, y - 10), "%d" % v, font=f_sm, fill=(170, 175, 185))
    for tt in (0, 300, 600, 900):
        x = sx(tt)
        d.line([(x, Tp), (x, B)], fill=(58, 62, 70))
        d.text((x - 14, B + 6), "%d" % tt, font=f_sm, fill=(170, 175, 185))
    d.text((R + 12, B + 6), "초", font=f_sm, fill=(170, 175, 185))

    marks = []
    for name in ("A", "B", "C", "D"):
        s_ = series.get(name)
        if not s_:
            continue
        pts = [(sx(t), sy(v)) for t, v in s_ if t <= tmax]
        if len(pts) > 1:
            d.line(pts, fill=(150, 155, 165), width=2)
        cur = min(s_, key=lambda kv: abs(kv[0] - t_now))
        marks.append([name, sx(cur[0]), sy(cur[1]), cur[1]])

    # B 와 D 는 대칭이라 값이 소수점까지 같다 → 라벨이 겹친다. 같은 값은 합치고,
    # 그래도 가까우면 위아래로 밀어낸다.
    merged = []
    for m in sorted(marks, key=lambda r: r[2]):
        if merged and abs(merged[-1][3] - m[3]) < 0.05:
            merged[-1][0] += "/" + m[0]
        else:
            merged.append(m)
    for i in range(1, len(merged)):
        if merged[i][2] - merged[i - 1][2] < 24:
            merged[i][2] = merged[i - 1][2] + 24

    for name, cx, cy, val in marks:
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=temp_rgb(val),
                  outline=(255, 255, 255))
    for name, cx, cy, val in merged:
        d.text((R + 10, cy - 11), "%s %.1f" % (name, val),
               font=f_sm, fill=(235, 238, 245))

    x = sx(t_now)
    d.line([(x, Tp), (x, B)], fill=(240, 210, 90), width=2)


def annotate(img, t_s, idx, n, series=None, mock=False):
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    f_big, f_mid, f_sm = font(44), font(24), font(20)

    # 시간
    d.rectangle([28, 24, 430, 150], fill=(0, 0, 0, 150))
    d.text((44, 34), "t = %d초 / 900초" % round(t_s), font=f_big, fill=(255, 255, 255))
    d.text((44, 92), "냉방 시작 후 경과 · 프레임 %d/%d" % (idx + 1, n),
           font=f_sm, fill=(190, 195, 205))

    # ⚠ 목데이터 표기 — 진짜 결과로 오해되면 안 된다
    if mock:
        d.rectangle([440, 24, 900, 66], fill=(120, 60, 0, 200))
        d.text((454, 32), "임시 목데이터 — vane25 CFD 계산 중, 완료 시 교체",
               font=f_sm, fill=(255, 225, 170))

    # 진행 막대
    x0, x1, y = 44, 414, 132
    d.rectangle([x0, y, x1, y + 7], fill=(70, 74, 84))
    d.rectangle([x0, y, x0 + int((x1 - x0) * (t_s / 900.0)), y + 7],
                fill=(240, 210, 90))

    # 온도 컬러바
    bx, by, bw, bh = W - 360, H - 108, 300, 22
    d.rectangle([bx - 16, by - 44, bx + bw + 16, by + bh + 40], fill=(0, 0, 0, 150))
    for i in range(bw):
        tc = TMIN + (TMAX - TMIN) * i / float(bw - 1)
        # 단면과 같은 0.5K 띠로 그려야 화면과 범례가 같은 규칙이 된다
        d.line([(bx + i, by), (bx + i, by + bh)], fill=temp_rgb(tc, 0.5))
    d.rectangle([bx, by, bx + bw, by + bh], outline=(210, 214, 222))
    d.text((bx, by - 36), "바람 색 = 온도 (°C)", font=f_mid, fill=(235, 238, 245))
    for v in (21, 23, 25, 27, 28):
        px = bx + int(bw * (v - TMIN) / (TMAX - TMIN))
        d.line([(px, by + bh), (px, by + bh + 6)], fill=(210, 214, 222))
        d.text((px - 14, by + bh + 8), "%d" % v, font=f_sm, fill=(215, 219, 227))

    # 크기 = 속도
    d.rectangle([28, H - 168, 600, H - 30], fill=(0, 0, 0, 150))
    d.text((44, H - 160), "온도 단면 2장 — 수평 1.1 m + 수직(에어컨 통과)",
           font=f_mid, fill=(235, 238, 245))
    d.text((44, H - 128), "화살표 = 바람 (길이 = 속도 0~0.45 m/s, 무늬가 흐름 방향)",
           font=f_sm, fill=(190, 195, 205))
    d.text((44, H - 100), "굵은 관 = 급기가 실제로 지나간 길(유선)",
           font=f_sm, fill=(190, 195, 205))
    d.text((44, H - 72), "회색 기둥 = A/B/C/D 측정 위치 (값은 우상단 그래프)",
           font=f_sm, fill=(190, 195, 205))

    draw_probe_chart(d, W, series or {}, t_s)
    return img


def main():
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    frames = man["frames"]
    series = load_probe_11()
    outs = []
    for i, meta in enumerate(frames):
        src = os.path.join(ANIM, "f_%02d.png" % meta["frame"])
        if not os.path.isfile(src):
            print("없음:", src)
            continue
        img = Image.open(src).convert("RGB")
        img = annotate(img, meta["time_s"], i, len(frames), series,
                       mock="MOCK" in str(man.get("source", "")).upper())
        dst = os.path.join(ANIM, "lab_%02d.png" % meta["frame"])
        img.save(dst)
        outs.append(dst)
    print("라벨 프레임 %d장" % len(outs))

    # 각 프레임을 **다음 프레임까지의 실제 시간** 만큼 물린다
    times = [float(m["time_s"]) for m in frames]
    dur = []
    for i in range(len(times)):
        if i + 1 < len(times):
            dt = times[i + 1] - times[i]
        else:
            dt = times[-1] - times[-2]          # 마지막은 직전 간격만큼
        dur.append(int(dt / SPEEDUP * 1000))
    print("총 재생 %.1f초 (실제 %.0f초 / %.0f배속)"
          % (sum(dur) / 1000.0, times[-1], SPEEDUP))

    ims = [Image.open(p).convert("RGB").resize((1280, 720), Image.LANCZOS)
           for p in outs]
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=192) for im in ims]
    gif = os.path.join(OUT, "smartfarm-flow.gif")
    pal[0].save(gif, save_all=True, append_images=pal[1:], duration=dur, loop=0,
                optimize=True)
    print("GIF %.1f MB -> %s" % (os.path.getsize(gif) / 1e6, gif))

    ff = shutil.which("ffmpeg")
    if ff:
        mp4 = os.path.join(OUT, "smartfarm-flow.mp4")
        # 프레임마다 길이가 다르므로 concat demuxer 로 duration 을 준다
        lst = os.path.join(ANIM, "_concat.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for p_, d_ in zip(outs, dur):
                f.write("file '" + p_.replace(chr(92), "/") + "'" + chr(10))
                f.write("duration %.3f" % (d_ / 1000.0) + chr(10))
            f.write("file '" + outs[-1].replace(chr(92), "/") + "'" + chr(10))
        cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", lst,
               "-vf", "scale=1280:-2,fps=%d" % FPS,
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            print("MP4 %.1f MB -> %s" % (os.path.getsize(mp4) / 1e6, mp4))
        else:
            print("ffmpeg 실패:", r.stderr.decode(errors="replace")[-400:])
    else:
        print("ffmpeg 없음 — GIF 만 생성")


if __name__ == "__main__":
    main()
