"""Where in each product chain does the price run ahead?

For each food line, line up the stages that exist in the data and look at which
step's price is growing fastest. A stage growing faster than the one before it is
widening its gross margin on that product."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT=ROOT/"output"; OUT.mkdir(exist_ok=True)
REF,PREV,DEC="2026-09","2025-09","2025-12"

def main():
    h=pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx=h[h.unit=="I15"].pivot_table(index="month",columns="coicop",values="value")
    p=pd.read_csv(PROC/"tr_ppi_monthly.csv")
    pidx=p[p.unit=="I21"].pivot_table(index="month",columns="nace_r2",values="value")
    cur=pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")
    def cv(s,m,pd_):
        r=cur[(cur.series==s)&(cur.measure==m)&(cur.period==pd_)]
        return float(r.value.iloc[0]) if len(r) else np.nan
    def yoy(df,c):
        if c not in df.columns: return np.nan
        s=df[c]
        return 100*(s[REF]/s[PREV]-1) if REF in s.index and PREV in s.index and pd.notna(s.get(REF)) and pd.notna(s.get(PREV)) else np.nan

    chains=[
      dict(chain="Meat",        farm=np.nan,                         farm_note="livestock (Tarim-UFE sub, m/m +1.0%)",
           processing=yoy(pidx,"C101"), retail=yoy(idx,"CP0112")),
      dict(chain="Dairy & eggs",farm=np.nan,                         farm_note="raw milk (regulated reference price)",
           processing=yoy(pidx,"C105"), retail=yoy(idx,"CP0114")),
      dict(chain="Bread & cereals", farm=np.nan,                     farm_note="wheat (TMO intervention price)",
           processing=yoy(pidx,"C106"), retail=yoy(idx,"CP0111")),
      dict(chain="Bakery (sub)",  farm=np.nan,                       farm_note="-",
           processing=yoy(pidx,"C107"), retail=yoy(idx,"CP01113")),
      dict(chain="Oils & fats",  farm=np.nan,                        farm_note="oilseeds/olives",
           processing=yoy(pidx,"C104"), retail=yoy(idx,"CP0115")),
      dict(chain="Vegetables",   farm=cv("Tarim-UFE-vegetables","yoy_pct","2026-09"), farm_note="Tarim-UFE vegetables/melons/roots",
           processing=np.nan,            retail=yoy(idx,"CP0117")),
      dict(chain="Fruit & nuts", farm=np.nan,                        farm_note="perennial crops falling (-8.4% m/m)",
           processing=np.nan,            retail=yoy(idx,"CP0116")),
      dict(chain="Non-alc beverages", farm=np.nan,                   farm_note="-",
           processing=yoy(pidx,"C11"),  retail=yoy(idx,"CP012")),
    ]
    d=pd.DataFrame(chains)
    d["retail_minus_processing_pp"]=d.retail-d.processing
    d["retail_minus_farm_pp"]=d.retail-d.farm
    d=d[["chain","farm","farm_note","processing","retail",
         "retail_minus_processing_pp","retail_minus_farm_pp"]]
    d.to_csv(OUT/"06_stage_margins.csv",index=False)
    pd.set_option("display.width",230); pd.set_option("display.max_colwidth",44)
    print(f"=== Annual % change by stage, {REF} ===")
    print("(retail_minus_processing_pp > 0: the shelf price is outrunning the factory gate)")
    print(d.round(1).to_string(index=False))

    # farm share of the food basket that is 'fresh, directly farm-linked'
    w=pd.read_csv(PROC/"tr_hicp_weights.csv")
    wt=w[w.year==2026].set_index("coicop")["weight_permille"]
    if wt.empty: wt=w[w.year==w.year.max()].set_index("coicop")["weight_permille"]
    food_w=wt.get("CP01",np.nan)
    fresh=sum(wt.get(c,0) for c in ["CP0116","CP0117"])
    print(f"\n=== How much of the food basket is fresh produce? ===")
    print(f"Food & non-alc beverages weight : {food_w:.1f} per mille of the whole CPI basket")
    print(f"Fruit + vegetables weight       : {fresh:.1f} per mille")
    print(f"Fresh produce = {100*fresh/food_w:.1f}% of the food basket; "
          f"the other {100-100*fresh/food_w:.1f}% is processed food, livestock products and beverages.")
    pd.DataFrame([dict(food_weight_permille=food_w, fresh_produce_permille=fresh,
                       fresh_share_of_food_pct=100*fresh/food_w)]).to_csv(
        OUT/"06_basket_structure.csv",index=False)

if __name__=="__main__":
    main()
