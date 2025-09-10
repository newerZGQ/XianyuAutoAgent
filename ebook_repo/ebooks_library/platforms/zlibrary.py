"""
Z-Library platform implementation
"""

import os
import logging
from typing import List, Optional, Union
from pathlib import Path

from .base import BasePlatform
from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo, Platform
from ..exceptions import SearchError, DownloadError, AuthenticationError
from ..adapters.Zlibrary import Zlibrary


logger = logging.getLogger(__name__)


class ZLibraryPlatform(BasePlatform):
    """Z-Library platform implementation"""
    
    def __init__(self, email: str, password: str, **kwargs):
        """
        Initialize Z-Library platform.
        
        Args:
            email: Z-Library account email
            password: Z-Library account password
        """
        super().__init__(**kwargs)
        self.email = email
        self.password = password
        self.zlibrary = None
        self._max_retries = 3
        
    async def _ensure_logged_in(self):
        """Ensure Z-Library session is logged in"""
        if self.zlibrary is None:
            self.zlibrary = Zlibrary()
            
        if not self.zlibrary.isLoggedIn():
            retry_count = 0
            while retry_count < self._max_retries:
                try:
                    result = self.zlibrary.login(self.email, self.password)
                    if self.zlibrary.isLoggedIn():
                        logger.info("Successfully logged into Z-Library")
                        return
                    else:
                        logger.warning(f"Z-Library login failed: {result}")
                except Exception as e:
                    logger.error(f"Z-Library login attempt {retry_count + 1} failed: {e}")
                    
                retry_count += 1
                
            raise AuthenticationError("Failed to login to Z-Library after multiple attempts", "zlibrary")
    
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search Z-Library for ebooks"""
        try:
            await self._ensure_logged_in()
            
            # Use the existing Zlibrary search method
            results = self.zlibrary.search(message=query, limit=limit)
            
            if not results or not results.get("books"):
                return []
                
            search_results = []
            books = results.get("books", [])
            
            for book in books:
                book_info = BookInfo(
                    title=book.get('title', 'Unknown'),
                    authors=book.get('author', 'Unknown'),
                    year=str(book.get('year', 'Unknown')),
                    publisher=book.get('publisher') if book.get('publisher') != 'None' else 'Unknown',
                    language=book.get('language', 'Unknown'),
                    description=self._clean_description(book.get('description')),
                    cover_url=book.get('cover'),
                    file_size=book.get('filesize'),
                    file_type=book.get('extension')
                )
                
                download_info = DownloadInfo(
                    platform=Platform.ZLIBRARY,
                    book_id=str(book.get('id')),
                    hash_id=book.get('hash'),
                    requires_auth=True
                )
                
                search_result = SearchResult(
                    book_info=book_info,
                    download_info=download_info,
                    platform=Platform.ZLIBRARY
                )
                
                search_results.append(search_result)
                
            logger.info(f"Found {len(search_results)} results from Z-Library")
            return search_results
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Z-Library search failed: {e}")
            raise SearchError(f"Z-Library search failed: {str(e)}", "zlibrary")
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """Download ebook from Z-Library"""
        try:
            await self._ensure_logged_in()
            
            if not download_info.book_id or not download_info.hash_id:
                raise DownloadError("Z-Library download requires both book_id and hash_id", "zlibrary")
            
            # Get book details first
            book_details = self.zlibrary.getBookInfo(download_info.book_id, hashid=download_info.hash_id)
            if not book_details:
                raise DownloadError("Could not get book details from Z-Library", "zlibrary")
            
            # Download the book
            download_result = self.zlibrary.downloadBook({
                "id": download_info.book_id,
                "hash": download_info.hash_id
            })
            
            if not download_result:
                raise DownloadError("Failed to download book from Z-Library", "zlibrary")
                
            book_name, book_content = download_result
            book_name = self._truncate_filename(book_name)
            
            if return_content:
                return DownloadResult(
                    success=True,
                    file_name=book_name,
                    file_size=len(book_content),
                    content=book_content
                )
            
            # Save to file
            if save_path is None:
                save_path = Path.cwd()
            else:
                save_path = Path(save_path)
                
            save_path.mkdir(parents=True, exist_ok=True)
            file_path = save_path / book_name
            
            with open(file_path, "wb") as f:
                f.write(book_content)
                
            logger.info(f"Successfully downloaded Z-Library book: {book_name}")
            
            return DownloadResult(
                success=True,
                file_path=str(file_path),
                file_name=book_name,
                file_size=len(book_content)
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Z-Library download failed: {e}")
            raise DownloadError(f"Z-Library download failed: {str(e)}", "zlibrary")
    
    async def get_book_info(self, download_info: DownloadInfo) -> Optional[BookInfo]:
        """Get detailed book information from Z-Library"""
        try:
            await self._ensure_logged_in()
            
            if not download_info.book_id or not download_info.hash_id:
                return None
                
            book_details = self.zlibrary.getBookInfo(download_info.book_id, hashid=download_info.hash_id)
            if not book_details or not book_details.get('success'):
                return None
                
            book = book_details.get('book', {})
            
            return BookInfo(
                title=book.get('title', 'Unknown'),
                authors=book.get('author', 'Unknown'),
                year=str(book.get('year', 'Unknown')),
                publisher=book.get('publisher') if book.get('publisher') != 'None' else 'Unknown',
                language=book.get('language', 'Unknown'),
                description=self._clean_description(book.get('description')),
                cover_url=book.get('cover'),
                file_size=book.get('filesize'),
                file_type=book.get('extension'),
                isbn=book.get('isbn')
            )
            
        except Exception as e:
            logger.error(f"Failed to get Z-Library book info: {e}")
            return None
    
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        return "https://z-library.sk"
    
    def _clean_description(self, description) -> Optional[str]:
        """Clean and truncate book description"""
        if not description or description == "None":
            return None
            
        if isinstance(description, str):
            description = description.strip()
            if len(description) > 300:
                description = description[:300] + "..."
            return description
            
        return None
    
    def _is_valid_book_id(self, book_id: str) -> bool:
        """Check if book ID is valid (numeric)"""
        return book_id and str(book_id).isdigit()
    
    def _is_valid_hash(self, hash_id: str) -> bool:
        """Check if hash is valid (6-character hex)"""
        if not hash_id or len(hash_id) != 6:
            return False
        try:
            int(hash_id, 16)
            return True
        except ValueError:
            return False
    
    async def close(self):
        """Close Z-Library session"""
        if self.zlibrary and self.zlibrary.isLoggedIn():
            self.zlibrary = None
        await super().close()
