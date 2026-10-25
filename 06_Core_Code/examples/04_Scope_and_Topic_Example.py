from pathlib import Path
import importlib.util
import json

def load_core(filename):
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

core = load_core('03_scope_and_topic_core.py')
scope, topic = core.configure_matchers()
record = {
    'title': 'Bridge structural health monitoring using wireless sensor networks and edge computing',
    'abstract': 'Synchronized acceleration measurements support modal identification and data quality control.',
    'keyword_channels': {'author_keywords': ['operational modal analysis', 'time synchronization']}
}
result = core.analyze_record(record, scope, topic)
assert result['domain'] == 'bridge'
assert result['keyword_policy'] == 'documentary'
assert 'T01' in result['themes']
groups = ['G' + str(i + 1) for i in range(8) if result['group_mask'] & (1 << i)]
print(json.dumps(dict(result, groups=groups), indent=2))
