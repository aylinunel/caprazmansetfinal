# Mesa simulator: vendor check

- Source: `mesa_bias_expanded_complete.zip` supplied by the owner on 14 November 2026.
- Vendored to `validation/mesa_bias_expanded/`, excluding `results/sweep/`, `results/sweep_first_attempt/`
  and `results/pytest_results.xml` (35 MB of run output).
- Every vendored file matches `SHA256SUMS.json` (`validation/tests/test_vendored.py`).
- Suite re-run on 14 November 2026: **1531 passed**, Python 3.13.18, Mesa 3.5.2, NumPy 2.5.3, pytest 9.2.0.
- These are software tests of authored toy mechanisms. They are not evidence of detector accuracy.
