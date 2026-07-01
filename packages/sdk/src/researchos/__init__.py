from .client import Client

_client: Client | None = None


def init(project: str, api_key: str | None = None) -> None:
    global _client
    _client = Client(project=project, api_key=api_key)


def log_params(params: dict[str, object]) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_params(params)


def log_metric(key: str, value: float, step: int | None = None) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_metric(key, value, step)


def log_artifact(kind: str, obj: object) -> None:
    assert _client is not None, "call ros.init() first"
    _client.log_artifact(kind, obj)


def finish() -> None:
    assert _client is not None, "call ros.init() first"
    _client.finish()
