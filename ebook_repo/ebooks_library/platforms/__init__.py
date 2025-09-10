"""
Platform implementations for different ebook sources
"""

from .base import BasePlatform
from .calibre_web import CalibreWebPlatform
from .zlibrary import ZLibraryPlatform
from .archive_org import ArchiveOrgPlatform
from .liber3 import Liber3Platform
from .annas_archive import AnnasArchivePlatform

__all__ = [
    "BasePlatform",
    "CalibreWebPlatform", 
    "ZLibraryPlatform",
    "ArchiveOrgPlatform",
    "Liber3Platform",
    "AnnasArchivePlatform"
]
