import json
import pandas as pd
from pathlib import Path

# Column name mapping: maps any known variant -> our standard internal name
COLUMN_ALIASES = {
    "app_id":        "app_id",
    "appId":         "app_id",
    "app_name":      "app_name",
    "appTitle":      "app_name",
    "reviewId":      "reviewId",
    "review_id":     "reviewId",
    "userName":      "userName",
    "username":      "userName",
    "score":         "score",
    "rating":        "score",
    "content":       "content",
    "review_text":   "content",
    "thumbsUpCount": "thumbsUpCount",
    "likes":         "thumbsUpCount",
    "at":            "at",
    "review_time":   "at",
}

def normalize_columns(df):
    """Rename columns to standard internal names using COLUMN_ALIASES."""
    rename_map = {col: COLUMN_ALIASES[col] for col in df.columns if col in COLUMN_ALIASES}
    unknown = [col for col in df.columns if col not in COLUMN_ALIASES]
    if unknown:
        print(f"WARNING: Unknown columns ignored during normalization: {unknown}")
    return df.rename(columns=rename_map)

def clean_dirty_records(df):
    """
    Detect and handle invalid, missing, or inconsistent values.
    - score: coerce to numeric, flag and remove out-of-range values (valid: 1-5)
    - at: coerce to datetime, flag rows with malformed timestamps
    - thumbsUpCount: coerce to numeric, replace NULL strings and NaN with 0
    - content: replace string "NULL" with empty string
    All problematic rows are logged before any action is taken.
    """
    # --- score: coerce to numeric (handles "five", empty strings, etc.) ---
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    invalid_score_type = df["score"].isna()

    # Flag out-of-range scores (valid range: 1-5)
    out_of_range = df["score"].notna() & ~df["score"].between(1, 5)

    if invalid_score_type.any():
        print(f"WARNING: {invalid_score_type.sum()} review(s) have non-numeric scores — score set to NaN:")
        print(df[invalid_score_type][["reviewId", "score"]].to_string(index=False))

    if out_of_range.any():
        print(f"WARNING: {out_of_range.sum()} review(s) have out-of-range scores (not in 1-5) — score set to NaN:")
        print(df[out_of_range][["reviewId", "score"]].to_string(index=False))

    # Set out-of-range scores to NaN so they don't corrupt aggregates
    df.loc[out_of_range, "score"] = None

    # --- at: coerce malformed timestamps to NaT ---
    df["at"] = pd.to_datetime(df["at"], errors="coerce")
    invalid_dates = df["at"].isna()
    if invalid_dates.any():
        print(f"WARNING: {invalid_dates.sum()} review(s) have malformed timestamps — 'at' set to NaT:")
        print(df[invalid_dates][["reviewId", "at"]].to_string(index=False))

    # --- thumbsUpCount: replace string "NULL" then coerce, fill remaining NaN with 0 ---
    df["thumbsUpCount"] = df["thumbsUpCount"].replace("NULL", None)
    df["thumbsUpCount"] = pd.to_numeric(df["thumbsUpCount"], errors="coerce").fillna(0).astype(int)

    # --- content: replace string "NULL" with empty string ---
    df["content"] = df["content"].replace("NULL", "").fillna("")

    return df


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
        # Load all as strings first so we can detect dirty values before pandas coerces them
        df_reviews = pd.read_csv(reviews_source, dtype=str)
        # Normalize column names to handle schema drift
        df_reviews = normalize_columns(df_reviews)
        # Clean dirty and inconsistent records explicitly
        df_reviews = clean_dirty_records(df_reviews)
        # Fill optional fields that may be missing after normalization
        df_reviews["content"] = df_reviews.get("content", pd.Series(dtype=str)).fillna("")
        df_reviews["thumbsUpCount"] = df_reviews.get("thumbsUpCount", pd.Series(dtype=float)).fillna(0)
        # Derive app_name from catalog if not present in the file
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
    # To use schema drift:  python transform_apps_reviews.py data/raw/note_taking_ai_reviews_schema_drift.csv
    # To use dirty data:    python transform_apps_reviews.py data/raw/note_taking_ai_reviews_dirty.csv
    source = sys.argv[1] if len(sys.argv) > 1 else None
    transform_apps_reviews(reviews_source=source)