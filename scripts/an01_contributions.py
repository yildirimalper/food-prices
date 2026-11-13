"""Which parts of the food basket actually produce Türkiye's food inflation?

Decomposes the annual food-group inflation rate into the contribution of each
sub-group: contribution_i = w_i/W_food * (rate_i), with weights from the HICP
item-weight file (per mille of the whole basket)."""
import sys, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import PROC, ROOT

OUT = ROOT / "output"; OUT.mkdir(exist_ok=True)
REF = "2026-09"      # last month of the Eurostat panel for Türkiye

SUB = {  # COICOP-2018 sub-groups that partition CP01 (food & non-alc beverages)
 "CP0111":"Cereals & bakery","CP0112":"Meat","CP0113":"Fish & seafood",
 "CP0114":"Milk, dairy & eggs","CP0115":"Oils & fats","CP0116":"Fruit & nuts",
 "CP0117":"Vegetables & pulses","CP0118":"Sugar & confectionery",
 "CP0119":"Ready-made & other food","CP012":"Non-alcoholic beverages",
 "CP013":"Food processing services"}

def main():
    h = pd.read_csv(PROC/"tr_hicp_monthly.csv")
    w = pd.read_csv(PROC/"tr_hicp_weights.csv")
    idx = h[h.unit=="I15"].pivot_table(index="month", columns="coicop", values="value")
    yr = int(REF[:4])
    wt = w[w.year==yr].set_index("coicop")["weight_permille"]
    if wt.empty:
        wt = w[w.year==w.year.max()].set_index("coicop")["weight_permille"]

    prev = f"{yr-1}-{REF[5:]}"; dec = f"{yr-1}-12"
    rows=[]
    for code,label in SUB.items():
        if code not in idx.columns: continue
        s = idx[code]
        if REF not in s.index or pd.isna(s.get(REF)): continue
        rows.append(dict(coicop=code, group=label,
            weight_permille=wt.get(code, float("nan")),
            yoy_pct=100*(s[REF]/s[prev]-1) if prev in s.index else None,
            ytd_pct=100*(s[REF]/s[dec]-1) if dec in s.index else None,
            index_2015_100=s[REF]))
    d = pd.DataFrame(rows)
    d["share_of_food_basket_pct"] = 100*d.weight_permille/d.weight_permille.sum()
    d["contribution_to_food_yoy_pp"] = d.share_of_food_basket_pct/100*d.yoy_pct
    d["contribution_to_food_ytd_pp"] = d.share_of_food_basket_pct/100*d.ytd_pct
    d = d.sort_values("contribution_to_food_yoy_pp", ascending=False)

    food = idx["CP011"]; cp01 = idx["CP01"]; tot = idx["TOTAL"]
    hdr = pd.DataFrame([
      dict(metric="Food & non-alc beverages (CP01)", yoy_pct=100*(cp01[REF]/cp01[prev]-1), ytd_pct=100*(cp01[REF]/cp01[dec]-1)),
      dict(metric="Food only (CP011)",               yoy_pct=100*(food[REF]/food[prev]-1), ytd_pct=100*(food[REF]/food[dec]-1)),
      dict(metric="Headline CPI (TOTAL)",            yoy_pct=100*(tot[REF]/tot[prev]-1),   ytd_pct=100*(tot[REF]/tot[dec]-1)),
    ])
    d.to_csv(OUT/"01_food_cpi_contributions.csv", index=False)
    hdr.to_csv(OUT/"01_headline_rates.csv", index=False)

    pd.set_option("display.width",200)
    print(f"=== Türkiye, {REF} (Eurostat HICP, ECOICOP-2018) ===\n")
    print(hdr.round(2).to_string(index=False))
    print(f"\n--- Food basket decomposition, {REF} ---")
    print(d[["group","share_of_food_basket_pct","yoy_pct","contribution_to_food_yoy_pp",
             "ytd_pct","contribution_to_food_ytd_pp"]].round(2).to_string(index=False))
    print(f"\nsum of contributions (y/y): {d.contribution_to_food_yoy_pp.sum():.2f} pp")
    print(f"sum of contributions (ytd): {d.contribution_to_food_ytd_pp.sum():.2f} pp")

if __name__ == "__main__":
    main()
