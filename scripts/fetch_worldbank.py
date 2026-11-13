"""World Bank Commodity Price Data ('Pink Sheet'): global fertiliser, energy and
food commodity prices — the imported-input side of Türkiye's farm cost stack."""
import sys, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import fetch, RAW, PROC

URL = ("https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
       "related/CMO-Historical-Data-Monthly.xlsx")

def main():
    dest = RAW / "worldbank_pinksheet_monthly.xlsx"
    fetch(URL, dest, timeout=300)
    print(f"[worldbank] pink sheet {dest.stat().st_size:,} bytes")
    xl = pd.ExcelFile(dest)
    print("   sheets:", xl.sheet_names)
    # Monthly Prices sheet: row 4 = names, row 5 = units, data from row 6
    raw = xl.parse("Monthly Prices", header=None)
    names = raw.iloc[4].tolist()
    units = raw.iloc[5].tolist()
    cols = []
    for i, (n, u) in enumerate(zip(names, units)):
        n = str(n).strip().replace("\n", " ")
        cols.append("month" if i == 0 else f"{n} ({str(u).strip()})")
    df = raw.iloc[6:].copy(); df.columns = cols
    df = df[df["month"].notna()].copy()
    df["month"] = (df["month"].astype(str).str.strip()
                   .str.replace("M", "-", regex=False))
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df["month"].str.match(r"^\d{4}-\d{2}$", na=False)]
    df.to_csv(PROC / "worldbank_commodity_monthly.csv", index=False)
    print(f"-> worldbank_commodity_monthly.csv {len(df):,} rows x {len(df.columns)} cols "
          f"({df['month'].min()}..{df['month'].max()})")
    keys = [c for c in df.columns if any(k in c.lower() for k in
            ["urea", "dap", "phosphate", "potassium", "crude", "natural gas",
             "wheat", "maize", "soybean", "sugar", "fertilizer"])]
    print("   key input columns:", keys[:18])

if __name__ == "__main__":
    main()
