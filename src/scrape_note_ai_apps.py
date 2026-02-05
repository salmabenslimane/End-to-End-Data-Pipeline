import json
from pathlib import Path
from google_play_scraper import search, app, reviews, Sort

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

APPS_JSON = RAW_DIR / "apps_metadata.json"
REVIEWS_JSONL = RAW_DIR / "reviews.jsonl"

QUERY = "AI note taking"
LANG = "en"
COUNTRY = "us"

N_APPS = 20
REVIEWS_PER_APP = 1000

apps = search(
    QUERY,
    lang=LANG,
    country=COUNTRY,
    n_hits=N_APPS
)

apps_metadata = []
all_reviews = []

for a in apps:
    app_id = a["appId"]
    print(f"Scraping {app_id}")

    app_data = app(
        app_id,
        lang=LANG,
        country=COUNTRY
    )
    apps_metadata.append(app_data)

    count = 0
    continuation_token = None

    while count < REVIEWS_PER_APP:
        batch, continuation_token = reviews(
            app_id,
            lang=LANG,
            country=COUNTRY,
            sort=Sort.NEWEST,
            count=200,
            continuation_token=continuation_token
        )

        if not batch:
            break

        for r in batch:
            r["appId"] = app_id
            all_reviews.append(r)

        count += len(batch)

        if continuation_token is None:
            break

with open(APPS_JSON, "w", encoding="utf-8") as f:
    json.dump(apps_metadata, f, ensure_ascii=False, indent=2)

with open(REVIEWS_JSONL, "w", encoding="utf-8") as f:
    for review in all_reviews:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")

print("Done ✅")
