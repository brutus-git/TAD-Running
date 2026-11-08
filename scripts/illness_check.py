#!/usr/bin/env python3
"""Morning illness check: score last night's recovery data against a 7-night baseline.

Usage:
  python3 scripts/illness_check.py --hrv hrv.json --rhr rhr.json --out <illness-json> [--today YYYY-MM-DD]

--hrv / --rhr are the raw answers of Kailo's context_get_hrv and context_get_heart_rate
(period last_30_days). Optional --resp / --spo2 take a JSON list of {"date", "value"} if a
source for those ever becomes available. The output file is rewritten; its "history" list
is carried over from the existing file (one entry per night, last 60 kept).
Never invents a number: anything missing is marked unavailable.
"""
import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone

METRICS = [
    # key, name, unit, illness direction (+1 up / -1 down), full-scale range, weight
    ("rhr", "Resting heart rate", "bpm", 1, 7.0, 30),
    ("hrv", "Overnight HRV", "ms", -1, 15.0, 25),
    ("resp", "Sleeping respiration", "br/min", 1, 3.0, 25),
    ("spo2", "Overnight blood oxygen", "%", -1, 3.0, 20),
]
FLAG_AT = 0.35
BANDS = [(25, "Clear"), (45, "Watch"), (65, "Elevated"), (85, "High"), (101, "Very likely")]
ADVICE = {
    "Clear": "Train as planned today.",
    "Watch": "Train as planned, but hold back on intensity and look again tomorrow.",
    "Elevated": "Keep it easy today: Zone 2 only, no intervals or long run.",
    "High": "Rest today: skip the run and put sleep and fluids first.",
    "Very likely": "Take the day off entirely and watch for symptoms.",
}


def load(path):
    with open(path) as f:
        return json.load(f)


def series_from_kailo(answer, list_key, date_key, value_key):
    if isinstance(answer, str):
        answer = json.loads(answer)
    recs = answer.get(list_key)
    if not isinstance(recs, list):
        raise SystemExit(f"Answer has no {list_key}: keys {list(answer)}")
    return {r[date_key]: float(r[value_key]) for r in recs if r.get(value_key) is not None}


def d(s):
    return date.fromisoformat(s)


def evaluate(series, night):
    """Per-metric results for one night (a date)."""
    out = []
    for key, name, unit, direction, rng, weight in METRICS:
        row = {"key": key, "name": name, "unit": unit, "weight": weight, "range": rng,
               "direction": "up" if direction > 0 else "down", "available": False,
               "last": None, "baseline": None, "diff": None, "dev": None, "flagged": False,
               "days": 0, "reason": ""}
        s = series.get(key)
        if s is None:
            row["reason"] = "Not in the Garmin data Kailo shares."
            out.append(row)
            continue
        days = sum(1 for i in range(15) if (night - timedelta(days=i)).isoformat() in s)
        prev = [s[k] for k in ((night - timedelta(days=i)).isoformat() for i in range(1, 8)) if k in s]
        row["days"] = days
        if night.isoformat() not in s:
            row["reason"] = "No reading for this night."
        elif days < 4:
            row["reason"] = "Fewer than 4 nights of data in the last 15."
        elif not prev:
            row["reason"] = "No data in the 7 nights before."
        else:
            last = s[night.isoformat()]
            base = sum(prev) / len(prev)
            diff = last - base
            dev = min(1.0, max(0.0, direction * diff / rng))
            row.update(available=True, last=last, baseline=round(base, 2), diff=round(diff, 2),
                       dev=round(dev, 4), flagged=dev > FLAG_AT)
        out.append(row)
    return out


def score(rows):
    ok = [r for r in rows if r["available"]]
    if len(ok) < 2:
        return {"score": None, "band": None, "used": len(ok), "flags": None, "raw": None, "mult": None}
    raw = sum(r["weight"] * r["dev"] for r in ok) / sum(r["weight"] for r in ok)
    flags = sum(r["flagged"] for r in ok)
    mult = 0.5 if flags == 0 else 0.6 if flags == 1 else min(1.3, 1.0 + 0.15 * (flags - 2))
    sc = min(100, round(raw * mult * 100))
    band = next(name for top, name in BANDS if sc < top)
    return {"score": sc, "band": band, "used": len(ok), "flags": flags, "raw": round(raw, 4), "mult": mult}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hrv", required=True)
    ap.add_argument("--rhr", required=True)
    ap.add_argument("--resp")
    ap.add_argument("--spo2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--today", help="Today's local date (America/Los_Angeles), YYYY-MM-DD")
    ap.add_argument("--backfill", type=int, default=0, help="Also score this many earlier nights into history")
    a = ap.parse_args()

    series = {
        "hrv": series_from_kailo(load(a.hrv), "hrv_records", "calendar_date", "last_night_avg_ms"),
        "rhr": series_from_kailo(load(a.rhr), "heart_rate_records", "date", "resting_hr_bpm"),
    }
    for key, path in (("resp", a.resp), ("spo2", a.spo2)):
        if path:
            series[key] = {r["date"]: float(r["value"]) for r in load(path) if r.get("value") is not None}

    dates = sorted(set().union(*[set(s) for s in series.values()]))
    if not dates:
        raise SystemExit("No data at all from Kailo.")
    night = d(dates[-1])
    prior = night - timedelta(days=1)

    m_last, m_prior = evaluate(series, night), evaluate(series, prior)
    s_last, s_prior = score(m_last), score(m_prior)
    two_high = all(s["score"] is not None and s["score"] >= 65 for s in (s_last, s_prior))

    history = []
    if os.path.exists(a.out):
        try:
            history = load(a.out).get("history", [])
        except (ValueError, OSError):
            history = []
    hist = {h["date"]: h for h in history}
    nights = [(prior, s_prior), (night, s_last)]
    nights += [(night - timedelta(days=i), score(evaluate(series, night - timedelta(days=i)))) for i in range(2, 2 + a.backfill)]
    for nd, s in nights:
        if s["score"] is not None:
            hist[nd.isoformat()] = {"date": nd.isoformat(), "score": s["score"], "band": s["band"],
                                    "used": s["used"], "flags": s["flags"]}
    history = sorted(hist.values(), key=lambda h: h["date"])[-60:]

    missing = [r["name"] for r in m_last if not r["available"]]
    out = {
        "updated": a.today or night.isoformat(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "night": night.isoformat(),
        "synced": (a.today is None) or (night.isoformat() == a.today),
        **s_last,
        "advice": ADVICE[s_last["band"]] if s_last["band"] else
                  "Not enough data to score: fewer than two metrics are available. Missing: " + ", ".join(missing) + ".",
        "two_high": two_high,
        "prior": {"night": prior.isoformat(), **s_prior},
        "metrics": m_last,
        "missing": missing,
        "history": history,
        "method": {
            "baseline": "Mean of the 7 nights before last night, last night excluded.",
            "flag_at": FLAG_AT,
            "multiplier": "x0.5 no flags, x0.6 one, x1.0 two, x1.15 three, x1.3 four",
            "bands": "0-24 Clear, 25-44 Watch, 45-64 Elevated, 65-84 High, 85-100 Very likely",
            "source": "Garmin via Kailo (context_get_hrv, context_get_heart_rate)",
        },
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(json.dumps({k: out[k] for k in ("night", "synced", "score", "band", "used", "flags", "two_high")}))
    print(json.dumps({"prior": out["prior"]}))
    for r in m_last:
        print(r["key"], r["available"], r["last"], r["baseline"], r["diff"], r["dev"], r["flagged"], r["reason"])


if __name__ == "__main__":
    main()
