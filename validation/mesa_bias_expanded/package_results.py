#!/usr/bin/env python3
"""Package verified source, standalone script, tests, documentation and raw results."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT.parent/'mesa_bias_expanded_complete.zip'


def main():
    status=json.loads((ROOT/'results/FINAL_STATUS.json').read_text())
    if status.get('software_scope_complete') is not True:
        raise SystemExit('Refusing complete-package export: validation is incomplete.')
    required=[ROOT/'expanded_mesa_biases.py',ROOT/'README.md',ROOT/'VALIDATION.md',
              ROOT/'results/coverage.json',ROOT/'results/pytest_results.xml',
              ROOT/'results/sweep/summary.json']
    for file in required:
        if not file.is_file() or file.stat().st_size==0:
            raise SystemExit(f'Missing required deliverable: {file.name}')
    ids=[r['id'] for r in json.loads((ROOT/'missing_concepts.json').read_text())]
    assert len(set(ids))==138
    for concept in ids:
        for path in [ROOT/'mechanisms'/f'{concept}.py',ROOT/'tests'/f'test_{concept}.py',
                     ROOT/'specs'/f'{concept}_implementation.md']:
            assert path.is_file() and path.stat().st_size>0,path
    excluded={'.venv','__pycache__','.pytest_cache','.git'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and
           not excluded.intersection(p.relative_to(ROOT).parts) and
           p.name not in {'SHA256SUMS.json'} and p.suffix not in {'.pyc','.zip'}]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}
    hash_path=ROOT/'SHA256SUMS.json'
    hash_path.write_text(json.dumps(hashes,indent=2)+'\n')
    files.append(hash_path)
    with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(files):
            archive.write(path,Path('mesa_bias_expanded')/path.relative_to(ROOT))
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        for relative,sha in hashes.items():
            assert hashlib.sha256(archive.read('mesa_bias_expanded/'+relative)).hexdigest()==sha
    print('Complete package:',OUTPUT)
    print('Standalone script:',ROOT/'expanded_mesa_biases.py')
    print('Archived files:',len(files),'archive bytes:',OUTPUT.stat().st_size)


if __name__=='__main__':
    main()
