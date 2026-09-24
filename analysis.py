import zipfile
import pandas as pd
from pathlib import Path


# Open the dataset archive without extracting it.
with zipfile.ZipFile("archive.zip") as archive:
    books = pd.read_csv(
        archive.open("Books.csv"),
        dtype=str,
    )

    ratings = pd.read_csv(
        archive.open("Ratings.csv"),
        dtype={"ISBN": str},
    )

    users = pd.read_csv(
        archive.open("Users.csv"),
    )


# Inspect each dataset.
for name, data in [
    ("Books", books),
    ("Ratings", ratings),
    ("Users", users),
]:
    print(f"\n--- {name} ---")
    print(f"Rows: {len(data):,}")
    print("Columns:", data.columns.tolist())
    print(data.head(3).to_string(index=False))


# Count how often each rating value appears.
print("\n--- Rating distribution ---")
print(ratings["Book-Rating"].value_counts().sort_index())

# Keep explicit ratings for calculating book quality.
explicit_ratings = ratings[
    ratings["Book-Rating"].between(1, 10)
].copy()

print(f"\nAll interactions: {len(ratings):,}")
print(f"Explicit ratings: {len(explicit_ratings):,}")
print(f"Zero ratings: {(ratings['Book-Rating'] == 0).sum():,}")

# Calculate rating statistics for each book edition.
book_stats = (
    explicit_ratings.groupby("ISBN")
    .agg(
        rating_count=("Book-Rating", "count"),
        average_rating=("Book-Rating", "mean"),
    )
    .reset_index()
)

print("\n--- Book rating statistics ---")
print(book_stats.head(10).to_string(index=False))
print(f"\nISBNs with explicit ratings: {len(book_stats):,}")

# Require enough feedback before recommending a book.
minimum_ratings = 50

popular_books = book_stats[
    book_stats["rating_count"] >= minimum_ratings
].copy()


# Correct known spelling and encoding variations.
author_corrections = {
    "antoine de saint-exupã©ry": "Antoine de Saint-Exupéry",
    "antoine de saint-exupery": "Antoine de Saint-Exupéry",
    "antoine de saint-exupéry": "Antoine de Saint-Exupéry",
    "j.r.r. tolkien": "J. R. R. Tolkien",
    "j. r. r. tolkien": "J. R. R. Tolkien",
    "j.k. rowling": "J. K. Rowling",
    "j. k. rowling": "J. K. Rowling",
    "l.m. montgomery": "L. M. Montgomery",
    "l. m. montgomery": "L. M. Montgomery",
}

# Build comparable names for looking up corrections.
author_names = books["Book-Author"].str.strip().str.casefold()

corrected_names = author_names.map(author_corrections)

# Keep the original name when no correction is listed.
books["Book-Author"] = corrected_names.fillna(books["Book-Author"])

# Keep the catalogue columns we need.
book_details = books[
    ["ISBN", "Book-Title", "Book-Author"]
].drop_duplicates(subset="ISBN")


# Attach titles and authors to books with at least 50 ratings.
ranked_books = popular_books.merge(
    book_details,
    on="ISBN",
    how="inner",
    validate="one_to_one",
)

# Create consistent labels for comparing titles and authors.
ranked_books["title_key"] = (
    ranked_books["Book-Title"].str.strip().str.casefold()
)

ranked_books["author_key"] = (
    ranked_books["Book-Author"].str.strip().str.casefold()
)

# For matching titles and authors, keep the edition with most ratings.
unique_books = (
    ranked_books.sort_values(
        by=["rating_count", "ISBN"],
        ascending=[False, True],
    )
    .drop_duplicates(subset=["title_key", "author_key"])
)

# Rank the remaining editions by their average rating.
top_books = unique_books.sort_values(
    by=["average_rating", "rating_count", "ISBN"],
    ascending=[False, False, True],
).head(20)

print("\n--- Top 20 books ---")

print(
    top_books[
        [
            "Book-Title",
            "Book-Author",
            "rating_count",
            "average_rating",
        ]
    ].round(2).to_string(index=False)
)

print(f"\nEligible editions: {len(ranked_books):,}")
print(f"Unique title-author pairs: {len(unique_books):,}")
print(f"Selected recommendations: {len(top_books)}")

# Create a separate folder for our simplified analysis results.
output_folder = Path("output/simple")
output_folder.mkdir(parents=True, exist_ok=True)

# Select the columns useful to the client.
recommendations = top_books[
    [
        "ISBN",
        "Book-Title",
        "Book-Author",
        "rating_count",
        "average_rating",
    ]
].copy()

recommendations["average_rating"] = (
    recommendations["average_rating"].round(2)
)

# Save without the pandas row index.
output_file = output_folder / "recommended_books.csv"

recommendations.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
)

print(f"\nSaved {len(recommendations)} recommendations to {output_file}")

# Attach author information to each explicit rating.
author_ratings = explicit_ratings.merge(
    book_details,
    on="ISBN",
    how="inner",
    validate="many_to_one",
)

# Exclude records without an author.
author_ratings = author_ratings.dropna(subset=["Book-Author"])

# Group names consistently despite capitalisation and extra spaces.
author_ratings["author_key"] = (
    author_ratings["Book-Author"].str.strip().str.casefold()
)

author_ratings = author_ratings[
    author_ratings["author_key"] != ""
].copy()

# Calculate statistics for each author.
author_stats = (
    author_ratings.groupby("author_key")
    .agg(
        author=("Book-Author", "first"),
        rating_count=("Book-Rating", "count"),
        reader_count=("User-ID", "nunique"),
        average_rating=("Book-Rating", "mean"),
    )
    .reset_index()
)

print("\n--- Author statistics ---")
print(
    author_stats[
        ["author", "rating_count", "reader_count", "average_rating"]
    ].head(10).round(2).to_string(index=False)
)

print(f"\nAuthor groups: {len(author_stats):,}")

# Require feedback from at least 100 different readers.
minimum_readers = 100

eligible_authors = author_stats[
    author_stats["reader_count"] >= minimum_readers
].copy()

# Select the highest-rated eligible authors.
top_authors = eligible_authors.sort_values(
    by=["average_rating", "reader_count", "author_key"],
    ascending=[False, False, True],
).head(10)

print("\n--- Top 10 authors ---")
print(
    top_authors[
        ["author", "rating_count", "reader_count", "average_rating"]
    ].round(2).to_string(index=False)
)

print(f"\nEligible author groups: {len(eligible_authors):,}")

# Select the author information useful to the client.
author_recommendations = top_authors[
    ["author", "rating_count", "reader_count", "average_rating"]
].copy()

author_recommendations["average_rating"] = (
    author_recommendations["average_rating"].round(2)
)

author_output_file = output_folder / "recommended_authors.csv"

author_recommendations.to_csv(
    author_output_file,
    index=False,
    encoding="utf-8-sig",
)

print(
    f"\nSaved {len(author_recommendations)} author recommendations "
    f"to {author_output_file}"
)