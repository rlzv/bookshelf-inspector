"""Optional, cached API enrichment. The ranking pipeline works without network access."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd


def fetch(base, params, cache):
    # Cache identity excludes credentials. Failed requests are not cached.
    cache.mkdir(parents=True, exist_ok=True)
    identity = base + '?' + urllib.parse.urlencode(params)
    path = cache / (hashlib.sha256(identity.encode()).hexdigest() + '.json')
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    if 'googleapis.com' in base and os.getenv('GOOGLE_BOOKS_API_KEY'):
        params = {**params, 'key': os.environ['GOOGLE_BOOKS_API_KEY']}
    url = base + '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent': 'BookshelfInspectorAcademy/0.1'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.load(response)
            payload = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'data': data}
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code not in [429, 500, 502, 503, 504] or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def book_metadata(row, cache):
    payload = fetch('https://www.googleapis.com/books/v1/volumes', {'q': 'isbn:' + row.isbn}, cache)
    for item in payload['data'].get('items', []):
        info = item.get('volumeInfo', {})
        ids = [v.get('identifier', '').replace('-', '') for v in info.get('industryIdentifiers', [])]
        if row.isbn not in ids:
            continue
        return {'isbn': row.isbn, 'status': 'matched_isbn', 'source': item.get('selfLink'),
                'retrieved_at': payload['retrieved_at'], 'description': info.get('description'),
                'categories': info.get('categories'), 'language': info.get('language'),
                'page_count': info.get('pageCount'), 'cover_url': info.get('imageLinks', {}).get('thumbnail'),
                'preview_url': info.get('previewLink')}
    return {'isbn': row.isbn, 'status': 'no_exact_isbn_match'}


def author_metadata(row, cache):
    payload = fetch('https://en.wikipedia.org/w/api.php', {
        'action': 'query', 'format': 'json', 'titles': row.author, 'redirects': 1,
        'prop': 'extracts|info|pageprops', 'exintro': 1, 'explaintext': 1,
        'exchars': 650, 'inprop': 'url'}, cache)
    for page in payload['data'].get('query', {}).get('pages', {}).values():
        if 'missing' in page or 'disambiguation' in page.get('pageprops', {}):
            continue
        return {'author': row.author, 'status': 'needs_editorial_identity_review',
                'candidate_title': page.get('title'), 'biography_candidate': page.get('extract'),
                'source': page.get('fullurl'), 'retrieved_at': payload['retrieved_at']}
    return {'author': row.author, 'status': 'no_unambiguous_page'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('output'))
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    results = {'books': [], 'authors': []}
    for kind, file, fn in [('books', 'books_top20.csv', book_metadata),
                           ('authors', 'authors_top10.csv', author_metadata)]:
        frame = pd.read_csv(args.output / file, dtype={'isbn': str})
        for row in frame.head(args.limit).itertuples():
            try:
                results[kind].append(fn(row, args.output / 'api_cache'))
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                # Never log full request URLs: they may contain API keys.
                results[kind].append({'identity': row.isbn if kind == 'books' else row.author,
                                      'status': 'request_failed', 'error_type': type(exc).__name__})
            time.sleep(0.2)
    (args.output / 'enrichment.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Saved enrichment.json; inspect statuses before displaying any metadata.')


if __name__ == '__main__':
    main()
