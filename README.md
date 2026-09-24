# Bookshelf Inspector

A small Python project that recommends books and authors for a bookshop's
international catalogue and adds information from external APIs.

## Project files

- `analysis.py`: selects 20 books and 10 authors using reader ratings.
- `book_api.py`: adds book information from Google Books.
- `author_api.py`: retrieves author biography candidates from Wikipedia.
- `output/simple/`: recommendation and enriched CSV files.

## Dataset

Download the Book Recommendation Dataset:
https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset

Place `archive.zip` in the project root without extracting it.
The dataset and virtual environment are excluded from Git.

## Setup

Use Python 3.12.

On Windows with Git Bash:

```bash
py -3.12 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

For subsequent terminal sessions, activate the existing environment:

```bash
source .venv/Scripts/activate
```

## Run

```bash
python analysis.py
python book_api.py
python author_api.py
```

The analysis runs locally. Both API scripts require internet access.

The Google Books script prompts for a Google Books API key.
Enable Books API in your Google Cloud project before using it.
Do not put the key in source code or commit it.

The Wikipedia script does not require an API key.

## Recommendation method

### Books

1. Use explicit ratings from 1 to 10. Zero represents implicit feedback.
2. Calculate rating count and average rating for each ISBN.
3. Keep editions with at least 50 ratings.
4. Join the results to catalogue titles and authors.
5. Correct selected known author-name variations.
6. For matching normalized title-author pairs, retain the eligible edition
   with the most ratings.
7. Select 20 editions ordered by average rating, then rating count.

### Authors

1. Join explicit ratings to catalogue authors.
2. Group by normalized author name after the known-name corrections.
3. Calculate rating count, distinct reader count, and average rating.
4. Keep authors with at least 100 distinct readers.
5. Select 10 authors ordered by average rating, then reader count.

These thresholds and shortlist sizes are starting choices, not client requirements.
Author averages give each rating equal weight, so prolific readers contribute more.

## Outputs

All files are saved in `output/simple/`:

| File | Contents |
|---|---|
| `recommended_books.csv` | Book shortlist and rating statistics |
| `recommended_authors.csv` | Author shortlist and rating statistics |
| `enriched_books.csv` | Book shortlist plus API metadata and lookup status |
| `enriched_authors.csv` | Author shortlist plus biography candidates and source links |

The observed Google Books run matched 19 of 20 ISBNs.
A matched ISBN does not guarantee that every metadata field is available.
Missing information remains blank; failed lookups retain the original recommendation.
Non-positive page counts are treated as missing.

Wikipedia biographies marked `needs_review` must be checked against their source
pages to confirm the correct author. Keep source links with displayed information.

## Limitations and future improvements

- The dataset is historical, collected in 2004, and does not establish current
  worldwide demand.
- Reader countries are not used in this version.
- Different subtitles and uncorrected author aliases can leave duplicate works.
- Book averages refer to selected editions, not combined ratings across editions.
- Catalogue cleaning is partial; some malformed source records remain.
- The shortlist can be dominated by a series or author and needs editorial review.
- API information can be incomplete or unavailable.

With more time, I would improve work and author matching, validate remaining
catalogue issues, analyse target-country preferences, check stock and language
availability, and evaluate the shortlist using current customer behaviour.
