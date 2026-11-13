"""Türkiye: food-manufacturing producer prices, EUR/TRY, minimum wage (Eurostat)."""
import sys, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import fetch_json, RAW, PROC
from fetch_eurostat_hicp import jsonstat_to_frame

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
# NACE branches that make up the food chain's processing stage
NACE = ["B-E36", "C", "C10", "C101", "C102", "C103", "C104", "C105", "C106",
        "C107", "C108", "C109", "C11", "C1101", "C1105", "C1107", "C17", "C20",
        "C2015", "C22", "C2222", "C23", "D", "D35", "MIG_COG", "MIG_NRG"]

def main():
    # ---- producer prices in industry, domestic market ----
    frames = []
    for unit in ["I21", "PCH_SM"]:
        q = "&".join(f"nace_r2={n}" for n in NACE)
        url = (f"{API}/sts_inppd_m?format=JSON&geo=TR&unit={unit}"
               f"&sinceTimePeriod=2015-01&{q}")
        print(f"[eurostat] sts_inppd_m unit={unit}")
        d = fetch_json(url, RAW / f"eurostat_ppi_TR_{unit}.json")
        if "error" in d:
            print("   !", str(d["error"])[:160]); continue
        df = jsonstat_to_frame(d)
        df["nace_label"] = df["nace_r2"].map(
            d["dimension"]["nace_r2"]["category"].get("label", {}))
        frames.append(df)
        print(f"   {len(df):,} obs {df['time'].min()}..{df['time'].max()}")
    ppi = pd.concat(frames, ignore_index=True).rename(columns={"time": "month"})
    ppi = ppi[["month", "nace_r2", "nace_label", "unit", "value"]].sort_values(
        ["nace_r2", "unit", "month"])
    ppi.to_csv(PROC / "tr_ppi_monthly.csv", index=False)
    print(f"-> tr_ppi_monthly.csv {len(ppi):,} rows")

    # ---- EUR exchange rates (TRY + USD, to derive USD/TRY) ----
    print("[eurostat] ert_bil_eur_m")
    d = fetch_json(f"{API}/ert_bil_eur_m?format=JSON&currency=TRY&currency=USD"
                   f"&statinfo=AVG&sinceTimePeriod=2015-01",
                   RAW / "eurostat_fx.json")
    fx = jsonstat_to_frame(d).rename(columns={"time": "month"})
    fx = fx.pivot_table(index="month", columns="currency", values="value").reset_index()
    fx["TRY_per_EUR"] = fx["TRY"]; fx["USD_per_EUR"] = fx["USD"]
    fx["TRY_per_USD"] = fx["TRY"] / fx["USD"]
    fx[["month", "TRY_per_EUR", "USD_per_EUR", "TRY_per_USD"]].to_csv(
        PROC / "tr_fx_monthly.csv", index=False)
    print(f"-> tr_fx_monthly.csv {len(fx):,} rows {fx['month'].min()}..{fx['month'].max()}")

    # ---- statutory minimum wage ----
    print("[eurostat] earn_mw_cur")
    d = fetch_json(f"{API}/earn_mw_cur?format=JSON&geo=TR&currency=NAC&sinceTimePeriod=2015",
                   RAW / "eurostat_minwage.json")
    mw = jsonstat_to_frame(d).rename(columns={"time": "half_year", "value": "min_wage_try"})
    mw[["half_year", "min_wage_try"]].to_csv(PROC / "tr_minwage.csv", index=False)
    print(f"-> tr_minwage.csv {len(mw)} rows {mw['half_year'].min()}..{mw['half_year'].max()}")

if __name__ == "__main__":
    main()
