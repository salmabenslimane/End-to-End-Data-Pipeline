import json
import pandas as pd
from pathlib import Path

def transform_apps_metadata():
    # --- Paths ---
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent  # project root
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    RAW_APPS_FILE = RAW_DIR / "apps_metadata.json"
    PROCESSED_APPS_FILE = PROCESSED_DIR / "apps_catalog.csv"

    # --- Load raw apps metadata ---
    with open(RAW_APPS_FILE, "r", encoding="utf-8") as f:
        apps_raw = json.load(f)

    # --- Transform apps metadata ---
    apps_clean = []

    for app in apps_raw:
        # Clean installs: convert "10,000,000+" -> 10000000
        installs = app.get("installs")
        installs_clean = int(installs.replace(",", "").replace("+", "")) if installs else None

        # Price: ensure numeric
        price = app.get("price", 0)
        price = float(price) if price is not None else 0.0

        apps_clean.append({
            "appId": app.get("appId"),
            "title": app.get("title"),
            "developer": app.get("developer"),
            "score": app.get("score"),
            "ratings": app.get("ratings"),
            "installs": installs_clean,
            "genre": app.get("genre"),
            "price": price
        })

    # --- Save to CSV ---
    df_apps = pd.DataFrame(apps_clean)

    # Optional: remove old file if exists (ensures clean re-run)
    if PROCESSED_APPS_FILE.exists():
        PROCESSED_APPS_FILE.unlink()

    df_apps.to_csv(PROCESSED_APPS_FILE, index=False, encoding="utf-8")

    print(f"Processed apps metadata saved to: {PROCESSED_APPS_FILE}")

if __name__ == "__main__":
    transform_apps_metadata()
