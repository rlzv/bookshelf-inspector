# Results from the supplied archive

## Recommendation

Use the 20-book and 10-author lists below as candidates for an international catalogue pilot. Have an editor check series order, language, current availability and metadata before publication. For example, The Two Towers is a sequel: its high score does not make it the best entry point for a new reader.

## Dataset and quality findings

- 271,360 raw book rows, 278,858 users and 1,149,780 rating records.
- 716,109 zeros (62.3%) represent implicit feedback; excluded from quality averages.
- 5 book records quarantined; 315 duplicate ISBN rows after normalization collapsed.
- 4,685 retained books have unknown/implausible publication years, set to null.
- 118,647 rating rows cannot join to a usable book (10.3% of raw interactions).
- 382,922 explicit reader/work observations after edition collapsing.
- 256 eligible book candidates; 20 chosen with the author cap.
- Mean explicit reader/work rating: 7.6255/10.

The USA accounts for 44,149 of 68,091 distinct readers with at least one joined explicit rating (64.8%, including unknown-country readers in the denominator). Requiring several countries does not make the sample representative of the world. The data is from a 2004 crawl, not a measure of 2026 trends.

## Selected books, in recommendation order

| title | author | readers | average_rating | score | supported_countries |
| --- | --- | --- | --- | --- | --- |
| The Two Towers (The Lord of the Rings, Part 2) | J. R. R. Tolkien | 135 | 9.333 | 8.872 | 4 |
| Harry Potter and the Goblet of Fire (Book 4) | J. K. Rowling | 242 | 9.114 | 8.859 | 5 |
| The Return of the King (The Lord of the Rings, Part 3) | J. R. R. Tolkien | 117 | 9.342 | 8.828 | 3 |
| Harry Potter and the Prisoner of Azkaban (Book 3) | J. K. Rowling | 274 | 9.046 | 8.826 | 7 |
| To Kill a Mockingbird | Harper Lee | 266 | 8.977 | 8.764 | 6 |
| Ender's Game (Ender Wiggins Saga (Paperback)) | Orson Scott Card | 150 | 8.92 | 8.596 | 3 |
| The Little Prince | Antoine de Saint-Exupéry | 90 | 9.111 | 8.581 | 5 |
| 1984 | George Orwell | 143 | 8.783 | 8.483 | 6 |
| Dune (Remembering Tomorrow) | Frank Herbert | 75 | 8.973 | 8.434 | 4 |
| Tuesdays with Morrie: An Old Man, a Young Man, and Life's Greatest Lesson | MITCH ALBOM | 249 | 8.582 | 8.422 | 5 |
| 84 Charing Cross Road | Helene Hanff | 59 | 9.073 | 8.409 | 4 |
| A Prayer for Owen Meany | John Irving | 182 | 8.615 | 8.402 | 4 |
| The Secret Life of Bees | Sue Monk Kidd | 402 | 8.471 | 8.378 | 4 |
| The Da Vinci Code | Dan Brown | 494 | 8.439 | 8.364 | 8 |
| Fahrenheit 451 | RAY BRADBURY | 198 | 8.53 | 8.348 | 4 |
| The Subtle Knife (His Dark Materials, Book 2) | PHILIP PULLMAN | 107 | 8.673 | 8.339 | 4 |
| Anne of Green Gables (Anne of Green Gables Novels (Paperback)) | L. M. Montgomery | 66 | 8.879 | 8.339 | 3 |
| The Color Purple | Alice Walker | 144 | 8.583 | 8.336 | 5 |
| Watership Down | Richard Adams | 122 | 8.574 | 8.298 | 5 |
| Anne Frank: The Diary of a Young Girl | ANNE FRANK | 79 | 8.722 | 8.297 | 3 |

## Selected authors

| author | readers | rated_works | average_rating | score | supported_countries |
| --- | --- | --- | --- | --- | --- |
| J. K. Rowling | 1013 | 61 | 8.827 | 8.712 | 14 |
| Harper Lee | 280 | 7 | 8.986 | 8.607 | 7 |
| J. R. R. Tolkien | 731 | 123 | 8.712 | 8.572 | 16 |
| Antoine de Saint-Exupéry | 205 | 33 | 8.957 | 8.495 | 9 |
| Bill Watterson | 143 | 36 | 9.068 | 8.442 | 5 |
| Dr. Seuss | 131 | 31 | 9.089 | 8.421 | 3 |
| L. M. Montgomery | 191 | 66 | 8.758 | 8.342 | 7 |
| Anne Frank | 169 | 18 | 8.719 | 8.283 | 7 |
| Sue Monk Kidd | 404 | 3 | 8.464 | 8.282 | 4 |
| E. B. White | 141 | 10 | 8.783 | 8.27 | 3 |

Scores are adjusted ranking values out of 10, not raw ratings or probabilities. Supported countries means at least three distinct explicit readers in each country.

## Largest audience groups

| country | readers |
| --- | --- |
| usa | 44149 |
| canada | 6239 |
| germany | 3531 |
| united kingdom | 2971 |
| nan | 2443 |
| australia | 1801 |
| spain | 1669 |
| france | 802 |
| italy | 774 |
| new zealand | 459 |

## Sensitivity

| prior_strength | top20_overlap_with_configured_run |
| --- | --- |
| 20 | 17 |
| 50 | 20 |
| 100 | 18 |

The overlap is measured after applying the same eligibility rules and author cap. Stability to this one parameter is not proof of commercial value. Reader/country thresholds, work identity and editorial constraints also affect results.

## Verification and unfinished work

The full pipeline completed on the supplied archive. Six unit tests passed, and all shortlist assertions passed. API enrichment was attempted separately; see enrichment.json for outcomes. The network-independent ranking is complete. A full enriched catalogue, human identity review, current-market validation, a website and production scheduling are not completed.

Observed enrichment smoke check: Google Books request failed; Wikipedia returned a J. K. Rowling biography candidate with its source and retrieval time. No book description is claimed. Run full enrichment locally after resolving API access/quota.
