"""
Base platform interface for ebook sources
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
from pathlib import Path
import aiohttp
import logging

from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo


logger = logging.getLogger(__name__)


class BasePlatform(ABC):
    """
    Abstract base class for ebook platform implementations.
    
    All platform implementations must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, proxy: Optional[str] = None, timeout: int = 30):
        """
        Initialize the platform.
        
        Args:
            proxy: HTTP proxy URL (optional)
            timeout: Request timeout in seconds
        """
        self.proxy = proxy
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
                }
            )
        return self._session
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search for ebooks on this platform.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """
        Download an ebook from this platform.
        
        Args:
            download_info: Platform-specific download information
            save_path: Directory to save the file
            return_content: If True, return content in memory
            
        Returns:
            DownloadResult object
        """
        pass
    
    async def get_book_info(self, download_info: DownloadInfo) -> Optional[BookInfo]:
        """
        Get detailed information about a book.
        
        Args:
            download_info: Platform-specific download information
            
        Returns:
            BookInfo object or None if not available
        """
        # Default implementation returns None
        # Platforms can override this if they support detailed book info
        return None
    
    async def test_connection(self) -> bool:
        """
        Test if the platform is accessible.
        
        Returns:
            True if platform is accessible, False otherwise
        """
        try:
            session = await self._get_session()
            # Each platform should implement specific connection test
            # This is a basic implementation
            async with session.head(
                self._get_test_url(), 
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return response.status < 400
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    @abstractmethod
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        pass
    
    async def close(self):
        """Close HTTP session and cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            
    def _truncate_filename(self, filename: str, max_length: int = 100) -> str:
        """Truncate filename if too long"""
        if len(filename.encode('utf-8')) <= max_length:
            return filename
            
        # Keep file extension
        base, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            ext = '.' + ext
            
        # Calculate available space for base name
        available = max_length - len(ext.encode('utf-8')) - len(" <省略>".encode('utf-8'))
        
        # Truncate base name
        truncated_base = base
        while len(truncated_base.encode('utf-8')) > available and truncated_base:
            truncated_base = truncated_base[:-1]
            
        return f"{truncated_base} <省略>{ext}"
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        return url and (url.startswith('http://') or url.startswith('https://'))
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
