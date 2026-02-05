import json
import pandas as pd
from pathlib import Path

def transform_apps_reviews():
    # --- Paths ---
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent  # project root
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    RAW_REVIEWS_FILE = RAW_DIR / "reviews.jsonl"
    PROCESSED_APPS_FILE = PROCESSED_DIR / "apps_catalog.csv"
    PROCESSED_REVIEWS_FILE = PROCESSED_DIR / "apps_reviews.csv"

    # --- Load apps catalog for app names ---
    apps_df = pd.read_csv(PROCESSED_APPS_FILE, usecols=["appId", "title"])
    app_id_to_name = dict(zip(apps_df["appId"], apps_df["title"]))

    # --- Load raw reviews ---
    reviews_list = []
    with open(RAW_REVIEWS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            # Clean timestamp
            at = pd.to_datetime(r.get("at"), errors="coerce") if r.get("at") else None

            reviews_list.append({
                "app_id": r.get("appId"),
                "app_name": app_id_to_name.get(r.get("appId"), None),
                "reviewId": r.get("reviewId"),
                "userName": r.get("userName"),
                "score": r.get("score"),
                "content": r.get("content") if r.get("content") else "",
                "thumbsUpCount": r.get("thumbsUpCount", 0),
                "at": at
            })

    df_reviews = pd.DataFrame(reviews_list)

    # Optional: remove old file if exists (ensures clean re-run)
    if PROCESSED_REVIEWS_FILE.exists():
        PROCESSED_REVIEWS_FILE.unlink()

    # --- Save processed reviews ---
    df_reviews.to_csv(PROCESSED_REVIEWS_FILE, index=False, encoding="utf-8")
    print(f"Processed reviews saved to: {PROCESSED_REVIEWS_FILE}")


if __name__ == "__main__":
    transform_apps_reviews()
