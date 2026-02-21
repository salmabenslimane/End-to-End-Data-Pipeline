Feedback:

- Think about writing with append in the loop; it is always better to prevent data loss if code crashes
- The data quality verification is neat!
- Please add a screenshot of your dashboard to the readmefile


# Dashboard screenshots : 

![alt text](image.png)

![alt text](image-1.png)

![alt text](image-3.png)

# Observations on supporting the new batch :

1. How many changes were required? 
-> Two additions: format detection (CSV vs JSONL) and a deduplication step. The rest of the pipeline was unchanged.

2. Is it a full refresh or implicit? 
-> It's a full refresh; the old processed file is deleted and rewritten from scratch each run.

3. How are duplicates handled? 
-> r_2002 appears twice? the script now explicitly drops duplicates keeping the first occurrence and logs how many were found.

4. What happens to unknown apps? 
-> com.ghost.notes and com.newnote.ai are not in the apps catalog, they are kept in the reviews but app_name will be None, and a warning is printed.


# Observations on schema drift :

1. Which parts of your pipeline rely on hard-coded column names?
-> transform_apps_reviews.py relied on "app_name", "app_id" by name in the CSV branch. serve_layer_metrics.py references "reviewId", "score", "app_id", "app_name", "at" in its groupby and agg calls. verify_data_quality.py explicitly references "score", "thumbsUpCount", "at" in its numeric summary and anomaly checks.

2. Does the pipeline fail explicitly, or does it produce incorrect results silently?
-> Mostly silently. pandas does not raise an error when expected column names are absent, it simply produces NaN for any operation referencing those columns. score and at being NaN would have propagated into serve_layer_metrics.py, producing NaN average ratings and broken daily aggregations with no exception raised. The only explicit crash would have been in verify_data_quality.py which references column names directly.

3. How localized or widespread are the required code changes?
-> The fix was fully localized to transform_apps_reviews.py. Because normalization happens at load time, all downstream scripts (serve_layer_metrics, verify_data_quality, dashboard) required zero changes, they continue to operate on the standard column names. This confirms that the transformation layer is the correct place to absorb schema changes.

# Observations on dirty and inconsistent data records:

1. How does your pipeline handle invalid ratings or timestamps?
-> score coerced to numeric via pd.to_numeric(errors="coerce"): "five" (r_2101) and empty (r_2105) become NaN. Out-of-range scores (-1 for r_2102, 0 for r_2109) are detected and explicitly set to NaN with a warning. Malformed timestamps like "not_a_date" (r_2103) become NaT via pd.to_datetime(errors="coerce"). All problematic rows are logged before any action is taken.

2. Are problematic records filtered out, transformed, or propagated downstream?
-> Records are kept but their invalid fields are neutralized: bad scores become NaN, bad timestamps become NaT, string "NULL" in thumbsUpCount and content are replaced with 0 and "" respectively. No rows are dropped. This means reviews with NaN scores are still counted in num_reviews in the serving layer but excluded from avg_rating calculations. Reviews with NaT timestamps are excluded from daily_metrics aggregations.

3. Do data quality issues surface early, or do they affect aggregated metrics silently?
-> With the fix, they surface early — every problematic record is printed with its reviewId at transformation time, before any aggregation happens. Without the fix (old behavior with parse_dates and no dtype=str), pandas would have silently coerced types on load, "five" would become NaN with no warning, and 0/-1 scores would have passed through unchecked and directly lowered average ratings in the serving layer.