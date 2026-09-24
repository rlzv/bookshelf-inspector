import time

import pandas as pd
import requests


authors = pd.read_csv("output/simple/recommended_authors.csv")

# Correct the capitalisation for this Wikipedia page lookup.
page_names = {
    "ANNE FRANK": "Anne Frank",
}

headers = {
    "User-Agent": (
        "BookshelfInspector/1.0 "
        "(https://github.com/rlzv/bookshelf-inspector)"
    )
}

results = []

for _, author in authors.iterrows():
    name = author["author"]
    page_name = page_names.get(name, name)

    print(f"Looking up: {name}")

    result = author.to_dict()
    result.update({
        "biography": None,
        "wikipedia_title": None,
        "source_url": None,
        "api_status": "not_found",
    })

    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "titles": page_name,
                "redirects": 1,
                "prop": "extracts|info|pageprops",
                "exintro": 1,
                "explaintext": 1,
                "exchars": 700,
                "inprop": "url",
            },
            headers=headers,
            timeout=20,
        )

        if response.status_code != 200:
            result["api_status"] = f"http_{response.status_code}"
        else:
            data = response.json()

            if "error" in data:
                result["api_status"] = "api_error"
            else:
                pages = data.get("query", {}).get("pages", {})

                for page in pages.values():
                    if "missing" in page:
                        continue

                    if "disambiguation" in page.get("pageprops", {}):
                        result["api_status"] = "ambiguous"
                        continue

                    biography = page.get("extract")

                    result.update({
                        "biography": biography,
                        "wikipedia_title": page.get("title"),
                        "source_url": page.get("fullurl"),
                        "api_status": (
                            "needs_review" if biography else "no_biography"
                        ),
                    })

    except requests.RequestException:
        result["api_status"] = "connection_error"
    except ValueError:
        result["api_status"] = "invalid_json"

    results.append(result)
    time.sleep(1)


enriched_authors = pd.DataFrame(results)

output_file = "output/simple/enriched_authors.csv"

enriched_authors.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
)

print(f"\nSaved {len(enriched_authors)} authors to {output_file}")
print("\nAPI results:")
print(enriched_authors["api_status"].value_counts())