# Presentation and interview guide

## A five-minute presentation

**0:00–0:40 — Problem.** The client needs books and authors for an international catalogue. I chose a transparent ranking baseline because they need a shared editorial shortlist rather than personalized recommendations for logged-in customers.

**0:40–1:30 — Data.** Show the three CSVs and their join keys. Explain that zero means implicit feedback. Show the audit: missing catalogue matches, malformed records, author aliases and repeated editions matter before any scoring.

**1:30–2:30 — Method.** Explain the score as real votes plus 50 average votes. Explain minimum readers, country support and the two-books-per-author cap. For authors, each reader gets one averaged vote per author.

**2:30–3:30 — Results.** Open the shortlist and compare adjusted score, raw mean, readers and countries. Point out that the dataset is historically and geographically biased. It suggests an initial catalogue, not today's global demand. Sequels need editorial review.

**3:30–4:15 — Enrichment/demo.** Show `enrich.py`, exact ISBN checks, source links and statuses. Explain why an unavailable API must not stop ranking. Do not imply failed API calls produced metadata.

**4:15–5:00 — Next steps.** Current data, verified work IDs, stock/language checks and a measured catalogue pilot. Discuss SQL/scaling only after explaining the business result.

## Questions you should be able to answer

**Why no ML?** There is no requirement to personalize results to an individual. A weighted rating baseline directly solves the editorial selection problem and is easy to audit. ML can be compared later against this baseline when there is a measurable objective.

**Why not sort by average rating?** A single ten-star review is weak evidence. Shrinkage reduces the advantage of small samples.

**Why not sort by rating count?** Popularity is not satisfaction. Counts are valuable evidence but should not be the only criterion.

**Why keep zeros at all?** They represent observed implicit interactions and help describe reach or choose an edition. They are excluded from quality averages.

**Why m=50?** It is an explicit starting policy: the global average has the weight of 50 votes. I show sensitivity at 20 and 100 instead of claiming 50 is optimal.

**Why three countries and three readers per country?** It avoids calling one isolated foreign interaction international support. These are heuristic thresholds that should be adjusted to target markets and data volume.

**Does this remove US bias?** No. Cross-country eligibility prevents entirely local evidence, but the overall score is still reader-weighted. A next experiment would compare country-balanced scoring for agreed target countries, with minimum evidence per market.

**What is the difference between an ISBN and a work?** ISBN identifies an edition; the same story can have several editions. My title/author grouping is an approximate work ID and has documented limitations.

**What was the most useful cleaning fix?** Author-name variants split Tolkien across rankings. Explicit aliases fixed an observed problem without adding opaque fuzzy matching.

**How do you avoid joins multiplying rows?** Deduplicate catalogue/user keys, then enforce pandas `validate='many_to_one'`. At work level, collapse reader/edition votes before counting readers.

**What do you do with missing age?** Nothing: age is not needed for this business question. I do not invent demographic values.

**How do you validate API matches?** Require a returned ISBN match for a book. Author pages remain review candidates because names may be ambiguous. Store source, status and retrieval time.

**How do you know the ranking is good?** I have data-quality checks, logical tests and parameter sensitivity. Those do not prove business impact. A client review and a live controlled pilot would provide that evidence.

**How would SQL implement this?** Join ratings to books/users, filter explicit ratings, GROUP BY user/work to deduplicate votes, then GROUP BY work for count and mean. Apply the same formula and eligibility rules. Use ROW_NUMBER partitioned by author for a diversity cap.

**What would you monitor?** Successful scheduled completion, expected row counts, orphan joins, catalogue freshness and API success rates. Alert on failure and continue serving the last validated output.

**What would you spend the budget on?** First validate the value cheaply. If successful, prioritize current data, catalogue quality and controlled market experiments; infrastructure spend follows measured workload, not the size of the budget.

## Suggested work order before the deadline

1. Run the project and trace one book through the pipeline.
2. Recalculate its score by hand and explain each parameter.
3. Review the 20 selected books and 10 authors; mark series/language issues.
4. Try enrichment locally; keep observed failures transparent.
5. Rehearse the five-minute explanation with the code and CSVs open.
6. Only then add optional presentation polish. Avoid spending the final hours on a new web app or distributed infrastructure.

State your actual AI usage honestly: this starter was AI-assisted. Explain what you ran, inspected, corrected and understood yourself. Do not claim independent implementation if that is inaccurate.
