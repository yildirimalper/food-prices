"""FAOSTAT: Türkiye farm-gate producer prices and production volumes.
Annual and lagged, but the only open source of actual farm-gate price *levels*
(LCU/tonne) per commodity, so it anchors the 'what the farmer is paid' side."""
import sys, zipfile, io, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import fetch, RAW, PROC

BASE = "https://bulks-faostat.fao.org/production"
TR_AREA = "Türkiye"

def grab(fname, outname, keep):
    dest = RAW / fname
    if not dest.exists():
        fetch(f"{BASE}/{fname}", dest, timeout=900)
    print(f"[faostat] {fname} {dest.stat().st_size:,} bytes")
    with zipfile.ZipFile(dest) as z:
        member = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(member) as fh:
            chunks = []
            for ch in pd.read_csv(fh, chunksize=500_000, encoding="latin-1", low_memory=False):
                col = "Area" if "Area" in ch.columns else "AreaName"
                ch = ch[ch[col].astype(str).str.contains("rkiye|Turkey", regex=True, na=False)]
                if len(ch): chunks.append(ch)
    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    print(f"   Türkiye rows: {len(df):,}")
    if len(df):
        cols = [c for c in keep if c in df.columns]
        df = df[cols]
        df.to_csv(PROC / outname, index=False)
        print(f"-> {outname} {len(df):,} rows, years "
              f"{df['Year'].min()}..{df['Year'].max()}")
    return df

def main():
    p = grab("Prices_E_All_Data_(Normalized).zip", "tr_faostat_producer_prices.csv",
             ["Area","Item","Item Code (CPC)","Element","Year","Months","Unit","Value","Flag"])
    if len(p):
        el = p["Element"].value_counts()
        print("   elements:", el.to_dict())
    q = grab("Production_Crops_Livestock_E_All_Data_(Normalized).zip",
             "tr_faostat_production.csv",
             ["Area","Item","Item Code (CPC)","Element","Year","Unit","Value","Flag"])
    if len(q):
        print("   elements:", q["Element"].value_counts().to_dict())

if __name__ == "__main__":
    main()
