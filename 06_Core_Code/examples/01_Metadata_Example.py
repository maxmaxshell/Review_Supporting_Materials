from pathlib import Path
import importlib.util
import json

def load_core(filename):
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

core = load_core('01_metadata_core.py')
work = {
    'id': 'EXAMPLE_BRIDGE_RECORD',
    'doi': 'https://doi.org/10.0000/example',
    'title': 'Example bridge structural health monitoring using edge computing',
    'publication_date': '2024-01-01',
    'publication_year': 2024,
    'language': 'en',
    'type': 'article',
    'abstract_inverted_index': {'Bridge': [0], 'monitoring': [1], 'example': [2]},
    'keywords': [{'display_name': 'structural health monitoring'}],
    'primary_location': {'source': {'id': 'S000000000', 'display_name': 'Example Journal'}},
    'authorships': [{}]
}

class ExampleClient:
    def request(self, provider, url, params=None, headers=None):
        if provider == 'openalex':
            return {'results': [work], 'meta': {'next_cursor': None}}
        return {'externalIds': {'DOI': '10.0000/example'}, 'title': work['title'], 'abstract': 'Example metadata response.'}

START_DATE, END_DATE, LANGUAGE = core.START_DATE, core.END_DATE, core.LANGUAGE
source = 'S000000000'
client = ExampleClient()
cursor = '*'
filters = ','.join(['primary_location.source.id:' + source, 'primary_location.source.type:journal', 'from_publication_date:' + START_DATE, 'to_publication_date:' + END_DATE, 'language:' + LANGUAGE, 'type:article|review'])
data = client.request('openalex', 'https://api.openalex.org/works', {'filter': filters, 'per_page': 100, 'cursor': cursor})
assert len(data['results']) == 1
print(json.dumps(core.normalize_openalex(data['results'][0]), ensure_ascii=False, indent=2))
print(json.dumps(core.provider_metadata(ExampleClient(), 'semantic_scholar', '10.0000/example'), indent=2))
