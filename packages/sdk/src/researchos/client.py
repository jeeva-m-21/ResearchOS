import os


class Client:
    """Idempotent, buffered ingest client. Resyncs if the session drops."""

    def __init__(self, project: str, api_key: str | None = None) -> None:
        self.project = project
        self.api_key = api_key or os.getenv("RESEARCHOS_API_KEY", "")

    def log_params(self, params: dict[str, object]) -> None: ...
    def log_metric(self, key: str, value: float, step: int | None = None) -> None: ...
    def log_artifact(self, kind: str, obj: object) -> None: ...
    def finish(self) -> None: ...  # snapshots code + env, computes repro score
