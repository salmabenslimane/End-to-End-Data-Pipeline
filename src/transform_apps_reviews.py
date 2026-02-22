import json
import pandas as pd
from pathlib import Path

def clean_installs(value):
    """Convert installs field to integer. Handles '1,000,000+', '500000', missing values."""
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return int(str(value).replace(",", "").replace("+", "").strip())
    except ValueError:
        return None

def transform_apps_metadata(apps_source=None):
    # --- Paths ---
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    PROCESSED_APPS_FILE = PROCESSED_DIR / "apps_catalog.csv"

    # --- Determine source file ---
    if apps_source is None:
        apps_source = RAW_DIR / "apps_metadata.json"
    apps_source = Path(apps_source)

    # --- Load depending on format ---
    if apps_source.suffix == ".json":
        with open(apps_source, "r", encoding="utf-8") as f:
            apps_raw = json.load(f)

        apps_clean = []
        for app in apps_raw:
            installs = app.get("installs")
            installs_clean = clean_installs(installs)
            price = app.get("price", 0)
            price = float(price) if price is not None else 0.0
            apps_clean.append({
                "appId":     app.get("appId"),
                "title":     app.get("title"),
                "developer": app.get("developer"),
                "score":     app.get("score"),
                "ratings":   app.get("ratings"),
                "installs":  installs_clean,
                "genre":     app.get("genre"),
                "price":     price
            })
        df_apps = pd.DataFrame(apps_clean)

    elif apps_source.suffix == ".csv":
        df_apps = pd.read_csv(apps_source, dtype=str)

        # --- Clean installs: handles "1,000,000+", "500000", missing ---
        df_apps["installs"] = df_apps["installs"].apply(clean_installs)

        # --- Coerce numeric fields ---
        df_apps["score"]   = pd.to_numeric(df_apps["score"],   errors="coerce")
        df_apps["ratings"] = pd.to_numeric(df_apps["ratings"], errors="coerce")
        df_apps["price"]   = pd.to_numeric(df_apps["price"],   errors="coerce").fillna(0.0)

        # --- Flag missing values in key fields ---
        missing_score = df_apps["score"].isna().sum()
        missing_installs = df_apps["installs"].isna().sum()
        if missing_score > 0:
            print(f"WARNING: {missing_score} app(s) have missing score values:")
            print(df_apps[df_apps["score"].isna()][["appId", "title", "score"]].to_string(index=False))
        if missing_installs > 0:
            print(f"WARNING: {missing_installs} app(s) have missing or unparseable installs values:")
            print(df_apps[df_apps["installs"].isna()][["appId", "title", "installs"]].to_string(index=False))

    else:
        raise ValueError(f"Unsupported apps metadata format: {apps_source.suffix}")

    # --- Handle duplicate appIds: log and keep first occurrence ---
    duplicates = df_apps["appId"].duplicated()
    if duplicates.any():
        print(f"WARNING: {duplicates.sum()} duplicate appId(s) found — keeping first occurrence:")
        print(df_apps[duplicates][["appId", "title"]].to_string(index=False))
    df_apps = df_apps.drop_duplicates(subset="appId", keep="first")

    # --- Save to CSV ---
    if PROCESSED_APPS_FILE.exists():
        PROCESSED_APPS_FILE.unlink()
    df_apps.to_csv(PROCESSED_APPS_FILE, index=False, encoding="utf-8")
    print(f"Processed apps metadata saved to: {PROCESSED_APPS_FILE}")


if __name__ == "__main__":
    import sys
    # Default: use original JSON
    # To use updated apps: python transform_apps_metadata.py data/raw/note_taking_ai_apps_updated.csv
    source = sys.argv[1] if len(sys.argv) > 1 else None
    transform_apps_metadata(apps_source=source)