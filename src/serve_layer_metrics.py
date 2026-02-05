# src/serve_layer_metrics.py

import pandas as pd
from pathlib import Path

def generate_app_level_kpis(reviews_df, processed_dir):
    """Generate app-level KPIs."""
    kpis = reviews_df.groupby(['app_id', 'app_name']).agg(
        num_reviews=('reviewId', 'count'),
        avg_rating=('score', 'mean'),
        low_rating_pct=('score', lambda x: (x <= 2).mean() * 100),
        first_review_date=('at', 'min'),
        last_review_date=('at', 'max')
    ).reset_index()

    kpis_file = processed_dir / "apps_kpis.csv"
    if kpis_file.exists():
        kpis_file.unlink()  # ensure re-runnable
    kpis.to_csv(kpis_file, index=False, encoding='utf-8')
    print(f"App-level KPIs saved to: {kpis_file}")
    return kpis

def generate_daily_metrics(reviews_df, processed_dir):
    """Generate daily time series metrics."""
    reviews_df['review_date'] = reviews_df['at'].dt.date
    daily_metrics = reviews_df.groupby('review_date').agg(
        daily_num_reviews=('reviewId', 'count'),
        daily_avg_rating=('score', 'mean')
    ).reset_index()

    daily_file = processed_dir / "daily_metrics.csv"
    if daily_file.exists():
        daily_file.unlink()  # ensure re-runnable
    daily_metrics.to_csv(daily_file, index=False, encoding='utf-8')
    print(f"Daily metrics saved to: {daily_file}")
    return daily_metrics

def main():
    # --- Paths ---
    SRC_DIR = Path(__file__).resolve().parent
    BASE_DIR = SRC_DIR.parent
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

    REVIEWS_FILE = PROCESSED_DIR / "apps_reviews.csv"

    # --- Load reviews ---
    reviews_df = pd.read_csv(REVIEWS_FILE, parse_dates=['at'])

    # --- Generate outputs ---
    generate_app_level_kpis(reviews_df, PROCESSED_DIR)
    generate_daily_metrics(reviews_df, PROCESSED_DIR)

if __name__ == "__main__":
    main()
