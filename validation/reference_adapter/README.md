# Reference adapter (kept for comparison)

`reference_adapter.py` is the Appendix A demo from the Mesa integration guide, unchanged. It renders
`selective_statistics` cases for a mock detector and checks the boundary between private simulation
state and detector-visible input.

Its `MockContractDetector` is a regular-expression parser for its own fixtures. Never use it on real
text, and never report its output as a detector result. The lab's own code is in `validation/biaslab/`.

```bash
MESA_BIAS_ROOT=validation/mesa_bias_expanded python validation/reference_adapter/reference_adapter.py
```
