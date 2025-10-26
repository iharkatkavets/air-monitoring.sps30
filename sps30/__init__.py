from importlib import metadata as _metadata

from .sps30 import SPS30  # re-export

__all__ = ["SPS30"]
try:
    __version__ = _metadata.version("sps30")
except _metadata.PackageNotFoundError:
    __version__ = "0.0.0"
