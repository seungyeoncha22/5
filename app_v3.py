"""노른자 v3 화면 (원래 app.py와 별개)

실행:  streamlit run app_v3.py
- 필수 입력: 가게, 후보 동네(서울 426개 동에서 검색, 최대 3곳)
- 선택 입력: 영업시간, 영업 요일, 월세, 객단가, 홍보 예산. 넣을수록 결과가 자세해진다
  (월세 -> 손익분기, 홍보 예산 -> 홍보 추천, 영업시간·요일 -> 시간대·요일 반영)
- 미리 계산된 결과가 있으면 그대로 쓰고, 없거나 조건이 다르면 엔진을 바로 돌린다 (runs/ 폴더에 저장)
- 페이지: ?page=home(첫 화면), result(결과), how(계산 방법). 개발용 정보는 ?debug=1
"""
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "frontend" / "data" / "real"
VIEW = ROOT / "frontend" / "v3" / "view.html"
RUNS = ROOT / "runs"
RADIUS_KM = 3.0
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
ENGINE_FILES = ["personas.csv", "reactions.json", "dong_stats.csv", "dongs.geojson", "ad_costs.json"]

st.set_page_config(page_title="노른자", layout="wide", initial_sidebar_state="collapsed")
page = st.query_params.get("page", "home")

# ---------- 화면 기본 스타일 ----------
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
html, body, [class*="css"], .stApp, input, textarea, button { font-family: 'Pretendard', sans-serif !important; }
.stApp { background: #FAFAF7; color: #111111; }
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
.block-container { padding: 0 0 48px 0 !important; max-width: 100% !important; }
.nr-top { background: #111111; height: 64px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; }
.nr-top a { color: #FFFFFF !important; text-decoration: none !important; }
.nr-logo { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 900; }
.nr-nav { display: flex; gap: 32px; font-size: 14px; }
.nr-nav a:hover, .nr-logo:hover { color: #F5B301 !important; }
.nr-search-title { width: calc(100% - 80px); max-width: 1280px; margin: 8px auto 0; font-size: 24px; font-weight: 900; }
.nr-hero .eyebrow { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.nr-hero .eyebrow i { width: 8px; height: 8px; border-radius: 999px; background: #E9A400; display: inline-block; }
.nr-hero h1 { font-size: 64px; line-height: 1.1; font-weight: 900; letter-spacing: -0.03em; margin: 14px 0 12px; color: #111111; }
.nr-hero p { font-size: 18px; line-height: 1.6; color: #111111; margin: 0; }
/* 입력 영역 */
.st-key-nr-search { box-sizing: border-box; width: calc(100% - 80px); max-width: 1280px; margin: 8px auto 0 !important;
  background: #FFFFFF; border: 1.5px solid #111111 !important; border-radius: 0 !important; padding: 24px 28px 20px !important; }
.st-key-nr-search div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; }
.stTextInput input, div[data-baseweb="select"] input, div[data-baseweb="select"] div, .stNumberInput input {
  font-family: 'Pretendard', sans-serif !important; font-size: 17px !important; font-weight: 400 !important; color: #111111; }
.stTextInput input { min-height: 56px; border-radius: 0 !important; }
.stTextInput input::placeholder { color: #8A8A8A !important; opacity: 1 !important; }
div[data-baseweb="select"] [aria-hidden="true"], div[data-baseweb="select"] input::placeholder { color: #8A8A8A !important; }
div[data-baseweb="input"], div[data-baseweb="select"] > div { border-radius: 0 !important; border-color: #111111 !important; }
div[data-baseweb="select"] > div { min-height: 56px; }
.stTextInput label p, .stMultiSelect label p, .stNumberInput label p, .stSelectbox label p, .stCheckbox label p {
  font-size: 15px !important; font-weight: 600 !important; color: #111111 !important; }
span[data-baseweb="tag"], .stMultiSelect [data-baseweb="tag"] { background-color: #111111 !important; border-radius: 0 !important; }
span[data-baseweb="tag"] span, span[data-baseweb="tag"] svg { color: #FFFFFF !important; fill: #FFFFFF !important; }
div[data-testid="stExpander"] details { border-radius: 0 !important; border: 1px solid #E0E0E0 !important; }
.stButton button { border-radius: 999px; height: 52px; padding: 0 36px; background: #F5B301 !important; color: #111111 !important;
  border: none; transition: background-color 200ms ease; }
.stButton button p { font-family: 'Pretendard', sans-serif !important; font-weight: 600 !important; font-size: 17px !important; letter-spacing: -0.01em; }
.stButton button:hover { background: #E5A500 !important; }
.stButton button:focus-visible { outline: 2px solid #111111; outline-offset: 2px; }
.nr-note { font-size: 14px; color: #595959; margin: 4px 0 0; }
/* 안내·오류 메시지도 검색 상자와 같은 폭으로 */
div[data-testid="stAlert"], div[data-testid="stNotification"] { box-sizing: border-box; width: calc(100% - 80px) !important;
  max-width: 1280px; margin: 12px auto 0 !important; }
</style>
<div class="nr-top">
  <a class="nr-logo" href="?page=home" target="_self">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="10" fill="#FFFFFF"/><circle cx="11" cy="11" r="5" fill="#F5B301"/></svg>
    노른자
  </a>
  <nav class="nr-nav"><a href="?page=how" target="_self">계산 방법</a></nav>
</div>
""", unsafe_allow_html=True)


# ---------- 데이터 ----------
def read_json(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


@st.cache_data
def load_dongs():
    """서울 426개 동: 화면 표시 이름 -> 동 코드 (같은 이름 동이 여러 구에 있어서 구 이름을 붙임)"""
    out = {}
    with open(DATA / "dong_stats.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            label = f"{row['dong']} · {row.get('gu') or ''}".strip(" ·")
            out[label] = row["dong_code"]
    return dict(sorted(out.items()))


@st.cache_data
def load_people():
    people = {}
    with open(DATA / "personas.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            people[int(row["id"])] = (float(row["lat"]), float(row["lng"]), row["dong_code"])
    return people


def km(a, b):
    dy = (a[0] - b[0]) * 111.0
    dx = (a[1] - b[1]) * 111.0 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def diag_summary(text):
    if not text:
        return None
    if "[요약]" in text:
        return text.split("[요약]", 1)[1].split("[", 1)[0].strip()
    return text.strip().split("\n")[0][:200]


def build_dong(r, steps_per_week):
    people = load_people()
    code = r["dong_code"]
    mine = [v for v in people.values() if v[2] == code]
    center = (sum(p[0] for p in mine) / len(mine), sum(p[1] for p in mine) / len(mine)) if mine else (37.55, 126.92)
    heard = {}
    for step, ids in enumerate(r.get("steps", [])):
        for i in ids:
            heard.setdefault(int(i), step // steps_per_week)
    dots = [[round(lat, 5), round(lng, 5), heard.get(pid, -1)] for pid, (lat, lng, _) in people.items()
            if pid in heard or km((lat, lng), center) <= RADIUS_KM]
    calib = read_json(DATA / f"calibration_demo_{code}.json")
    rev = read_json(DATA / f"revision_{code}.json") or {}
    bp = r.get("budget_plan") or {}
    hv = r.get("hub_vs_broad") or {}
    return {
        "code": code, "dong": r["dong"], "center": center, "dots": dots,
        "monthly": r.get("monthly_customers"), "breakeven": r.get("breakeven_week"),
        "weekly": r.get("weekly_visitors"), "range": r.get("visitors_range"),
        "channels": r.get("channel_total") or {},
        "promo": {"split": bp.get("split"), "discount": bp.get("open_discount"), "gain": bp.get("visitors_gain"),
                  "roas": bp.get("roas"), "payback": bp.get("payback_week"), "budget": bp.get("budget")} if bp else None,
        "hub": {"reach_hub": hv.get("reach_hub"), "reach_broad": hv.get("reach_broad"),
                "ratio": hv.get("per_person_ratio")} if hv else None,
        "presc": (r.get("prescriptions") or [None])[0],
        "summary": diag_summary(r.get("diagnosis")),
        "calib": {"reduction": calib.get("error_reduction")} if calib else None,
        "revision": rev.get("business_idea"),
        "detail": {
            "weekly": r.get("weekly_visitors"), "repromo": r.get("repromo"), "assumptions": r.get("assumptions") or {},
            "scenarios": r.get("scenarios") or [], "budget_plan": bp, "hub_vs_broad": hv, "hubs": r.get("hubs") or [],
            "channel_share": r.get("channel_share") or {}, "group_awareness": r.get("group_awareness") or {},
            "prescriptions": r.get("prescriptions") or [], "diagnosis": r.get("diagnosis"),
            "revision_changes": rev.get("changes") or [],
        },
    }


def load_validation():
    for cand in [DATA / "validation_log.json", ROOT / "validation_log.json", ROOT / "outputs" / "validation_log.json"]:
        v = read_json(cand, [])
        if v:
            return v if isinstance(v, list) else [v]
    return []


def precomputed(codes, opts):
    """조건 없이 미리 계산된 결과가 있는 동만 고른 경우 그대로 사용"""
    if any(v for v in opts.values()):
        return None
    out = []
    for c in codes:
        r = read_json(DATA / f"result_{c}.json")
        if not r or not r.get("weekly_visitors"):
            return None
        out.append(r)
    return out


def run_engine(codes, opts, idea):
    """조건에 맞게 엔진 실행. 같은 조건은 runs/<키>에 저장해 다시 쓰기"""
    key = hashlib.md5(json.dumps({"c": sorted(codes), "o": opts}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    folder = RUNS / key
    results = [read_json(folder / f"result_{c}.json") for c in codes]
    if all(results):
        return results, None
    folder.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        src, dst = DATA / name, folder / name
        if src.exists() and not dst.exists():
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy(src, dst)
    scenario = {"business_idea": idea, "candidate_dongs": codes, **opts}
    json.dump(scenario, open(folder / "scenario.json", "w", encoding="utf-8"), ensure_ascii=False)
    cmd = [sys.executable, str(ROOT / "engine" / "simulate.py"), "--data", f"runs/{key}", "--dongs", *codes]
    if not opts.get("budget"):
        cmd.append("--no-promo")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=900)
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout)[-1500:]
    return [read_json(folder / f"result_{c}.json") for c in codes], None


dong_map = load_dongs()
labels = list(dong_map.keys())
code_to_label = {v: k for k, v in dong_map.items()}
scenario0 = read_json(DATA / "scenario.json", {})
default_labels = [code_to_label[c] for c in ["1144066000", "1144071000", "1144069000"] if c in code_to_label]

# ---------- 첫 화면 제목 + 예시 캐러셀 ----------
weights = read_json(ROOT / "config" / "weights.json", {})
spw = weights.get("steps_per_week", 2)


def home_examples():
    recent = [read_json(DATA / f"result_{c}.json") for c in ["1144066000", "1144071000", "1144069000"]]
    return sorted([build_dong(r, spw) for r in recent if r and r.get("weekly_visitors")], key=lambda d: -(d["monthly"] or 0))


def render_view(view, extra, height):
    base = {"view": view, "dong_total": len(labels), "people_total": len(load_people()), "flags": {},
            "conditions": [], "dongs": [], "validation": None, "validation_all": []}
    base.update(extra)
    html = VIEW.read_text(encoding="utf-8").replace("__DATA__", json.dumps(base, ensure_ascii=False))
    components.html(html, height=height, scrolling=False)


if page == "home":
    examples = home_examples()
    render_view("hero", {"dongs": examples, "idea": scenario0.get("business_idea") or "디저트 카페"}, 680)

# ---------- 입력 (계산 방법·팀 화면에서는 숨김) ----------
go = False
opts = {"open_hours": None, "open_days": None, "rent": None, "avg_price": None, "budget": None}
if page in ("home", "result"):
    with st.container(key="nr-search"):
        c1, c2 = st.columns([1, 1])
        with c1:
            idea = st.text_input("가게 (필수)", value=st.session_state.get("idea", ""),
                                 placeholder="예) 20대 대학생 대상 합리적인 가격의 디저트 카페")
        with c2:
            picked = st.multiselect("후보 동네 (필수, 최대 3곳)", labels, default=st.session_state.get("picked", []),
                                    max_selections=3, placeholder="동 이름을 입력해 검색")
        with st.expander("상세 조건 (선택)"):
            st.markdown('<p class="nr-note">월세를 넣으면 손익분기, 홍보 예산을 넣으면 채널별 홍보 추천, 영업시간·요일을 넣으면 그 시간대 유동인구가 반영돼요. 비워두면 기본 시뮬레이션만 보여드려요.</p>', unsafe_allow_html=True)
            h1, h2, h3 = st.columns([1, 1, 2])
            with h1:
                use_hours = st.checkbox("영업시간 지정")
            with h2:
                start = st.selectbox("여는 시간", list(range(0, 24)), index=10, disabled=not use_hours, format_func=lambda h: f"{h}시")
            with h3:
                end = st.selectbox("닫는 시간", list(range(1, 25)), index=21, disabled=not use_hours, format_func=lambda h: f"{h}시")
            days = st.multiselect("영업 요일", DAYS, default=DAYS)
            n1, n2, n3 = st.columns(3)
            with n1:
                rent = st.number_input("월세 (만 원)", min_value=0, step=10, value=0, help="0이면 넣지 않은 것으로 봐요")
            with n2:
                price = st.number_input("객단가 (원)", min_value=0, step=500, value=0, help="0이면 동네 평균을 써요")
            with n3:
                budget = st.number_input("홍보 예산 (만 원)", min_value=0, step=10, value=0, help="0이면 홍보 추천을 계산하지 않아요")
        go = st.button("결과 보기")

    opts = {
        "open_hours": [start, end] if use_hours and end > start else None,
        "open_days": days if days and len(days) < 7 else None,
        "rent": rent * 10000 if rent else None,
        "avg_price": price or None,
        "budget": budget * 10000 if budget else None,
    }
    if go:
        if not idea.strip() or not picked:
            st.warning("가게와 후보 동네는 꼭 넣어주세요.")
            go = False
        else:
            st.session_state.update(idea=idea, picked=picked, opts=opts)
            st.query_params["page"] = "result"
            st.rerun()  # 첫 화면 제목·캐러셀 없이 결과 화면으로 다시 그림

# ---------- 결과 계산 ----------
validation = load_validation()
payload = {"view": page, "dong_total": len(labels), "people_total": len(load_people()),
           "validation": None, "validation_all": validation, "flags": {}, "conditions": [], "dongs": []}
if validation:
    v = validation[-1]
    payload["validation"] = {"rank_corr": v.get("rank_corr"), "target": v.get("target"), "round": v.get("round")}

if page == "result":
    picked = st.session_state.get("picked") or default_labels
    opts = st.session_state.get("opts") or opts
    idea = st.session_state.get("idea") or idea
    codes = [dong_map[l] for l in picked if l in dong_map]
    results = precomputed(codes, opts)
    if results is None:
        with st.spinner(f"{len(codes)}개 동네에 소식을 퍼뜨려 보는 중이에요. 동네당 30초쯤 걸려요."):
            results, err = run_engine(codes, opts, idea)
        if err:
            st.error("계산 중 문제가 생겼어요.")
            if st.query_params.get("debug") == "1":
                st.code(err)
            st.stop()
    payload["dongs"] = sorted([build_dong(r, spw) for r in results if r], key=lambda d: -(d["monthly"] or 0))
    payload["idea"] = idea
    payload["flags"] = {"promo": bool(opts.get("budget")), "breakeven": bool(opts.get("rent"))}
    cond = []
    if opts.get("open_hours"):
        cond.append(f"영업 {opts['open_hours'][0]}~{opts['open_hours'][1]}시")
    if opts.get("open_days"):
        cond.append("·".join(opts["open_days"]))
    if opts.get("rent"):
        cond.append(f"월세 {opts['rent'] // 10000:,}만 원")
    if opts.get("avg_price"):
        cond.append(f"객단가 {opts['avg_price']:,}원")
    if opts.get("budget"):
        cond.append(f"홍보 {opts['budget'] // 10000:,}만 원")
    payload["conditions"] = cond
elif page == "home":
    payload["dongs"] = examples
    payload["idea"] = scenario0.get("business_idea") or "디저트 카페"

html = VIEW.read_text(encoding="utf-8").replace("__DATA__", json.dumps(payload, ensure_ascii=False))
heights = {"home": 520, "result": 2300, "how": 1500}
components.html(html, height=heights.get(page, 1200), scrolling=False)

if st.query_params.get("debug") == "1":
    with st.expander("개발용 정보"):
        st.write({"page": page, "opts": opts, "가중치": weights.get("version"), "runs": str(RUNS)})
