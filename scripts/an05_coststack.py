"""What is actually pushing food prices up, if not the farm gate?

Builds every major non-farm cost in the food chain on a common basis:
annual % change to Sep-2026 and cumulative change since Dec-2025."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT=ROOT/"output"; OUT.mkdir(exist_ok=True)
REF="2026-09"; PREV="2025-09"; DEC="2025-12"

def chg(s, a, b):
    if a in s.index and b in s.index and pd.notna(s.get(a)) and pd.notna(s.get(b)):
        return 100*(s[a]/s[b]-1)
    return np.nan

def main():
    rows=[]
    cur=pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")
    def cv(s,m,p):
        r=cur[(cur.series==s)&(cur.measure==m)&(cur.period==p)]
        return float(r.value.iloc[0]) if len(r) else np.nan

    # --- farm inputs (TurkStat Tarim-GFE, latest published = Aug-2026) ---
    rows += [
      dict(block="Farm inputs", item="All agricultural inputs (Tarim-GFE)", yoy_pct=cv("Tarim-GFE","yoy_pct","2026-08"), ytd_pct=np.nan, source="TurkStat (Aug-26)"),
      dict(block="Farm inputs", item="  Energy & lubricants",               yoy_pct=cv("Tarim-GFE-energy","yoy_pct","2026-08"), ytd_pct=np.nan, source="TurkStat (Aug-26)"),
      dict(block="Farm inputs", item="  Fertiliser & soil improvers",       yoy_pct=cv("Tarim-GFE-fertiliser","yoy_pct","2026-08"), ytd_pct=np.nan, source="TurkStat (Aug-26)"),
      dict(block="Farm output", item="Farm-gate prices (Tarim-UFE)",        yoy_pct=cv("Tarim-UFE","yoy_pct","2026-09"), ytd_pct=cv("Tarim-UFE","vs_dec_prev_pct","2026-09"), source="TurkStat (Sep-26)"),
    ]

    # --- processing / packaging / energy (PPI) ---
    p=pd.read_csv(PROC/"tr_ppi_monthly.csv")
    pidx=p[p.unit=="I21"].pivot_table(index="month",columns="nace_r2",values="value")
    for c,l in [("C10","Food manufacturing"),("C101","  Meat processing"),("C105","  Dairy processing"),
                ("C106","  Grain milling"),("C107","  Bakery"),("C11","Beverage manufacturing"),
                ("C22","Plastic packaging"),("C17","Paper & board packaging"),("C23","Glass packaging"),
                ("MIG_NRG","Energy (producer prices)"),("C","All manufacturing")]:
        if c in pidx.columns:
            rows.append(dict(block="Processing & packaging", item=l,
                yoy_pct=chg(pidx[c],REF,PREV), ytd_pct=chg(pidx[c],REF,DEC), source="Eurostat/TurkStat PPI"))

    # --- retail & away-from-home services (HICP) ---
    h=pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx=h[h.unit=="I15"].pivot_table(index="month",columns="coicop",values="value")
    for c,l in [("CP011","Retail food"),("CP111","Restaurants & cafés"),
                ("CP041","Actual rents for housing"),("CP07","Transport"),
                ("CP045","Electricity, gas & other fuels"),("TOTAL","Headline CPI")]:
        if c in idx.columns:
            rows.append(dict(block="Downstream prices", item=l,
                yoy_pct=chg(idx[c],REF,PREV), ytd_pct=chg(idx[c],REF,DEC), source="Eurostat/TurkStat HICP"))

    # --- imported input costs in lira ---
    wb=pd.read_csv(PROC/"worldbank_commodity_monthly.csv").set_index("month")
    fx=pd.read_csv(PROC/"tr_fx_monthly.csv").set_index("month")["TRY_per_USD"]
    pick={"Maize (($/mt))":"Maize (feed)","Soybean meal (($/mt))":"Soybean meal (feed)",
          "Wheat, US HRW (($/mt))":"Wheat (world)","Urea, (Europe) (($/mt))":"Urea fertiliser",
          "DAP (($/mt))":"DAP fertiliser","Crude oil, Brent (($/bbl))":"Crude oil (Brent)",
          "Palm oil (($/mt))":"Palm oil","Sugar, world (($/kg))":"Sugar (world)"}
    for col,lab in pick.items():
        if col not in wb.columns: continue
        usd=pd.to_numeric(wb[col],errors="coerce")
        try_= usd*fx.reindex(usd.index)
        rows.append(dict(block="Imported inputs (USD)", item=lab,
            yoy_pct=chg(usd,REF,PREV), ytd_pct=chg(usd,REF,DEC), source="World Bank Pink Sheet"))
        rows.append(dict(block="Imported inputs (in lira)", item=lab+" in TRY",
            yoy_pct=chg(try_,REF,PREV), ytd_pct=chg(try_,REF,DEC), source="Pink Sheet x TRY/USD"))

    # --- lira and labour ---
    rows.append(dict(block="Macro drivers", item="TRY per USD (depreciation)",
        yoy_pct=chg(fx,REF,PREV), ytd_pct=chg(fx,REF,DEC), source="Eurostat FX"))
    mw=pd.read_csv(PROC/"tr_minwage.csv").set_index("half_year")["min_wage_try"]
    if "2026-S1" in mw.index and "2025-S1" in mw.index:
        rows.append(dict(block="Macro drivers", item="Statutory minimum wage",
            yoy_pct=100*(mw["2026-S1"]/mw["2025-S1"]-1),
            ytd_pct=100*(mw["2026-S1"]/mw.get("2025-S2",np.nan)-1), source="Eurostat (bi-annual)"))

    d=pd.DataFrame(rows)
    d.to_csv(OUT/"05_cost_stack.csv",index=False)
    pd.set_option("display.width",220); pd.set_option("display.max_rows",100)
    print(f"=== Cost stack, Türkiye, {REF} (annual %, and % since Dec-2025) ===")
    for b in d.block.unique():
        print(f"\n-- {b} --")
        print(d[d.block==b][["item","yoy_pct","ytd_pct","source"]].round(1).to_string(index=False))

if __name__=="__main__":
    main()
