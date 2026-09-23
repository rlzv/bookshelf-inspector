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