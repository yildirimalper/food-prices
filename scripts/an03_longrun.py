"""Has the farm-gate share of the retail food price been falling for years,
or is 2026 unusual?

Farm gate  : FAOSTAT Producer Price Index for Türkiye (2014-2016 = 100), annual,
             aggregated across items as an unweighted median to resist outliers.
Retail     : Eurostat/TurkStat HICP food (CP011), annual average.
Both rebased to 2015 = 100 so the ratio is a pure relative-price measure."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT
OUT = ROOT/"output"; OUT.mkdir(exist_ok=True)

FOOD_ITEMS = None  # all items FAOSTAT reports for Türkiye

def main():
    fp = pd.read_csv(PROC/"tr_faostat_producer_prices.csv")
    ppi = fp[(fp.Element.str.contains("Producer Price Index")) &
             (fp.Months=="Annual value")][["Item","Year","Value"]].dropna()
    # median across items, then rebase to 2015
    farm = ppi.groupby("Year")["Value"].median()
    farm = 100*farm/farm.loc[2015]

    h = pd.read_csv(PROC/"tr_hicp_monthly.csv")
    idx = h[h.unit=="I15"].pivot_table(index="month", columns="coicop", values="value")
    yearly = idx.copy(); yearly["year"] = yearly.index.str[:4].astype(int)
    ann = yearly.groupby("year").mean()
    retail = 100*ann["CP011"]/ann.loc[2015,"CP011"]
    head   = 100*ann["TOTAL"]/ann.loc[2015,"TOTAL"]

    yrs = sorted(set(farm.index) & set(retail.index))
    yrs = [y for y in yrs if y>=2010]
    d = pd.DataFrame({"year":yrs,
                      "farm_gate_idx_2015_100":[farm[y] for y in yrs],
                      "retail_food_idx_2015_100":[retail[y] for y in yrs],
                      "headline_cpi_idx_2015_100":[head[y] for y in yrs]})
    d["retail_over_farm"] = d.retail_food_idx_2015_100/d.farm_gate_idx_2015_100
    d["farm_real_vs_cpi"] = d.farm_gate_idx_2015_100/d.headline_cpi_idx_2015_100
    d["retail_real_vs_cpi"] = d.retail_food_idx_2015_100/d.headline_cpi_idx_2015_100
    d.to_csv(OUT/"03_longrun_farm_vs_retail.csv", index=False)
    pd.set_option("display.width",200)
    print("=== Farm gate vs retail food, Türkiye (2015 = 100) ===")
    print(d.round(1).to_string(index=False))
    print("\nretail_over_farm  = how many units of retail food price per unit of farm-gate price.")
    print("                    rising -> the gap between shelf and field is widening.")
    print("farm_real_vs_cpi  = farm-gate prices deflated by headline CPI (farmers' terms of trade).")
    a,b = d.iloc[0], d.iloc[-1]
    print(f"\n{int(a.year)} -> {int(b.year)}: retail/farm ratio {a.retail_over_farm:.2f} -> {b.retail_over_farm:.2f} "
          f"({100*(b.retail_over_farm/a.retail_over_farm-1):+.0f}%)")
    print(f"{int(a.year)} -> {int(b.year)}: farm real terms of trade {a.farm_real_vs_cpi:.2f} -> {b.farm_real_vs_cpi:.2f} "
          f"({100*(b.farm_real_vs_cpi/a.farm_real_vs_cpi-1):+.0f}%)")

if __name__=="__main__":
    main()
