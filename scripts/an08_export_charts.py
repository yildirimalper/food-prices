"""Export chart-ready JSON for the report page."""
import sys, json, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT=ROOT/"output"

def main():
    j={}
    # 1. cost stack, ranked
    cs=pd.read_csv(OUT/"05_cost_stack.csv")
    keep=cs[cs.block.isin(["Farm inputs","Farm output","Processing & packaging",
                           "Downstream prices","Macro drivers","Imported inputs (in lira)"])].copy()
    keep=keep.dropna(subset=["yoy_pct"])
    drop={"All manufacturing","Headline CPI","Bakery (sub)"}
    keep=keep[~keep.item.isin(drop)]
    keep["item"]=keep.item.str.strip()
    j["cost_stack"]=[dict(label=r.item,value=round(r.yoy_pct,1),block=r.block)
                     for r in keep.sort_values("yoy_pct",ascending=False).itertuples()]

    # 2. contributions
    c=pd.read_csv(OUT/"01_food_cpi_contributions.csv")
    j["contributions"]=[dict(group=r.group, share=round(r.share_of_food_basket_pct,1),
                             rate=round(r.yoy_pct,1), contrib=round(r.contribution_to_food_yoy_pp,2))
                        for r in c.itertuples()]

    # 3. chain path, cumulative since Dec-2025 (monthly)
    h=pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx=h[h.unit=="I15"].pivot_table(index="month",columns="coicop",values="value")
    p=pd.read_csv(PROC/"tr_ppi_monthly.csv")
    pidx=p[p.unit=="I21"].pivot_table(index="month",columns="nace_r2",values="value")
    cur=pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")
    farm={r.period:r.value for r in cur[(cur.series=="Tarim-UFE")&(cur.measure=="vs_dec_prev_pct")].itertuples()}
    months=[f"2026-{m:02d}" for m in range(1,10)]
    def cum(df,c,m):
        if c not in df.columns or m not in df.index or "2025-12" not in df.index: return None
        s=df[c]
        return round(100*(s[m]/s["2025-12"]-1),1) if pd.notna(s.get(m)) else None
    j["chain"]=dict(months=months,
        farm=[farm.get(m) for m in months],
        mfg=[cum(pidx,"C10",m) for m in months],
        retail=[cum(idx,"CP011",m) for m in months],
        eatout=[cum(idx,"CP111",m) for m in months])

    # 4. fruit vs vegetables
    j["fresh"]=[
      dict(group="Fruit & nuts", production=60.8, farm=None, retail=-1.0,
           note="farm-gate perennial crops falling"),
      dict(group="Vegetables", production=-0.8, farm=61.1, retail=39.6,
           note="farm-gate rose faster than the shelf")]

    # 5. long run
    lr=pd.read_csv(OUT/"03_longrun_farm_vs_retail.csv")
    j["longrun"]=[dict(year=int(r.year), ratio=round(r.retail_over_farm,3),
                       tot=round(r.farm_real_vs_cpi,3)) for r in lr.itertuples()]

    # 6. headline numbers
    j["headline"]=dict(
      food_yoy=27.6, headline_yoy=29.7, farm_yoy=12.9, farm_input_yoy=30.3,
      food_ytd=21.8, farm_ytd=7.0, mfg_ytd=20.4, eatout_ytd=24.7,
      terms_of_trade=-13.3, fruit_saving_pp=3.03, fresh_share=23.5,
      fruit_production=60.8, veg_production=-0.8, fruit_retail=-1.0, veg_retail=39.6,
      tuik_food_oct=27.73, tuik_headline_oct=29.77)

    (OUT/"charts.json").write_text(json.dumps(j,indent=1))
    print("-> output/charts.json")
    print(json.dumps(j["headline"],indent=1))
    print("\ncost stack rows:",len(j["cost_stack"]))
    for r in j["cost_stack"][:6]: print("  ",r["label"],r["value"])
if __name__=="__main__": main()
