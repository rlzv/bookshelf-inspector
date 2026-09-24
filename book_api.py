from getpass import getpass
from pathlib import Path
import time

import pandas as pd
import requests


books = pd.read_csv(
    "output/simple/recommended_books.csv",
    dtype={"ISBN": str},
)

api_key = getpass("Paste your Google Books API key: ").strip()

results = []

for _, book in books.iterrows():
    isbn = book["ISBN"]
    print(f"Looking up: {book['Book-Title']}")

    # Keep the recommendation even if enrichment fails.
    result = book.to_dict()
    result.update({
        "description": None,
        "categories": None,
        "language": None,
        "page_count": None,
        "cover_url": None,
        "source_url": None,
        "api_status": "not_found",
    })

    try:
        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": f"isbn:{isbn}", "key": api_key},
            timeout=20,
        )

        if response.status_code != 200:
            result["api_status"] = f"http_{response.status_code}"
        else:
            data = response.json()

            for item in data.get("items", []):
                info = item.get("volumeInfo", {})

                identifiers = [
                    entry.get("identifier", "").replace("-", "")
                    for entry in info.get("industryIdentifiers", [])
                ]

                if isbn not in identifiers:
                    continue

                pages = info.get("pageCount")

                result.update({
                    "description": info.get("description"),
                    "categories": ", ".join(
                        info.get("categories", [])
                    ) or None,
                    "language": info.get("language"),
                    "page_count": (
                        pages
                        if isinstance(pages, int) and pages > 0
                        else None
                    ),
                    "cover_url": info.get(
                        "imageLinks", {}
                    ).get("thumbnail"),
                    "source_url": info.get("infoLink"),
                    "api_status": "matched",
                })

                break

    except requests.RequestException:
        result["api_status"] = "connection_error"
    except ValueError:
        result["api_status"] = "invalid_json"

    results.append(result)
    time.sleep(1)


enriched_books = pd.DataFrame(results)

output_file = Path("output/simple/enriched_books.csv")

enriched_books.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
)

print(f"\nSaved {len(enriched_books)} books to {output_file}")
print("\nAPI results:")
print(enriched_books["api_status"].value_counts())