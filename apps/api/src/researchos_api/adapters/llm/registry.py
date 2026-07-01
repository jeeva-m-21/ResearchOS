from ...ports.llm import LLMProvider
from .deepseek import DeepSeekProvider

_PROVIDERS = {"deepseek": DeepSeekProvider}


def get_llm(name: str = "deepseek") -> LLMProvider:
    """Factory: name -> LLMProvider. Add providers here, not in the domain."""
    return _PROVIDERS[name]()
