"""
EBooks Library - A comprehensive ebook search and download library

This library provides unified access to multiple ebook platforms including:
- Calibre-Web
- Z-Library  
- Archive.org
- Liber3
- Anna's Archive

Example:
    >>> from ebooks_library import EbooksLibrary
    >>> library = EbooksLibrary()
    >>> results = await library.search("Python programming")
    >>> book = results[0]
    >>> await library.download(book['download_info'], save_path="./downloads/")
"""

from .core import EbooksLibrary
from .models import BookInfo, SearchResult, DownloadInfo, LibraryConfig, Platform
from .exceptions import EbooksLibraryError, SearchError, DownloadError

__version__ = "1.0.0"
__author__ = "buding"
__all__ = [
    "EbooksLibrary",
    "BookInfo", 
    "SearchResult",
    "DownloadInfo",
    "LibraryConfig",
    "Platform",
    "EbooksLibraryError",
    "SearchError", 
    "DownloadError"
]
