"""What did the bumper fruit harvest actually buy the consumer?

Counterfactual: hold every other sub-group at its actual rate and ask what food
inflation would have been if fruit had merely tracked the rest of the basket."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT=ROOT/"output"
def main():
    d=pd.read_csv(OUT/"01_food_cpi_contributions.csv")
    tot=d.contribution_to_food_yoy_pp.sum()
    fruit=d[d.group=="Fruit & nuts"].iloc[0]
    rest=d[d.group!="Fruit & nuts"]
    rest_rate=rest.contribution_to_food_yoy_pp.sum()/ (rest.share_of_food_basket_pct.sum()/100)
    cf = rest.contribution_to_food_yoy_pp.sum() + fruit.share_of_food_basket_pct/100*rest_rate
    rows=[dict(scenario="Actual (Sep-2026)", food_inflation_pct=tot,
               fruit_rate_pct=fruit.yoy_pct, note="fruit deflating after a +60.8% harvest"),
          dict(scenario="If fruit had tracked the rest of the food basket",
               food_inflation_pct=cf, fruit_rate_pct=rest_rate,
               note="counterfactual, all other groups unchanged"),
          dict(scenario="Saving to the consumer", food_inflation_pct=cf-tot,
               fruit_rate_pct=np.nan, note="percentage points of food inflation avoided")]
    r=pd.DataFrame(rows); r.to_csv(OUT/"07_fruit_counterfactual.csv",index=False)
    pd.set_option("display.width",200); pd.set_option("display.max_colwidth",60)
    print("=== What the fruit harvest was worth ===")
    print(r.round(2).to_string(index=False))

    # farmers' terms of trade
    cur=pd.read_csv(ROOT/"data/curated/tuik_published_figures.csv")
    def cv(s,m,p):
        x=cur[(cur.series==s)&(cur.measure==m)&(cur.period==p)]
        return float(x.value.iloc[0]) if len(x) else np.nan
    out_,in_ = cv("Tarim-UFE","yoy_pct","2026-09"), cv("Tarim-GFE","yoy_pct","2026-08")
    tot_sq = 100*((1+out_/100)/(1+in_/100)-1)
    print(f"\n=== Farmers' terms of trade ===")
    print(f"Farm-gate output prices (Sep-26)      : {out_:+.1f}% y/y")
    print(f"Farm input prices (Aug-26)            : {in_:+.1f}% y/y")
    print(f"Terms of trade                        : {tot_sq:+.1f}%  <- real income squeeze per unit sold")
    pd.DataFrame([dict(output_yoy=out_,input_yoy=in_,terms_of_trade_pct=tot_sq)]).to_csv(
        OUT/"07_farmer_terms_of_trade.csv",index=False)
if __name__=="__main__": main()
