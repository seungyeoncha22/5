"""노른자 v3 화면 (원래 app.py와 별개)

실행:  streamlit run app_v3.py
- 결과 파일(frontend/data/real/result_{동코드}.json)을 읽어 화면에 보여준다. 엔진은 여기서 다시 돌리지 않는다.
- 입력 막대는 Streamlit 입력칸, 나머지 화면은 frontend/v3/view.html 하나에 데이터를 넣어 그린다.
- 개발용 정보는 주소 뒤에 ?debug=1 을 붙였을 때만 보인다.
"""
import csv
import json
import math
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "frontend" / "data" / "real"
VIEW = ROOT / "frontend" / "v3" / "view.html"
RADIUS_KM = 3.0

st.set_page_config(page_title="노른자", layout="wide", initial_sidebar_state="collapsed")

# ---------- 화면 기본 스타일 (Streamlit 티 지우기) ----------
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
html, body, [class*="css"], .stApp { font-family: 'Pretendard', sans-serif !important; }
.stApp { background: #FAFAF7; color: #111111; }
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stSidebar"],
[data-testid="collapsedControl"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
.block-container { padding: 0 0 48px 0 !important; max-width: 100% !important; }
.nr-top { background: #111111; color: #FFFFFF; height: 64px; display: flex; align-items: center;
          justify-content: space-between; padding: 0 40px; }
.nr-logo { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 900; }
.nr-nav { display: flex; gap: 32px; font-size: 14px; }
.nr-nav a { color: #FFFFFF; text-decoration: none; }
div[data-testid="stHorizontalBlock"] { padding: 24px 40px 8px; gap: 12px; }
.stTextInput input, div[data-baseweb="select"] > div { border-radius: 0 !important; border: 1.5px solid #111111 !important;
          background: #FFFFFF !important; min-height: 48px; font-size: 16px; }
.stTextInput label, .stMultiSelect label { font-size: 14px !important; color: #595959 !important; }
span[data-baseweb="tag"] { background: #111111 !important; border-radius: 0 !important; }
.stButton button { border-radius: 0; height: 48px; width: 100%; background: #F5B301; color: #111111;
          border: none; font-weight: 700; font-size: 16px; margin-top: 27px; transition: background-color 200ms ease; }
.stButton button:hover { background: #E5A500; color: #111111; }
.stButton button:focus-visible { outline: 2px solid #111111; outline-offset: 2px; }
</style>
<div class="nr-top">
  <div class="nr-logo">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="10" fill="#FFFFFF"/><circle cx="11" cy="11" r="5" fill="#F5B301"/></svg>
    노른자
  </div>
  <nav class="nr-nav"><a href="#how">계산 방법</a><a href="#list">동네 보기</a><a href="#team">팀</a></nav>
</div>
""", unsafe_allow_html=True)


# ---------- 데이터 읽기 ----------
def read_json(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


@st.cache_data
def load_results():
    out = {}
    for f in sorted(DATA.glob("result_*.json")):
        r = read_json(f)
        if r and r.get("weekly_visitors"):
            out[r["dong"]] = r
    return out


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
    """준혁 님 진단의 [요약] 부분만"""
    if not text:
        return None
    if "[요약]" in text:
        body = text.split("[요약]", 1)[1]
        return body.split("[", 1)[0].strip()
    return text.strip().split("\n")[0][:200]


@st.cache_data
def build_dong(r, steps_per_week):
    people = load_people()
    code = r["dong_code"]
    mine = [v for v in people.values() if v[2] == code]
    center = (sum(p[0] for p in mine) / len(mine), sum(p[1] for p in mine) / len(mine)) if mine else (37.55, 126.92)
    heard = {}
    for step, ids in enumerate(r.get("steps", [])):
        for i in ids:
            heard.setdefault(int(i), step // steps_per_week)
    dots = []
    for pid, (lat, lng, _) in people.items():
        if pid in heard or km((lat, lng), center) <= RADIUS_KM:
            dots.append([round(lat, 5), round(lng, 5), heard.get(pid, -1)])
    code_files = {
        "calib": read_json(DATA / f"calibration_demo_{code}.json"),
        "revision": read_json(DATA / f"revision_{code}.json"),
    }
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
        "calib": {"reduction": code_files["calib"].get("error_reduction")} if code_files["calib"] else None,
        "revision": code_files["revision"].get("business_idea") if code_files["revision"] else None,
    }


results = load_results()
weights = read_json(ROOT / "config" / "weights.json", {})
spw = weights.get("steps_per_week", 2)
scenario = read_json(DATA / "scenario.json", {})
validation = read_json(DATA / "validation_log.json", [])
val = validation[-1] if isinstance(validation, list) and validation else None

if not results:
    st.error("결과 파일이 없습니다. 먼저 엔진을 실행해 주세요.")
    st.stop()

# ---------- 입력 막대 ----------
names = list(results.keys())
c1, c2, c3 = st.columns([3, 3, 1])
with c1:
    idea = st.text_input("가게", value=scenario.get("business_idea", "20대 대학생 대상 디저트 카페"))
with c2:
    picked = st.multiselect("후보 동네", names, default=names[:3], max_selections=3)
with c3:
    go = st.button("결과 보기")

if go and picked:
    st.session_state["view"] = "result"
    st.session_state["picked"] = picked
view = st.session_state.get("view", "home")
picked = st.session_state.get("picked", picked) or names[:3]

# ---------- 화면 데이터 ----------
dongs = [build_dong(results[n], spw) for n in picked if n in results]
dongs.sort(key=lambda d: -(d["monthly"] or 0))
payload = {
    "view": view, "idea": idea, "dongs": dongs,
    "validation": {"rank_corr": val.get("rank_corr"), "target": val.get("target"), "round": val.get("round")} if val else None,
    "people_total": len(load_people()), "dong_total": 426,
}
html = VIEW.read_text(encoding="utf-8").replace("__DATA__", json.dumps(payload, ensure_ascii=False))
components.html(html, height=1500 if view == "home" else 1900, scrolling=False)

if st.query_params.get("debug") == "1":
    with st.expander("개발용 정보"):
        st.write({"결과 파일": names, "선택": picked, "가중치": weights.get("version")})
