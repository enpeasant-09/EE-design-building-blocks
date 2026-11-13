from .base import Provider, ProviderNotConfigured
from .digikey import DigiKeyProvider
from .mock import FileProvider
from .mouser import MouserProvider
from .nexar import NexarProvider

REGISTRY = {
    "octopart": NexarProvider,
    "nexar": NexarProvider,
    "digikey": DigiKeyProvider,
    "mouser": MouserProvider,
    "file": FileProvider,
}

__all__ = ["Provider", "ProviderNotConfigured", "REGISTRY"]
