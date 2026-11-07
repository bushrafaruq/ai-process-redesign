"""Generate the synthetic request log, the current-state baseline, the opportunity
ranking and the business case. Every number quoted in docs/ comes from here.

    python -m case_study.run
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from . import assumptions as A

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
DATA = ROOT / "data"


# --------------------------------------------------------------------------
# 1. Synthetic six-month request log (as-is process)
# --------------------------------------------------------------------------

def next_inbox_check(t: datetime, rng) -> datetime:
    """When will a coordinator next look at an email/portal request received at t?"""
    start, end = A.DESK_HOURS
    if t.hour < start:
        t0 = t.replace(hour=start, minute=0)
    elif t.hour >= end:
        t0 = (t + timedelta(days=1)).replace(hour=start, minute=0)
    else:
        t0 = t
    return t0 + timedelta(minutes=float(rng.uniform(0, A.INBOX_CHECK_INTERVAL_MIN)))


def generate_log(rng) -> list[dict]:
    rows = []
    start = datetime(2025, 8, 1)
    cats, cat_p = zip(*A.CATEGORY_MIX.items())
    chans, chan_p = zip(*A.CHANNEL_MIX.items())
    pris, pri_p = zip(*A.TRUE_PRIORITY_MIX.items())
    # arrival hour profile: quiet overnight, peaks morning and evening
    hour_w = np.array([1, .5, .3, .3, .3, .5, 1, 2, 3, 3.5, 3.5, 3, 3, 3, 3, 3, 3.5, 4, 4.5, 4.5, 4, 3.5, 2.5, 1.5])
    hour_p = hour_w / hour_w.sum()
    n_id = 0
    for d in range(A.DAYS):
        day = start + timedelta(days=d)
        lam = A.MEAN_REQUESTS_PER_DAY * (A.SEPTEMBER_UPLIFT if day.month == 9 else 1.0)
        for _ in range(rng.poisson(lam)):
            n_id += 1
            hour = rng.choice(24, p=hour_p)
            t = day + timedelta(hours=int(hour), minutes=int(rng.integers(0, 60)))
            ch = rng.choice(chans, p=chan_p)
            cat = rng.choice(cats, p=cat_p)
            pri = "P1" if cat == "safety_security" else rng.choice(pris, p=pri_p)
            # walk-ins and phone calls are triaged on the spot if the desk is open
            desk_open = A.DESK_HOURS[0] <= t.hour < A.DESK_HOURS[1]
            if ch in ("walk_in", "phone") and desk_open:
                triaged = t + timedelta(minutes=float(rng.uniform(1, 10)))
            elif ch in ("walk_in", "phone"):
                triaged = t + timedelta(minutes=float(rng.uniform(5, 30)))   # night porter
            else:
                triaged = next_inbox_check(t, rng)
            misrouted = rng.random() < A.MISROUTE_RATE
            logged_pri = pri if rng.random() >= A.PRIORITY_INCONSISTENCY else rng.choice(
                [p for p in pris if p != pri])
            reroute_h = float(rng.uniform(2, 24)) if misrouted else 0.0
            chased = rng.random() < A.CHASER_RATE
            rows.append({
                "request_id": f"R{n_id:05d}", "received_at": t.isoformat(timespec="minutes"),
                "channel": ch, "category": cat, "true_priority": pri, "logged_priority": logged_pri,
                "minutes_to_triage": round((triaged - t).total_seconds() / 60, 1),
                "misrouted_first_time": int(misrouted), "hours_lost_to_reroute": round(reroute_h, 1),
                "resident_chased": int(chased),
            })
    return rows


# --------------------------------------------------------------------------
# 2. Current-state baseline KPIs
# --------------------------------------------------------------------------

def baseline(rows: list[dict]) -> dict:
    mt = np.array([r["minutes_to_triage"] for r in rows])
    p1 = np.array([r["minutes_to_triage"] for r in rows if r["true_priority"] == "P1"])
    p1_inbox = np.array([r["minutes_to_triage"] for r in rows
                         if r["true_priority"] == "P1" and r["channel"] in ("email", "portal")])
    months = A.DAYS / 30.4
    n = len(rows)
    mis = sum(r["misrouted_first_time"] for r in rows)
    chased = sum(r["resident_chased"] for r in rows)
    effort_h = (n * A.TRIAGE_MINUTES_PER_REQUEST + mis * A.REWORK_MINUTES_PER_MISROUTE
                + chased * A.MINUTES_PER_CHASER) / 60
    return {
        "requests_total": n,
        "requests_per_month": round(n / months),
        "median_minutes_to_triage": round(float(np.median(mt)), 0),
        "p90_minutes_to_triage": round(float(np.percentile(mt, 90)), 0),
        "p1_median_minutes_to_triage": round(float(np.median(p1)), 0),
        "p1_via_inbox_median_minutes": round(float(np.median(p1_inbox)), 0),
        "p1_via_inbox_over_60_min_pct": round(float((p1_inbox > 60).mean() * 100), 1),
        "misrouted_pct": round(mis / n * 100, 1),
        "priority_inconsistent_pct": round(
            sum(r["true_priority"] != r["logged_priority"] for r in rows) / n * 100, 1),
        "chased_pct": round(chased / n * 100, 1),
        "coordinator_triage_hours_per_month": round(effort_h / months, 0),
        "share_received_out_of_hours_pct": round(sum(
            not (A.DESK_HOURS[0] <= datetime.fromisoformat(r["received_at"]).hour < A.DESK_HOURS[1])
            for r in rows) / n * 100, 1),
        "share_inbox_channels_pct": round(sum(r["channel"] in ("email", "portal") for r in rows) / n * 100, 1),
    }


# --------------------------------------------------------------------------
# 3. Opportunity scoring
# --------------------------------------------------------------------------

WEIGHTS = {"value": 0.30, "feasibility": 0.20, "data_readiness": 0.15, "risk": 0.20, "adoption": 0.15}

# Scores 1-5. For "risk", 5 = LOW risk (so a higher score is always better).
OPPORTUNITIES = [
    ("AI triage & routing with human approval", 5, 4, 4, 4, 4,
     "Biggest pain point; human approval keeps risk low"),
    ("Instant acknowledgement with expected response time", 3, 5, 5, 5, 5,
     "Simple template; cuts resident chasers"),
    ("Automated weekly KPI report", 3, 5, 4, 5, 4,
     "Uses the structured data triage creates"),
    ("Duplicate / same-issue detection", 3, 3, 3, 4, 4,
     "Needs a few weeks of structured data first"),
    ("Resident self-service FAQ assistant", 3, 3, 2, 3, 3,
     "Needs a maintained knowledge base; answer-quality risk"),
    ("Sentiment and complaint escalation", 2, 4, 3, 3, 3,
     "Useful but secondary to getting routing right"),
    ("Predictive maintenance from repeat faults", 4, 2, 1, 4, 3,
     "High value later; no asset-level history yet"),
    ("Fully autonomous resolution (AI books contractors)", 4, 2, 2, 1, 2,
     "Spend and safety decisions without a person: not now"),
]


def score_opportunities() -> list[dict]:
    out = []
    for name, v, f, d, r, a, note in OPPORTUNITIES:
        s = v * WEIGHTS["value"] + f * WEIGHTS["feasibility"] + d * WEIGHTS["data_readiness"] \
            + r * WEIGHTS["risk"] + a * WEIGHTS["adoption"]
        out.append({"opportunity": name, "value": v, "feasibility": f, "data_readiness": d,
                    "risk_low_is_5": r, "adoption": a, "weighted_score": round(s, 2), "note": note})
    out.sort(key=lambda x: x["weighted_score"], reverse=True)
    for i, o in enumerate(out):
        o["wave"] = "Wave 1 (now)" if i < 3 else ("Wave 2 (3-6 months)" if o["weighted_score"] >= 3.0 else "Not now")
    return out


# --------------------------------------------------------------------------
# 4. Business case
# --------------------------------------------------------------------------

def load_eval() -> dict:
    files = sorted(OUT.glob("eval_*.json"))
    llm = [f for f in files if "llm" in f.name and "fallback" not in f.name]
    path = llm[0] if llm else OUT / "eval_baseline_keywords_v1.json"
    return json.loads(path.read_text())


def business_case(base: dict, ev: dict) -> dict:
    n_month = base["requests_per_month"]
    share = ev["review_mode_share"]
    q, f, e = share.get("QUICK_APPROVE", 0), share.get("FULL_REVIEW", 0), share.get("ESCALATE_NOW", 0)
    future_triage_min = q * A.QUICK_APPROVE_MINUTES + f * A.FULL_REVIEW_MINUTES + e * A.ESCALATE_MINUTES
    # Future misroutes: a coordinator checks every proposal. Conservative assumption: they
    # catch only half of the agent's category errors, so residual = (1 - accuracy) x 0.5.
    future_misroute = min(A.MISROUTE_RATE, (1 - ev["category_accuracy"]) * A.REVIEW_CATCH_MISS_RATE)
    misroute_now = base["misrouted_pct"] / 100
    chaser_now = base["chased_pct"] / 100

    def monthly_hours(triage_min, misroute, chaser_rate):
        return n_month * (triage_min + misroute * A.REWORK_MINUTES_PER_MISROUTE
                          + chaser_rate * A.MINUTES_PER_CHASER) / 60

    now_h = monthly_hours(A.TRIAGE_MINUTES_PER_REQUEST, misroute_now, chaser_now)
    fut_h = monthly_hours(future_triage_min, future_misroute, chaser_now * (1 - A.CHASER_REDUCTION))

    build = A.BUILD_DAYS * A.DAY_RATE_EUR
    run_month = A.RUN_COST_PER_MONTH_EUR + n_month * A.LLM_COST_PER_REQUEST_EUR \
        + A.SUPPORT_DAYS_PER_QUARTER * A.DAY_RATE_EUR / 3
    scen = {}
    for name, mult in A.SCENARIOS.items():
        saved_h = (now_h - fut_h) * mult
        gross = saved_h * A.LOADED_COST_PER_HOUR_EUR
        net_month = gross - run_month
        scen[name] = {
            "hours_saved_per_month": round(saved_h, 0),
            "fte_equivalent": round(saved_h / 150, 2),
            "gross_value_per_year_eur": round(gross * 12, -2),
            "run_cost_per_year_eur": round(run_month * 12, -2),
            "net_value_per_year_eur": round(net_month * 12, -2),
            "payback_months": round(build / net_month, 1) if net_month > 0 else None,
            "three_year_net_eur": round(net_month * 36 - build, -2),
        }
    return {
        "source_eval_model": ev["model"],
        "current_hours_per_month": round(now_h, 0),
        "future_hours_per_month": round(fut_h, 0),
        "current_triage_min_per_request": A.TRIAGE_MINUTES_PER_REQUEST,
        "future_triage_min_per_request": round(future_triage_min, 2),
        "current_misroute_pct": base["misrouted_pct"],
        "future_misroute_pct": round(future_misroute * 100, 1),
        "chaser_pct_now": base["chased_pct"],
        "chaser_pct_future": round(base["chased_pct"] * (1 - A.CHASER_REDUCTION), 1),
        "p1_minutes_to_triage_future_target": A.FUTURE_TRIAGE_DELAY_MIN,
        "one_off_build_cost_eur": build,
        "scenarios": scen,
    }


# --------------------------------------------------------------------------
# 5. Charts
# --------------------------------------------------------------------------

def charts(rows: list[dict], base: dict, bc: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # time to triage by channel
    fig, ax = plt.subplots(figsize=(7, 4))
    chans = list(A.CHANNEL_MIX)
    data = [[r["minutes_to_triage"] for r in rows if r["channel"] == c] for c in chans]
    ax.boxplot(data, tick_labels=[c.replace("_", "-") for c in chans], showfliers=False)
    ax.set_ylabel("Minutes from arrival to triage")
    ax.set_title("Current state: time to triage by channel (synthetic, 6 months)")
    fig.tight_layout()
    fig.savefig(OUT / "chart_time_to_triage_by_channel.png", dpi=150)
    plt.close(fig)

    # effort waterfall-ish bar
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["Current", "Future (base)"], [bc["current_hours_per_month"], bc["future_hours_per_month"]],
           color=["#9aa5b1", "#2f6fdf"])
    for i, v in enumerate([bc["current_hours_per_month"], bc["future_hours_per_month"]]):
        ax.text(i, v + 3, f"{v:.0f} h", ha="center")
    ax.set_ylabel("Coordinator hours per month")
    ax.set_title("Triage, rework and chaser effort")
    fig.tight_layout()
    fig.savefig(OUT / "chart_effort_current_vs_future.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rng = np.random.default_rng(A.SEED)
    OUT.mkdir(exist_ok=True)
    rows = generate_log(rng)
    write_csv(DATA / "synthetic_request_log.csv", rows)
    base = baseline(rows)
    opps = score_opportunities()
    write_csv(OUT / "opportunity_scores.csv", opps)
    bc = business_case(base, load_eval())
    charts(rows, base, bc)
    (OUT / "current_state_kpis.json").write_text(json.dumps(base, indent=2))
    (OUT / "business_case.json").write_text(json.dumps(bc, indent=2))
    print(json.dumps({"current_state": base, "business_case": bc}, indent=2))
    for o in opps:
        print(f'{o["weighted_score"]:.2f}  {o["wave"]:22s} {o["opportunity"]}')


if __name__ == "__main__":
    main()
