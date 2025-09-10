"""
Anna's Archive platform implementation
"""

import logging
from typing import List, Optional, Union
from pathlib import Path

from .base import BasePlatform
from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo, Platform
from ..exceptions import SearchError, DownloadError
from ..adapters.annas_py import search as annas_search, get_information as get_annas_information
from ..adapters.annas_py.models.args import Language


logger = logging.getLogger(__name__)


class AnnasArchivePlatform(BasePlatform):
    """Anna's Archive platform implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search Anna's Archive for ebooks"""
        try:
            # Use the existing annas_py search function
            results = annas_search(query, Language.ZH)
            
            if not results:
                return []
            
            search_results = []
            for book in results[:limit]:
                book_info = BookInfo(
                    title=book.title,
                    authors=book.authors,
                    publisher=book.publisher,
                    year=book.publish_date,
                    language=book.file_info.language if book.file_info else "Unknown",
                    file_type=book.file_info.extension if book.file_info else "Unknown",
                    cover_url=book.thumbnail
                )
                
                download_info = DownloadInfo(
                    platform=Platform.ANNAS_ARCHIVE,
                    book_id=book.id,
                    requires_auth=False
                )
                
                search_result = SearchResult(
                    book_info=book_info,
                    download_info=download_info,
                    platform=Platform.ANNAS_ARCHIVE
                )
                
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} results from Anna's Archive")
            return search_results
            
        except Exception as e:
            logger.error(f"Anna's Archive search failed: {e}")
            raise SearchError(f"Anna's Archive search failed: {str(e)}", "annas_archive")
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """
        Anna's Archive doesn't support direct downloads.
        This method returns download links instead.
        """
        try:
            if not download_info.book_id:
                raise DownloadError("Anna's Archive download requires book_id", "annas_archive")
            
            # Get download information
            book_info = get_annas_information(download_info.book_id)
            urls = book_info.urls
            
            if not urls:
                raise DownloadError("No download links found for this book", "annas_archive")
            
            # Anna's Archive doesn't support direct download
            # Return information about available download links
            links_info = []
            
            # Fast links (paid)
            fast_links = [url for url in urls if "Fast Partner Server" in url.title]
            if fast_links:
                links_info.append("Fast links (paid):")
                for i, url in enumerate(fast_links, 1):
                    links_info.append(f"  {i}. {url.url}")
            
            # Slow links (free with wait)
            slow_links = [url for url in urls if "Slow Partner Server" in url.title]
            if slow_links:
                links_info.append("Slow links (free with wait):")
                for i, url in enumerate(slow_links, 1):
                    links_info.append(f"  {i}. {url.url}")
            
            # Other links
            other_links = [url for url in urls if 
                          "Fast Partner Server" not in url.title and 
                          "Slow Partner Server" not in url.title]
            if other_links:
                links_info.append("Other links:")
                for i, url in enumerate(other_links, 1):
                    links_info.append(f"  {i}. {url.url}")
            
            links_text = "\n".join(links_info)
            
            # Anna's Archive requires manual download
            return DownloadResult(
                success=False,
                error_message=f"Anna's Archive requires manual download. Available links:\n{links_text}"
            )
            
        except Exception as e:
            logger.error(f"Anna's Archive download info failed: {e}")
            raise DownloadError(f"Anna's Archive download info failed: {str(e)}", "annas_archive")
    
    async def get_book_info(self, download_info: DownloadInfo) -> Optional[BookInfo]:
        """Get detailed book information from Anna's Archive"""
        try:
            if not download_info.book_id:
                return None
            
            book_info = get_annas_information(download_info.book_id)
            
            return BookInfo(
                title=book_info.title,
                authors=book_info.authors,
                publisher=book_info.publisher,
                year=book_info.publish_date,
                description=book_info.description,
                language=book_info.file_info.language if book_info.file_info else "Unknown",
                file_type=book_info.file_info.extension if book_info.file_info else "Unknown",
                file_size=book_info.file_info.size if book_info.file_info else "Unknown",
                cover_url=book_info.thumbnail
            )
            
        except Exception as e:
            logger.error(f"Failed to get Anna's Archive book info: {e}")
            return None
    
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        return "https://annas-archive.org"
    
    def _is_valid_book_id(self, book_id: str) -> bool:
        """Check if book ID is valid (32-character hex string)"""
        if not book_id or len(book_id) != 32:
            return False
        try:
            int(book_id, 16)
            return True
        except ValueError:
            return False
