"""Execute the frozen edit stage only after out-of-band identity checks."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest_path = Path('feature_runs/compact_refiner/cr001-edit-v1/manifest.initial.json')
if sha(manifest_path) != '357ae56874a3be36da362c7841842c6d02fbf279a5c6c8218b64fd23fe0f29f2':
    raise SystemExit('Editing-stage manifest identity mismatch.')
parent = json.loads(Path('feature_runs/compact_refiner/cr001-v1/manifest.initial.json').read_text(encoding='utf-8'))
dataset = json.loads(Path('data/local/compact_refiner/cr001-v1/dataset_manifest.json').read_text(encoding='utf-8'))
actual = sha(Path('data/local/compact_refiner/cr001-v1/briefs.jsonl'))
if actual != parent['materialized_briefs_sha256'] or actual != dataset['briefs_sha256']:
    raise SystemExit('Materialized brief identity mismatch.')
raise SystemExit(subprocess.run([sys.executable, 'experiments/compact_refiner_edit_stage.py', 'run']).returncode)
