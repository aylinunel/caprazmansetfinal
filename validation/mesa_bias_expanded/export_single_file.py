#!/usr/bin/env python3
"""Bundle only complete, passing implementations into one runnable Python script."""
import json
from pathlib import Path
import sys

import expanded_mesa as engine


def main():
    root=Path(__file__).resolve().parent
    report=engine.coverage()
    if report['failed_or_missing_contracts'] or report['expected_new_mechanisms']!=138:
        print('Refusing to export incomplete/failing scope. Run expanded_mesa.py validate for details.',file=sys.stderr)
        raise SystemExit(2)
    sources={concept:(root/'mechanisms'/f'{concept}.py').read_text(encoding='utf-8')
             for concept in engine.expected_ids()}
    code=(root/'expanded_mesa.py').read_text(encoding='utf-8')
    # future imports must precede any non-docstring statement in the exported file.
    future='from __future__ import annotations\n'
    code=code.replace(future,'',1)
    header='''#!/usr/bin/env python3
"""Standalone Mesa extension: 138 task-specific illustrative mechanisms.

Dependencies: pip install mesa==3.5.2 numpy
Usage: python expanded_mesa_biases.py list
       python expanded_mesa_biases.py describe base_rate_fallacy
       python expanded_mesa_biases.py run base_rate_fallacy --output demo
       python expanded_mesa_biases.py validate
       python expanded_mesa_biases.py sweep --agents 12 --replicates 3

Embedded process code is fixed at export. No user input is executed. This is not
empirically fitted psychology, a natural-language detector or a human diagnosis.
"""
from __future__ import annotations
'''
    destination=root/'expanded_mesa_biases.py'
    destination.write_text(header+'\nEMBEDDED_MANIFEST = '+repr(engine.manifest())+'\n\nEMBEDDED_SOURCES = '+repr(sources)+'\n\n'+code,encoding='utf-8')
    compile(destination.read_text(encoding='utf-8'),str(destination),'exec')
    print('Exported:',destination,'bytes:',destination.stat().st_size)


if __name__=='__main__':
    main()
