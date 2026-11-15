"""AI 수정안 전후 비교

수정 전: frontend/data/real/result_{동코드}.json (원래 반응으로 계산한 결과)
수정 후: reactions_revised_{동코드}.json (수정한 아이디어로 다시 받은 설문)으로 같은 조건에서 다시 계산
결과:   frontend/data/real/revision_compare_{동코드}.json, 화면에 표로도 출력

실행 (저장소 맨 위에서):  python engine/compare_revision.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "frontend" / "data" / "real"
RUNS = ROOT / "runs"
CODES = ["1144066000", "1144069000", "1144071000"]
FILES = ["personas.csv", "dong_stats.csv", "dongs.geojson", "ad_costs.json", "scenario.json"]


def load(p):
    return json.load(open(p, encoding="utf-8"))


def main():
    rows = []
    for code in CODES:
        before_p, revised_p = DATA / f"result_{code}.json", DATA / f"reactions_revised_{code}.json"
        if not before_p.exists() or not revised_p.exists():
            print(f"{code}: 수정 전 결과나 재설문 파일이 없어 건너뜀")
            continue
        folder = RUNS / f"revised_{code}"
        folder.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            if (DATA / name).exists():
                shutil.copy(DATA / name, folder / name)
        shutil.copy(revised_p, folder / "reactions.json")       # 반응만 수정안 것으로 바꿈
        env = dict(os.environ, PYTHONIOENCODING="utf-8")  # 윈도우에서 한글 출력이 깨져 오류 나는 것 방지
        proc = subprocess.run([sys.executable, str(ROOT / "engine" / "simulate.py"), "--data", f"runs/revised_{code}",
                               "--dongs", code, "--no-promo"], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env)
        if proc.returncode != 0:
            print(f"{code}: 계산 실패\n{proc.stderr[-800:]}")
            continue
        b, a = load(before_p), load(folder / f"result_{code}.json")
        rev = load(DATA / f"revision_{code}.json") if (DATA / f"revision_{code}.json").exists() else {}
        ga_b, ga_a = b.get("group_awareness") or {}, a.get("group_awareness") or {}
        groups = sorted(set(ga_b) | set(ga_a), key=lambda g: (ga_a.get(g, 0) - ga_b.get(g, 0)), reverse=True)
        out = {
            "dong_code": code, "dong": b["dong"], "business_idea_after": rev.get("business_idea"),
            "before": {"monthly_customers": b.get("monthly_customers"), "visitors": b.get("visitors"),
                       "breakeven_week": b.get("breakeven_week"), "weekly_visitors": b.get("weekly_visitors")},
            "after": {"monthly_customers": a.get("monthly_customers"), "visitors": a.get("visitors"),
                      "breakeven_week": a.get("breakeven_week"), "weekly_visitors": a.get("weekly_visitors")},
            "group_awareness_change": {g: {"before": ga_b.get(g), "after": ga_a.get(g)} for g in groups},
            "note": "같은 조건(영업시간·월세·객단가)에서 시민 반응만 수정안 설문으로 바꿔 다시 계산",
        }
        json.dump(out, open(DATA / f"revision_compare_{code}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        mb, ma = out["before"]["monthly_customers"] or 0, out["after"]["monthly_customers"] or 0
        rows.append((b["dong"], mb, ma, out["before"]["breakeven_week"], out["after"]["breakeven_week"], groups[:2]))
    print("\n동네      3달째 월 손님 (전 -> 후)      손익분기 (전 -> 후)   인지율이 가장 오른 집단")
    for dong, mb, ma, bb, ba, top in rows:
        diff = (ma - mb) / mb * 100 if mb else 0
        print(f"{dong:<8} {mb:>6,} -> {ma:>6,}명 ({diff:+.0f}%)   {bb or '-'} -> {ba or '-'}주 차        {', '.join(top)}")


if __name__ == "__main__":
    main()
