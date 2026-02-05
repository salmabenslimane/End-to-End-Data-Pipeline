import pandas as pd
from pathlib import Path

def verify_data_quality():
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

    APPS_FILE = PROCESSED_DIR / "apps_catalog.csv"
    REVIEWS_FILE = PROCESSED_DIR / "apps_reviews.csv"
    REPORT_FILE = PROCESSED_DIR / "data_quality_report.txt"

    apps_df = pd.read_csv(APPS_FILE)
    reviews_df = pd.read_csv(REVIEWS_FILE, parse_dates=["at"])

    report_lines = []

    # Check that datasets are tabular
    report_lines.append(f"Apps dataset shape: {apps_df.shape}")
    report_lines.append(f"Reviews dataset shape: {reviews_df.shape}")
    report_lines.append(f"Apps columns: {apps_df.columns.tolist()}")
    report_lines.append(f"Reviews columns: {reviews_df.columns.tolist()}")

    # Check key fields for joins
    missing_apps = set(reviews_df['app_id']) - set(apps_df['appId'])
    report_lines.append(f"App IDs in reviews not in apps catalog: {missing_apps}")
    report_lines.append(f"Duplicate appIds in apps catalog: {apps_df['appId'].duplicated().sum()}")
    report_lines.append(f"Duplicate reviewIds in reviews: {reviews_df['reviewId'].duplicated().sum()}")

    # Check numeric fields
    numeric_apps = ["score", "ratings", "installs", "price"]
    numeric_reviews = ["score", "thumbsUpCount"]
    report_lines.append("\nApps numeric summary:\n" + str(apps_df[numeric_apps].describe()))
    report_lines.append("\nReviews numeric summary:\n" + str(reviews_df[numeric_reviews].describe()))

    # Check timestamps can be aggregated by day
    try:
        reviews_per_day = reviews_df.groupby(reviews_df['at'].dt.date).size()
        report_lines.append(f"\nReviews per day (sample 5 rows):\n{reviews_per_day.head()}")
    except Exception as e:
        report_lines.append(f"\nError aggregating timestamps: {e}")

    # Detect obvious anomalies
    report_lines.append(f"\nNegative thumbsUpCount reviews: {(reviews_df['thumbsUpCount'] < 0).sum()}")
    report_lines.append(f"Apps with installs <=0: {(apps_df['installs'] <= 0).sum()}")
    report_lines.append(f"Apps with score outside 0-5:\n{apps_df[(apps_df['score']>5) | (apps_df['score']<0)]}")
    report_lines.append(f"Reviews with score outside 0-5:\n{reviews_df[(reviews_df['score']>5) | (reviews_df['score']<0)]}")

    # --- Save report ---
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Data quality verification complete. Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    verify_data_quality()
