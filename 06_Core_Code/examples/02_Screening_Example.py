from pathlib import Path
import importlib.util
import json

def load_core(filename):
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

core = load_core('02_screening_core.py')
record = {
    'title': 'Correction: Example bridge monitoring article',
    'doi': '10.0000/example-correction',
    'abstract': 'Correction notice for an example article.',
    'keyword_channels': {'author_keywords': ['bridge monitoring']},
    'authorship_count': 1
}
result, reason, proposals = core.classify(record)
assert result == 'excluded'
print(json.dumps({'classification': result, 'reason': reason, 'rule_proposals': proposals}, indent=2))
