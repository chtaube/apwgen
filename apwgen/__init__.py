from .apwgen import *
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("apwgen")
except PackageNotFoundError:
    __version__ = None

