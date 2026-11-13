"""Türkiye HICP (ECOICOP-2018) monthly indices, annual rates and item weights.

Eurostat republishes TurkStat's harmonised consumer price collection, which is the
only machine-readable source giving Türkiye's food basket at 5-digit detail and
running to the current month.
"""
import json, sys, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import fetch_json, RAW, PROC

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

def jsonstat_to_frame(d):
    dims = d["id"]
    cats = {k: sorted(d["dimension"][k]["category"]["index"],
                      key=d["dimension"][k]["category"]["index"].get) for k in dims}
    labels = {k: d["dimension"][k]["category"].get("label", {}) for k in dims}
    sizes = [len(cats[k]) for k in dims]
    rows = []
    for flat, val in d["value"].items():
        i = int(flat); coord = []
        for s in reversed(sizes):
            coord.append(i % s); i //= s
        coord.reverse()
        rec = {k: cats[k][c] for k, c in zip(dims, coord)}
        rec["value"] = val
        rows.append(rec)
    df = pd.DataFrame(rows)
    if "coicop18" in df.columns:
        df["coicop_label"] = df["coicop18"].map(labels["coicop18"])
    return df

def main():
    out = []
    for unit in ["I15", "RCH_A", "I25"]:
        url = (f"{API}/prc_hicp_minr?format=JSON&geo=TR&unit={unit}"
               f"&sinceTimePeriod=2010-01")
        print(f"[eurostat] prc_hicp_minr unit={unit}")
        d = fetch_json(url, RAW / f"eurostat_hicp_minr_TR_{unit}.json")
        if "error" in d:
            print("   !", d["error"]); continue
        df = jsonstat_to_frame(d)
        print(f"   {len(df):,} obs, {df['coicop18'].nunique()} categories, "
              f"{df['time'].min()}..{df['time'].max()}")
        out.append(df)
    hicp = pd.concat(out, ignore_index=True)
    hicp = hicp.rename(columns={"coicop18": "coicop", "time": "month"})
    hicp = hicp[["month", "coicop", "coicop_label", "unit", "value"]].sort_values(
        ["coicop", "unit", "month"])
    PROC.mkdir(parents=True, exist_ok=True)
    hicp.to_csv(PROC / "tr_hicp_monthly.csv", index=False)
    print(f"-> tr_hicp_monthly.csv  {len(hicp):,} rows")

    # item weights (per mille of total basket), annual
    print("[eurostat] prc_hicp_iw (item weights)")
    d = fetch_json(f"{API}/prc_hicp_iw?format=JSON&geo=TR&sinceTimePeriod=2015",
                   RAW / "eurostat_hicp_iw_TR.json")
    w = jsonstat_to_frame(d).rename(columns={"coicop18": "coicop", "time": "year"})
    w = w[["year", "coicop", "coicop_label", "value"]].rename(columns={"value": "weight_permille"})
    w.to_csv(PROC / "tr_hicp_weights.csv", index=False)
    print(f"-> tr_hicp_weights.csv  {len(w):,} rows, years {w['year'].min()}..{w['year'].max()}")

if __name__ == "__main__":
    main()
