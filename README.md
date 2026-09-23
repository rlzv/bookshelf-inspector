# Bookshelf Inspector — explainable international catalogue selection

An interview project for Big Data Academy using Python and pandas. Start with this README, run the pipeline, then read RESULTS.md and INTERVIEW.md.

## Business answer

Recommend 20 books and 10 authors for an international catalogue pilot. Use explicit reader satisfaction with enough evidence, require support in several countries, and prevent one author dominating the Books page. These are historical recommendations, not current bestsellers or sales forecasts.

The task mentions a $1 million budget. A budget is a ceiling, not a requirement to spend: validate the catalogue cheaply before investing in infrastructure, marketing or licensed data. No paid services are required for the core prototype.

The client's Google Sites page could not be retrieved in this environment. Requirements are based on the supplied brief; no claims are made about its current design.

## Run locally

Use Python 3.11 or 3.12. Extract this project ZIP into a folder and place the original dataset archive.zip inside that folder. The input archive is not duplicated in this package.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements.txt
python pipeline.py --archive archive.zip
python -m unittest -v
```

Optional API enrichment (network required):

```bash
python enrich.py --limit 20
```

Google Books accepts an optional `GOOGLE_BOOKS_API_KEY` environment variable in this script. Do not commit API keys. API availability and quota depend on the provider. Delete `output/api_cache/` to refresh cached responses. Wikipedia candidates require human identity review; an exact page title is not proof that it describes the correct author.

Outputs are included so you can inspect the actual results before installing anything.

## Files and reading order

1. `pipeline.py`: input, cleaning, joins, ranking and output.
2. `author_aliases.csv`: transparent, manually reviewed name corrections.
3. `output/quality_report.json`: observed counts, thresholds and input SHA-256.
4. `output/books_top20.csv` and `output/authors_top10.csv`: client shortlists.
5. `output/books_ranked_top100.csv`: candidates before the author diversity cap.
6. `output/audience_countries.csv`: distinct explicitly rating readers by country, including unknown.
7. `output/sensitivity.csv`: shortlist overlap when the prior strength changes.
8. `output/quarantined_books.csv`: bad records retained for investigation.
9. `enrich.py`: optional Google Books and Wikipedia integration.
10. `RESULTS.md` and `INTERVIEW.md`: findings and presentation preparation.

## Understand the three inputs

- Books: catalogue metadata, keyed by ISBN (an edition identifier).
- Users: reader IDs and free-text locations. Age is not needed and is not loaded.
- Ratings: user/ISBN interactions. Values 1–10 are explicit ratings; zero means implicit feedback.

All interactions can indicate historical reach. Only explicit ratings can contribute to the quality score. They do not prove purchases, sales, or revenue.

## Cleaning decisions

- Keep ISBN as text to preserve leading zeros; trim and uppercase it. After normalization, collapse duplicate ISBNs using the first source record. The audit reports how many; production should compare conflicting metadata before choosing a canonical record.
- Quarantine records with nonnumeric years or missing titles/authors. Three shifted-column rows and two missing authors are excluded in this archive. Do not guess repairs.
- Set years outside 1450–2004 to unknown. This is a conservative plausibility rule for a 2004 snapshot, not a universal rule about publication dates. Retain these books for ranking.
- Normalize Unicode, case and whitespace. Use a small explicit author alias file for observed variants; do not guess all author identities with fuzzy matching.
- Group editions by normalized title plus normalized author. Average multiple explicit edition ratings by the same reader into one user/work vote. Different subtitles, translations and punctuation may still produce separate works. Conversely, identically named works by one author could be merged. A verified work identifier would improve this.
- Drop exact duplicate rating rows. If a user/ISBN has conflicting ratings, exclude those rows; no timestamps exist to select a latest rating. Neither issue was observed in this archive.
- Join ratings to usable books. Report orphan/unusable-book rows. A missing user record would retain its rating with unknown country.
- Extract the final comma-separated location component. Map common aliases against a conservative country list. Unknown values stay unknown. This list does not cover every country: geographic coverage is a lower bound.

## Explain the book score

Let R be a book's average explicit rating, v its number of distinct explicit readers, C the overall mean across deduplicated user/work votes, and m the prior strength.

```
score = (v × R + m × C) / (v + m)
```

For books, m = 50. Think of this as adding 50 average-rating votes. A book with two perfect reviews should not automatically beat a book with hundreds of strong reviews. This is a weighted rating with shrinkage; it is not a trained machine-learning model, probability, or confidence interval.

Eligibility: at least 50 explicit readers and at least three countries with three explicit readers each. The latter is modest evidence of cross-country appeal, not proof of worldwide demand. Sort by score, then reader count, then work key for deterministic ties. Select up to 20 with at most two per normalized author.

The representative ISBN is the edition with most observed interactions. Its publisher/year/cover describe that edition, not the whole work. English-language availability is not proven until metadata is checked.

## Explain the author score

First average each reader's ratings across an author's works. Then score the author using these per-reader averages, so one prolific fan does not contribute dozens of votes. Use the mean of all reader/author averages as C, m = 100, at least 100 distinct readers, and the same country-support condition. This has a different prior and unit of analysis; author and book scores should not be compared directly.

All thresholds are understandable starting choices, not optimized parameters. The sensitivity output varies book m across 20, 50 and 100. It measures robustness, not recommendation accuracy.

## What appears on each page

| Books | Authors |
|---|---|
| Title and author | Author name |
| Representative ISBN, publisher, edition year | Historical reader count and number of rated works |
| Historical average rating and number of readers | Historical reader-balanced average rating |
| Adjusted score labelled as a recommendation score | Representative books from the candidate catalogue |
| Countries with sufficient reader support | Countries with sufficient reader support |
| Optional Google Books description, category, language, pages, cover and preview link | Optional reviewed Wikipedia biography and source link |

Descriptions and covers do not affect ranking. Exact ISBN matching is required for Google Books metadata. Wikipedia text is a candidate until checked. Metadata requests use timeouts, bounded retries and successful-response caching; errors are recorded without losing the rankings. Missing descriptions must remain missing, not invented.

The included enrichment run only attempts one book and one author as a connectivity check. Inspect `enrichment.json` for actual outcomes. Full enrichment is a follow-up run, not an accomplished result. Keep attribution/source links and review reuse terms before public deployment, even though the brief says copyright is not a priority.

## Validation and production follow-up

Six focused unit tests cover shrinkage, ranking, country handling, normalization and the author cap. A full-data run also asserts eligibility, score bounds, ISBN uniqueness and author diversity in the shortlist. The quality audit exposes losses at each relevant step; some audit categories overlap and must not be summed as a single waterfall.

For a real launch, obtain current customer interactions and market priorities, confirm language/stock/delivery availability, review series order, improve author/work identity, and validate enrichment. Pilot a curated list against the existing selection and compare click-through, add-to-cart and conversion by country. The historical dataset has no timestamps or sales outcomes; the prototype does not claim sales uplift or temporal validation.

At this volume, pandas is sufficient and avoids a dense user-by-book matrix. If memory or update volume becomes a problem, move joins/aggregations to SQL or DuckDB first; consider Spark only when measurements justify distribution. In production schedule runs, record completion/row counts, alert on failure or abnormal orphan rates, monitor metadata success rates, and keep the last validated catalogue on failure. These operational components are proposed, not implemented.

## Sources

- Supplied dataset: https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset
- Dataset provenance: https://dbis.informatik.uni-freiburg.de/forschung/projekte/2nd-Gen-RS/index.html
- Google Books API: https://developers.google.com/books/docs/v1/using
- Volume fields: https://developers.google.com/books/docs/v1/reference/volumes
- Wikipedia extracts API: https://www.mediawiki.org/wiki/Extension:TextExtracts

The source describes a four-week crawl in August/September 2004. Original published dataset counts can differ from this supplied CSV version; the audit always uses the supplied files.
