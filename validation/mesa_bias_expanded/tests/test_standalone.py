"""Portability check: embedded script must not depend on the plugin directory."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest
import expanded_mesa as engine
import export_single_file


@pytest.fixture(scope='module')
def isolated_script(tmp_path_factory):
    export_single_file.main()  # refuses incomplete or failing scope
    folder = tmp_path_factory.mktemp('standalone')
    path = folder / 'expanded_mesa_biases.py'
    path.write_bytes((engine.ROOT/'expanded_mesa_biases.py').read_bytes())
    return path


def launch(script, *args):
    env=dict(os.environ)
    env.pop('PYTHONPATH',None)
    return subprocess.run([sys.executable,str(script),*args],cwd=script.parent,
                          env=env,capture_output=True,text=True,timeout=120)


def test_standalone_lists_exact_138_without_modular_source(isolated_script):
    result=launch(isolated_script,'list')
    assert result.returncode==0,result.stderr
    assert len(json.loads(result.stdout))==138
    assert not (isolated_script.parent/'mechanisms').exists()


def test_standalone_full_contracts_pass_outside_checkout(isolated_script):
    output=isolated_script.parent/'coverage.json'
    result=launch(isolated_script,'validate','--output',str(output))
    assert result.returncode==0,result.stdout+result.stderr
    coverage=json.loads(output.read_text())
    assert coverage['passing_contracts']==138
    assert coverage['failed_or_missing_contracts']==0


def test_standalone_cli_paired_run_exports_real_data(isolated_script):
    output=isolated_script.parent/'demo'
    result=launch(isolated_script,'run','base_rate_fallacy','--agents','3',
                  '--replicates','2','--output',str(output))
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads((output/'failures.json').read_text())==[]
    metadata=json.loads((output/'run_metadata.json').read_text())
    assert metadata['replicates']==2
    assert metadata['synthetic_only'] is True
    assert len((output/'traces.jsonl').read_text().splitlines())>0
