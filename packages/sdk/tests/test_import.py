import researchos as ros


def test_public_surface() -> None:
    for fn in ("init", "log_params", "log_metric", "log_artifact", "finish"):
        assert hasattr(ros, fn)
