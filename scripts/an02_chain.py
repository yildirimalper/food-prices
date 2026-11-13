"""The farm-to-shelf wedge.

Stage 1  farm gate  : TurkStat Tarim-UFE (agricultural producer prices)
Stage 2  factory    : Eurostat/TurkStat domestic PPI, NACE C10 'manufacture of food products'
Stage 3  shelf      : Eurostat/TurkStat HICP CP011 'food'
Stage 3b away-from-home: HICP CP111 food & beverage serving services
"""
import sys, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT = ROOT/"output"; OUT.mkdir(exist_ok=True)

def main():
    h = pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx = h[h.unit=="I15"].pivot_table(index="month", columns="coicop", values="value")
    p = pd.read_csv(PROC/"tr_ppi_monthly.csv")
    pidx = p[p.unit=="I21"].pivot_table(index="month", columns="nace_r2", values="value")
    cur = pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")

    def g(series, measure, period):
        r = cur[(cur.series==series)&(cur.measure==measure)&(cur.period==period)]
        return float(r.value.iloc[0]) if len(r) else None

    rows=[]
    for per in ["2026-06","2026-07","2026-08","2026-09"]:
        prev=f"2025-{per[5:]}"; dec="2025-12"
        def pc(df,c):
            if c not in df.columns: return (None,None)
            s=df[c]
            yoy = 100*(s[per]/s[prev]-1) if per in s.index and prev in s.index and pd.notna(s.get(per)) and pd.notna(s.get(prev)) else None
            ytd = 100*(s[per]/s[dec]-1)  if per in s.index and dec  in s.index and pd.notna(s.get(per)) and pd.notna(s.get(dec))  else None
            return yoy,ytd
        f_yoy, f_ytd = g("Tarim-UFE","yoy_pct",per), g("Tarim-UFE","vs_dec_prev_pct",per)
        m_yoy, m_ytd = pc(pidx,"C10")
        r_yoy, r_ytd = pc(idx,"CP011")
        s_yoy, s_ytd = pc(idx,"CP111")
        rows.append(dict(month=per,
            farm_gate_yoy=f_yoy, food_mfg_yoy=m_yoy, retail_food_yoy=r_yoy, eating_out_yoy=s_yoy,
            farm_gate_ytd=f_ytd, food_mfg_ytd=m_ytd, retail_food_ytd=r_ytd, eating_out_ytd=s_ytd))
    d=pd.DataFrame(rows)
    d["wedge_retail_minus_farm_yoy"]=d.retail_food_yoy-d.farm_gate_yoy
    d["wedge_retail_minus_farm_ytd"]=d.retail_food_ytd-d.farm_gate_ytd
    d["wedge_retail_minus_mfg_yoy"]=d.retail_food_yoy-d.food_mfg_yoy
    d.to_csv(OUT/"02_price_chain.csv", index=False)
    pd.set_option("display.width",220)
    print("=== Farm gate -> factory -> shelf, annual % change ===")
    print(d[["month","farm_gate_yoy","food_mfg_yoy","retail_food_yoy","eating_out_yoy",
             "wedge_retail_minus_farm_yoy"]].round(1).to_string(index=False))
    print("\n=== Same, cumulative since December 2025 (year to date) ===")
    print(d[["month","farm_gate_ytd","food_mfg_ytd","retail_food_ytd","eating_out_ytd",
             "wedge_retail_minus_farm_ytd"]].round(1).to_string(index=False))

    # longer view of the manufacturing stage
    print("\n=== Food-chain PPI branches, annual % change (Sep 2026) ===")
    br={"C10":"Manufacture of food products","C101":"Meat processing","C105":"Dairy products",
        "C104":"Vegetable & animal oils/fats","C106":"Grain mill products","C107":"Bakery & farinaceous",
        "C108":"Other food products","C11":"Beverages","C2015":"Fertilisers & nitrogen compounds",
        "C17":"Paper & paper products","C22":"Rubber & plastic (packaging)","C23":"Glass & non-metallic",
        "D35":"Electricity, gas, steam","MIG_NRG":"Energy (MIG)","C":"Total manufacturing"}
    out=[]
    for c,l in br.items():
        if c in pidx.columns and "2026-09" in pidx.index and "2025-09" in pidx.index:
            s=pidx[c]
            if pd.notna(s.get("2026-09")) and pd.notna(s.get("2025-09")):
                out.append(dict(nace=c,branch=l,yoy_pct=100*(s["2026-09"]/s["2025-09"]-1),
                                ytd_pct=100*(s["2026-09"]/s["2025-12"]-1)))
    b=pd.DataFrame(out).sort_values("yoy_pct",ascending=False)
    b.to_csv(OUT/"02_ppi_branches.csv",index=False)
    print(b.round(1).to_string(index=False))

if __name__=="__main__":
    main()
