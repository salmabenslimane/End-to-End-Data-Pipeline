import json
import pandas as pd
from pathlib import Path

def transform_apps_reviews(reviews_source=None):
    # --- Paths ---
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    PROCESSED_APPS_FILE = PROCESSED_DIR / "apps_catalog.csv"
    PROCESSED_REVIEWS_FILE = PROCESSED_DIR / "apps_reviews.csv"

    # --- Load apps catalog for app names ---
    apps_df = pd.read_csv(PROCESSED_APPS_FILE, usecols=["appId", "title"])
    known_app_ids = set(apps_df["appId"])
    app_id_to_name = dict(zip(apps_df["appId"], apps_df["title"]))

    # --- Determine source file ---
    if reviews_source is None:
        reviews_source = RAW_DIR / "reviews.jsonl"
    reviews_source = Path(reviews_source)

    # --- Load reviews depending on format ---
    if reviews_source.suffix == ".jsonl":
        reviews_list = []
        with open(reviews_source, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
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

    elif reviews_source.suffix == ".csv":
        df_reviews = pd.read_csv(reviews_source, parse_dates=["at"])
        # app_name may already be in the CSV, but we still validate app_ids
        if "app_name" not in df_reviews.columns:
            df_reviews["app_name"] = df_reviews["app_id"].map(app_id_to_name)

    else:
        raise ValueError(f"Unsupported reviews file format: {reviews_source.suffix}")

    # --- Handle duplicates: keep first occurrence of each reviewId ---
    duplicates = df_reviews["reviewId"].duplicated().sum()
    print(f"Duplicate reviewIds found: {duplicates} — keeping first occurrence")
    df_reviews = df_reviews.drop_duplicates(subset="reviewId", keep="first")

    # --- Handle unknown apps: flag reviews with no matching app in catalog ---
    unknown_apps = df_reviews[~df_reviews["app_id"].isin(known_app_ids)]["app_id"].unique()
    if len(unknown_apps) > 0:
        print(f"WARNING: Reviews reference app_ids not in apps catalog: {list(unknown_apps)}")
        print(f"These reviews will be kept but app_name will be None.")

    # --- Save processed reviews ---
    if PROCESSED_REVIEWS_FILE.exists():
        PROCESSED_REVIEWS_FILE.unlink()
    df_reviews.to_csv(PROCESSED_REVIEWS_FILE, index=False, encoding="utf-8")
    print(f"Processed reviews saved to: {PROCESSED_REVIEWS_FILE}")


if __name__ == "__main__":
    import sys
    # Default: use original JSONL
    # To use batch2: python transform_apps_reviews.py data/raw/note_taking_ai_reviews_batch2.csv
    source = sys.argv[1] if len(sys.argv) > 1 else None
    transform_apps_reviews(reviews_source=source)