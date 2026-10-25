from pathlib import Path
import importlib.util
import json

def load_core(filename):
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

from collections import defaultdict
from difflib import SequenceMatcher
import csv
import io

core = load_core('02_screening_core.py')
normalize_doi = core.normalize_doi
normalize = core.normalize

def find_candidates(records):
    doi_groups = defaultdict(list)
    title_groups = defaultdict(list)
    duplicate_holds = set()
    identities = set()
    counts = defaultdict(int)
    buffer = io.StringIO(newline='')
    candidates = csv.writer(buffer)
    for record in records:
        identity = record.get('openalex_id') or record.get('id')
        if not identity:
            raise ValueError('Record identity missing')
        if identity in identities:
            candidates.writerow([identity, identity, 'same_openalex_identity', 1, 1])
            counts['repeated_identity'] += 1
            continue
        identities.add(identity)
        result, route, _ = core.classify(record)
        doi = normalize_doi(record.get('doi'))
        title = normalize(record.get('title'))
        journal = record.get('journal_id') or record.get('journal') or ''
        year = record.get('publication_year')
        pool = doi_groups[doi] if doi else []
        for (other_id, other_title) in pool:
            duplicate_holds.update((identity, other_id))
            score = SequenceMatcher(None, title, other_title).ratio()
            candidates.writerow([identity, other_id, 'same_doi_requires_adjudication', score, 0])
            if result in ('original_research', 'review'):
                (result, route) = ('pending', 'duplicate_candidate_requires_adjudication')
        if doi:
            doi_groups[doi].append((identity, title))
        block = (journal, year, title[:12])
        for (other_id, other_title) in title_groups[block]:
            score = SequenceMatcher(None, title, other_title).ratio()
            if score >= 0.95:
                duplicate_holds.update((identity, other_id))
                candidates.writerow([identity, other_id, 'same_journal_year_title_similarity', score, 0])
                if result in ('original_research', 'review'):
                    (result, route) = ('pending', 'duplicate_candidate_requires_adjudication')
        title_groups[block].append((identity, title))
    return list(csv.reader(io.StringIO(buffer.getvalue()))), sorted(duplicate_holds)

record = {
    'openalex_id': 'EXAMPLE_A', 'title': 'Example bridge monitoring study',
    'doi': '10.0000/example', 'journal': 'Example Journal', 'publication_year': 2024
}
candidates, holds = find_candidates([record, dict(record, openalex_id='EXAMPLE_B'), record])
assert holds == ['EXAMPLE_A', 'EXAMPLE_B']
assert any(row[2] == 'same_openalex_identity' for row in candidates)
print(json.dumps({'candidates': candidates, 'review_required': holds}, indent=2))
