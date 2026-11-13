"""Fresh produce: does a good harvest reach the consumer?

(a) 2026 snapshot: production vs farm-gate price vs shelf price, fruit vs vegetables.
(b) 2018-2024 pass-through: for commodities where FAOSTAT reports a monthly
    farm-gate price and the HICP reports a matching retail category, track the
    ratio retail_index / farm_index. A rising ratio = the marketing margin is
    widening relative to the farm price."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT = ROOT/"output"; OUT.mkdir(exist_ok=True)

MONTHS = {m:i+1 for i,m in enumerate(
  ["January","February","March","April","May","June","July","August",
   "September","October","November","December"])}

# FAOSTAT item  ->  (HICP coicop, readable name)
PAIRS = {
 "Potatoes":                ("CP01175","Tubers & potatoes"),
 "Tomatoes":                ("CP01172","Fruit-bearing vegetables"),
 "Onions and shallots, dry (excluding dehydrated)": ("CP01174","Other fresh vegetables"),
 "Apples":                  ("CP01163","Stone & pome fruit"),
 "Raw milk of cattle":      ("CP01141","Raw & whole milk"),
 "Wheat":                   ("CP01112","Flour of cereals"),
 "Oranges":                 ("CP01162","Citrus fruit"),
 "Grapes":                  ("CP01165","Other fresh fruit"),
}

def main():
    cur = pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")
    h = pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx = h[h.unit=="I15"].pivot_table(index="month", columns="coicop", values="value")

    # ---------- (a) 2026 snapshot ----------
    def val(s,m,p):
        r=cur[(cur.series==s)&(cur.measure==m)&(cur.period==p)]
        return float(r.value.iloc[0]) if len(r) else np.nan
    def hicp_yoy(code,per="2026-09"):
        s=idx[code]; prev=f"2025-{per[5:]}"
        return 100*(s[per]/s[prev]-1) if per in s.index and prev in s.index else np.nan
    snap = pd.DataFrame([
      dict(group="Fruit (& nuts)",
           production_2026_yoy_pct=val("production-fruit","yoy_pct","2026"),
           farm_gate_signal="perennial crops -8.4% m/m; tropical/subtropical fruit -14.7% m/m (Sep-26)",
           retail_yoy_pct=hicp_yoy("CP0116"),
           contribution_to_food_inflation_pp=-0.09),
      dict(group="Vegetables (& pulses)",
           production_2026_yoy_pct=val("production-vegetables","yoy_pct","2026"),
           farm_gate_signal=f"vegetables/melons/roots +{val('Tarim-UFE-vegetables','yoy_pct','2026-09'):.1f}% y/y (Sep-26)",
           retail_yoy_pct=hicp_yoy("CP0117"),
           contribution_to_food_inflation_pp=5.58),
    ])
    snap.to_csv(OUT/"04a_fresh_produce_2026.csv", index=False)
    pd.set_option("display.width",250); pd.set_option("display.max_colwidth",70)
    print("=== (a) 2026: harvest vs farm price vs shelf price ===")
    print(snap.round(1).to_string(index=False))

    # ---------- (b) pass-through 2018-2024 ----------
    fp = pd.read_csv(PROC/"tr_faostat_producer_prices.csv")
    m = fp[(fp.Element=="Producer Price (LCU/tonne)") & (fp.Months!="Annual value")].copy()
    m["mnum"]=m.Months.map(MONTHS); m=m.dropna(subset=["mnum"])
    m["month"]=m.Year.astype(int).astype(str)+"-"+m.mnum.astype(int).astype(str).str.zfill(2)

    rows=[]
    for item,(code,label) in PAIRS.items():
        if code not in idx.columns: continue
        f = m[m.Item==item].set_index("month")["Value"].sort_index()
        if len(f)<36: continue
        both = pd.DataFrame({"farm":f, "retail":idx[code]}).dropna()
        both = both[(both.index>="2018-01")&(both.index<="2024-12")]
        if len(both)<36: continue
        base = both.iloc[:12].mean()          # 2018 average = 100
        both["farm_i"]   = 100*both.farm/base.farm
        both["retail_i"] = 100*both.retail/base.retail
        both["ratio"]    = both.retail_i/both.farm_i
        first = both.iloc[:12].ratio.mean(); last = both.iloc[-12:].ratio.mean()
        rows.append(dict(commodity=item, retail_category=label,
            farm_2018_to_2024_pct=100*(both.iloc[-12:].farm_i.mean()/100-1),
            retail_2018_to_2024_pct=100*(both.iloc[-12:].retail_i.mean()/100-1),
            margin_ratio_2018=first, margin_ratio_2024=last,
            margin_widening_pct=100*(last/first-1), n_months=len(both)))
        both.reset_index().rename(columns={"index":"month"}).assign(commodity=item)\
            .to_csv(OUT/f"04b_passthrough_{code}.csv", index=False)
    d=pd.DataFrame(rows).sort_values("margin_widening_pct",ascending=False)
    d.to_csv(OUT/"04b_passthrough_summary.csv", index=False)
    print("\n=== (b) 2018 -> 2024: farm-gate vs retail, same commodity ===")
    print("(margin_widening_pct > 0 means the shelf price outran the farm price)")
    print(d.round(1).to_string(index=False))

if __name__=="__main__":
    main()
