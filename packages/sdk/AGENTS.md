# packages/sdk rules
- Public API stays 2-line simple: init / log_params / log_metric / finish.
- Everything buffers to local disk and resyncs (Colab sessions drop).
- Framework hooks are strategies under integrations/.
- This ships to PyPI: keep the README and public surface pristine.
