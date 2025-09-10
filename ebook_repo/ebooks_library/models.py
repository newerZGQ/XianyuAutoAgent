"""
Data models for ebooks library
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class Platform(Enum):
    """Supported ebook platforms"""
    CALIBRE_WEB = "calibre_web"
    ZLIBRARY = "zlibrary"
    ARCHIVE_ORG = "archive_org"
    LIBER3 = "liber3"
    ANNAS_ARCHIVE = "annas_archive"


@dataclass
class BookInfo:
    """Basic book information"""
    title: str
    authors: Optional[str] = None
    year: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    file_size: Optional[str] = None
    file_type: Optional[str] = None
    isbn: Optional[str] = None


@dataclass
class DownloadInfo:
    """Download information for a book"""
    platform: Platform
    download_url: Optional[str] = None
    book_id: Optional[str] = None
    hash_id: Optional[str] = None
    file_name: Optional[str] = None
    requires_auth: bool = False
    additional_params: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Search result containing book info and download info"""
    book_info: BookInfo
    download_info: DownloadInfo
    platform: Platform
    relevance_score: Optional[float] = None


@dataclass
class DownloadResult:
    """Result of a download operation"""
    success: bool
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    content: Optional[bytes] = None  # For in-memory downloads


@dataclass
class LibraryConfig:
    """Configuration for the ebooks library"""
    # Calibre-Web settings
    calibre_web_url: Optional[str] = None
    enable_calibre: bool = False
    
    # Z-Library settings  
    zlib_email: Optional[str] = None
    zlib_password: Optional[str] = None
    enable_zlib: bool = False
    
    # Archive.org settings
    enable_archive: bool = True
    
    # Liber3 settings
    enable_liber3: bool = True
    
    # Anna's Archive settings
    enable_annas: bool = False
    
    # General settings
    max_results: int = 20
    proxy: Optional[str] = None
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
