import zipfile

import pandas as pd


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

top_books = popular_books.sort_values(
    by=["average_rating", "rating_count", "ISBN"],
    ascending=[False, False, True],
).head(20)

print("\n--- Top 20 ISBNs with at least 50 ratings ---")
print(top_books.to_string(index=False))