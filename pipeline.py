"""Explainable catalogue recommendations. Run: python pipeline.py --archive ../archive.zip"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import zipfile

import pandas as pd

# Deliberately conservative: unrecognised free-text locations stay unknown.
COUNTRIES = '''usa|canada|united kingdom|germany|spain|australia|italy|france|portugal|new zealand|netherlands|switzerland|brazil|china|sweden|india|austria|malaysia|argentina|singapore|finland|mexico|belgium|denmark|ireland|philippines|turkey|poland|pakistan|japan|south africa|norway|greece|romania|czechia|slovakia|hungary|israel|russia|indonesia|thailand|south korea|chile|colombia|peru|venezuela|egypt|iceland|croatia|slovenia|estonia|latvia|lithuania|ukraine|taiwan|hong kong|luxembourg|malta|cyprus|united arab emirates'''.split('|')
ALIASES = {'united states': 'usa', 'united states of america': 'usa', 'u.s.a.': 'usa',
           'us': 'usa', 'uk': 'united kingdom', 'england': 'united kingdom',
           'scotland': 'united kingdom', 'wales': 'united kingdom',
           'czech republic': 'czechia', 'republic of korea': 'south korea'}


def normalize(value):
    """Keep punctuation/accents to avoid aggressive false merges."""
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(value))).strip().casefold()


def country(location):
    value = normalize(str(location).rsplit(',', 1)[-1]).strip('" ')
    value = ALIASES.get(value, value)
    return value if value in COUNTRIES else pd.NA


def adjusted_score(mean, count, prior, strength):
    return (count * mean + strength * prior) / (count + strength)


def rank(frame, key, prior, strength):
    scores = frame.groupby(key).agg(readers=('user_id', 'nunique'),
                                    average_rating=('rating', 'mean'))
    scores['score'] = adjusted_score(scores.average_rating, scores.readers, prior, strength)
    return scores.sort_values(['score', 'readers', key], ascending=[False, False, True])


def shortlist(ranked, n=20, per_author=2):
    counts, selected = {}, []
    for idx, row in ranked.iterrows():
        author = row['author_key']
        if counts.get(author, 0) < per_author:
            selected.append(idx)
            counts[author] = counts.get(author, 0) + 1
        if len(selected) == n:
            break
    return ranked.loc[selected].copy()


def run(archive, output, min_readers=50, min_countries=3, strength=50):
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        books = pd.read_csv(z.open('Books.csv'), dtype=str).rename(columns={
            'ISBN': 'isbn', 'Book-Title': 'title', 'Book-Author': 'author',
            'Year-Of-Publication': 'year', 'Publisher': 'publisher', 'Image-URL-L': 'cover_url'})
        users = pd.read_csv(z.open('Users.csv'), usecols=['User-ID', 'Location']).rename(
            columns={'User-ID': 'user_id', 'Location': 'location'})
        ratings = pd.read_csv(z.open('Ratings.csv'), dtype={'ISBN': str}).rename(
            columns={'User-ID': 'user_id', 'ISBN': 'isbn', 'Book-Rating': 'rating'})
    quality = {'raw_books': len(books), 'raw_users': len(users), 'raw_ratings': len(ratings),
               'zero_ratings': int(ratings.rating.eq(0).sum())}
    for frame in [books, ratings]:
        frame['isbn'] = frame.isbn.str.strip().str.upper()
    for col in ['title', 'author']:
        books[col] = books[col].fillna('').str.strip()
    years = pd.to_numeric(books.year, errors='coerce')
    # Shifted CSV rows cannot safely supply titles/authors. Retain them for inspection.
    malformed = years.isna() | books.title.eq('') | books.author.eq('')
    books.loc[malformed].to_csv(output / 'quarantined_books.csv', index=False)
    quality['quarantined_books'] = int(malformed.sum())
    quality['duplicate_isbns'] = int(books.isbn.duplicated().sum())
    books = books.loc[~malformed].drop_duplicates('isbn').copy()
    valid_year = years.between(1450, 2004)
    quality['unknown_or_implausible_years_retained'] = int((~valid_year.loc[books.index]).sum())
    books['year'] = years.loc[books.index].where(valid_year.loc[books.index]).astype('Int64')
    aliases = pd.read_csv(Path(__file__).with_name('author_aliases.csv'))
    alias_map = dict(zip(aliases.alias.map(normalize), aliases.canonical))
    books['author'] = books.author.map(lambda value: alias_map.get(normalize(value), value))
    books['author_key'] = books.author.map(normalize)
    books['work_key'] = books.title.map(normalize) + ' || ' + books.author_key
    quality['approximate_works'] = int(books.work_key.nunique())
    quality['duplicate_user_ids'] = int(users.user_id.duplicated().sum())
    users = users.drop_duplicates('user_id').copy()
    users['country'] = users.location.map(country)
    quality['users_unknown_country'] = int(users.country.isna().sum())
    valid_rating = ratings.rating.between(0, 10) & ratings.rating.mod(1).eq(0)
    quality['invalid_rating_rows'] = int((~valid_rating).sum())
    ratings = ratings.loc[valid_rating].drop_duplicates().copy()
    quality['exact_duplicate_rating_rows'] = quality['raw_ratings'] - quality['invalid_rating_rows'] - len(ratings)
    quality['conflicting_user_isbn_rows'] = int(ratings.duplicated(['user_id', 'isbn'], keep=False).sum())
    # No timestamps: quarantine conflicting user/ISBN observations rather than picking a latest value.
    ratings = ratings.loc[~ratings.duplicated(['user_id', 'isbn'], keep=False)].copy()
    quality['ratings_without_usable_book'] = int((~ratings.isbn.isin(books.isbn)).sum())
    quality['ratings_without_user'] = int((~ratings.user_id.isin(users.user_id)).sum())
    joined = ratings.merge(books, on='isbn', validate='many_to_one').merge(
        users[['user_id', 'country']], on='user_id', how='left', validate='many_to_one')
    interactions = joined.groupby('work_key').user_id.nunique().rename('interaction_readers')
    # Collapse editions before scoring: one reader cannot vote repeatedly for a work.
    explicit = joined.loc[joined.rating.gt(0)].groupby(['user_id', 'work_key'], as_index=False).agg(
        rating=('rating', 'mean'), country=('country', 'first'), author_key=('author_key', 'first'))
    quality['explicit_user_work_pairs'] = len(explicit)
    quality['joined_explicit_rows'] = int(joined.rating.gt(0).sum())
    prior = float(explicit.rating.mean())
    # Country evidence requires >= 3 distinct explicit readers within a country.
    country_counts = explicit.dropna(subset=['country']).groupby(['work_key', 'country']).user_id.nunique()
    supported = country_counts[country_counts.ge(3)].groupby('work_key').size().rename('supported_countries')
    ranked = rank(explicit, 'work_key', prior, strength).join(supported).join(interactions)
    ranked['supported_countries'] = ranked.supported_countries.fillna(0).astype(int)
    # Choose a representative edition by observed interaction count, then ISBN for ties.
    edition_counts = joined.groupby('isbn').size().rename('edition_interactions')
    representatives = books.join(edition_counts, on='isbn').sort_values(
        ['edition_interactions', 'isbn'], ascending=[False, True]).drop_duplicates('work_key').set_index('work_key')
    ranked = ranked.join(representatives[['isbn', 'title', 'author', 'author_key', 'year', 'publisher', 'cover_url']])
    eligible = ranked.loc[ranked.readers.ge(min_readers) & ranked.supported_countries.ge(min_countries)]
    top = shortlist(eligible)
    top.to_csv(output / 'books_top20.csv', index=False)
    eligible.head(100).to_csv(output / 'books_ranked_top100.csv', index=False)

    # Author scoring: first average each reader's ratings for an author, then average readers.
    author_votes = explicit.groupby(['user_id', 'author_key'], as_index=False).agg(
        rating=('rating', 'mean'), country=('country', 'first'))
    author_prior = float(author_votes.rating.mean())
    authors = rank(author_votes, 'author_key', author_prior, strength=100)
    authors = authors.join(explicit.groupby('author_key').work_key.nunique().rename('rated_works'))
    ac = author_votes.dropna(subset=['country']).groupby(['author_key', 'country']).user_id.nunique()
    authors = authors.join(ac[ac.ge(3)].groupby('author_key').size().rename('supported_countries'))
    authors['supported_countries'] = authors.supported_countries.fillna(0).astype(int)
    labels = books.groupby('author_key').author.agg(lambda x: x.value_counts().index[0])
    authors = authors.join(labels)
    top_authors = authors.loc[authors.readers.ge(100) & authors.supported_countries.ge(min_countries)].head(10)
    top_authors.to_csv(output / 'authors_top10.csv', index=True)
    coverage = explicit.drop_duplicates('user_id').groupby('country', dropna=False).agg(readers=('user_id', 'nunique'))
    coverage.sort_values('readers', ascending=False).to_csv(output / 'audience_countries.csv')

    # Small robustness check: how much does the selected list change with the prior strength?
    sensitivity = []
    for m in [20, 50, 100]:
        variant = eligible.copy()
        variant['score'] = adjusted_score(variant.average_rating, variant.readers, prior, m)
        variant = variant.sort_values(['score', 'readers', 'work_key'], ascending=[False, False, True])
        picks = shortlist(variant)
        sensitivity.append({'prior_strength': m, 'top20_overlap_with_configured_run': len(set(picks.index) & set(top.index))})
    pd.DataFrame(sensitivity).to_csv(output / 'sensitivity.csv', index=False)
    quality.update({'book_prior_mean': prior, 'author_prior_mean': author_prior,
                    'eligible_books': len(eligible), 'selected_books': len(top),
                    'selected_authors': len(top_authors), 'min_readers': min_readers,
                    'min_supported_countries': min_countries, 'book_prior_strength': strength,
                    'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()})
    (output / 'quality_report.json').write_text(json.dumps(quality, indent=2), encoding='utf-8')
    assert top.readers.ge(min_readers).all()
    assert top.supported_countries.ge(min_countries).all()
    assert top.groupby('author_key').size().le(2).all()
    assert top.score.between(1, 10).all()
    assert top.isbn.is_unique
    print(json.dumps(quality, indent=2))
    print(top[['title', 'author', 'readers', 'score']].to_string(index=False))
    print(top_authors[['author', 'readers', 'score']].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('output'))
    parser.add_argument('--min-readers', type=int, default=50)
    parser.add_argument('--min-countries', type=int, default=3)
    parser.add_argument('--strength', type=float, default=50)
    args = parser.parse_args()
    if args.min_readers < 1 or args.min_countries < 1 or args.strength <= 0:
        parser.error('Thresholds and strength must be positive.')
    run(args.archive, args.output, args.min_readers, args.min_countries, args.strength)
