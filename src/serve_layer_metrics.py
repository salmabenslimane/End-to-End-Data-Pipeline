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
        kpis_file.unlink()
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
        daily_file.unlink()
    daily_metrics.to_csv(daily_file, index=False, encoding='utf-8')
    print(f"Daily metrics saved to: {daily_file}")
    return daily_metrics

def generate_sentiment_contradiction_report(reviews_df, processed_dir):
    """
    Generate a per-app summary of sentiment contradictions.
    A contradiction is a review where the text sentiment (positive/negative)
    conflicts with the numeric score (e.g. positive text + low score, or
    negative text + high score).
    Requires columns: sentiment_contradicts_score, contradiction_type
    produced by add_sentiment_heuristic() in transform_apps_reviews.py.
    """
    # Per-review contradiction details (full list for inspection)
    contradictions_df = reviews_df[reviews_df["sentiment_contradicts_score"] == True][[
        "app_id", "app_name", "reviewId", "userName",
        "score", "content", "sentiment_label", "contradiction_type", "at"
    ]].copy()

    contradictions_file = processed_dir / "sentiment_contradictions.csv"
    if contradictions_file.exists():
        contradictions_file.unlink()
    contradictions_df.to_csv(contradictions_file, index=False, encoding="utf-8")
    print(f"Sentiment contradiction details saved to: {contradictions_file}")

    # Per-app contradiction summary
    app_sentiment = reviews_df.groupby(["app_id", "app_name"]).agg(
        total_reviews=("reviewId", "count"),
        contradiction_count=("sentiment_contradicts_score", "sum"),
        positive_text_low_score=("contradiction_type",
                                  lambda x: (x == "positive_text_low_score").sum()),
        negative_text_high_score=("contradiction_type",
                                   lambda x: (x == "negative_text_high_score").sum()),
    ).reset_index()

    app_sentiment["contradiction_pct"] = (
        app_sentiment["contradiction_count"] / app_sentiment["total_reviews"] * 100
    ).round(2)

    sentiment_summary_file = processed_dir / "app_sentiment_summary.csv"
    if sentiment_summary_file.exists():
        sentiment_summary_file.unlink()
    app_sentiment.to_csv(sentiment_summary_file, index=False, encoding="utf-8")
    print(f"App sentiment summary saved to: {sentiment_summary_file}")

    return contradictions_df, app_sentiment

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
    generate_sentiment_contradiction_report(reviews_df, PROCESSED_DIR)

if __name__ == "__main__":
    main()