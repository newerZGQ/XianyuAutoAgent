"""
Core EbooksLibrary class
"""

import asyncio
import os
import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .models import (
    LibraryConfig, SearchResult, DownloadResult, BookInfo, 
    DownloadInfo, Platform
)
from .exceptions import (
    EbooksLibraryError, SearchError, DownloadError, 
    ConfigurationError, NetworkError
)
from .platforms import (
    CalibreWebPlatform, ZLibraryPlatform, ArchiveOrgPlatform,
    Liber3Platform, AnnasArchivePlatform
)


logger = logging.getLogger(__name__)


class EbooksLibrary:
    """
    Main class for ebook search and download operations across multiple platforms.
    
    This class provides a unified interface to search and download ebooks from
    various platforms including Calibre-Web, Z-Library, Archive.org, Liber3,
    and Anna's Archive.
    
    Example:
        >>> config = LibraryConfig(enable_calibre=True, calibre_web_url="http://localhost:8083")
        >>> library = EbooksLibrary(config)
        >>> results = await library.search("Python programming", limit=10)
        >>> if results:
        >>>     download_result = await library.download(results[0].download_info, "./downloads/")
        >>>     print(f"Downloaded: {download_result.file_name}")
    """
    
    def __init__(self, config: Optional[LibraryConfig] = None):
        """
        Initialize the EbooksLibrary with configuration.
        
        Args:
            config: LibraryConfig object with platform settings
        """
        self.config = config or LibraryConfig()
        self.platforms = {}
        self._setup_platforms()
        
    def _setup_platforms(self):
        """Initialize enabled platforms based on configuration"""
        if self.config.enable_calibre and self.config.calibre_web_url:
            self.platforms[Platform.CALIBRE_WEB] = CalibreWebPlatform(
                base_url=self.config.calibre_web_url,
                proxy=self.config.proxy,
                timeout=self.config.timeout
            )
            
        if self.config.enable_zlib and self.config.zlib_email and self.config.zlib_password:
            self.platforms[Platform.ZLIBRARY] = ZLibraryPlatform(
                email=self.config.zlib_email,
                password=self.config.zlib_password,
                proxy=self.config.proxy,
                timeout=self.config.timeout
            )
            
        if self.config.enable_archive:
            self.platforms[Platform.ARCHIVE_ORG] = ArchiveOrgPlatform(
                proxy=self.config.proxy,
                timeout=self.config.timeout
            )
            
        if self.config.enable_liber3:
            self.platforms[Platform.LIBER3] = Liber3Platform(
                proxy=self.config.proxy,
                timeout=self.config.timeout
            )
            
        if self.config.enable_annas:
            self.platforms[Platform.ANNAS_ARCHIVE] = AnnasArchivePlatform(
                proxy=self.config.proxy,
                timeout=self.config.timeout
            )
            
        logger.info(f"Initialized {len(self.platforms)} platforms: {list(self.platforms.keys())}")
    
    async def search(
        self, 
        query: str, 
        platforms: Optional[List[Platform]] = None,
        limit: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search for ebooks across enabled platforms.
        
        Args:
            query: Search query string
            platforms: List of specific platforms to search (if None, searches all enabled)
            limit: Maximum number of results per platform
            
        Returns:
            List of SearchResult objects
            
        Raises:
            SearchError: If search fails
        """
        if not query or not query.strip():
            raise SearchError("Search query cannot be empty")
            
        search_limit = limit or self.config.max_results
        target_platforms = platforms or list(self.platforms.keys())
        
        # Filter to only enabled platforms
        target_platforms = [p for p in target_platforms if p in self.platforms]
        
        if not target_platforms:
            raise SearchError("No platforms available for search")
            
        logger.info(f"Searching for '{query}' across {len(target_platforms)} platforms")
        
        # Create search tasks for each platform
        tasks = []
        for platform in target_platforms:
            platform_obj = self.platforms[platform]
            task = asyncio.create_task(
                self._search_platform(platform_obj, platform, query, search_limit)
            )
            tasks.append(task)
            
        # Execute searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results from all platforms
        all_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for platform {target_platforms[i]}: {result}")
                continue
            if result:
                all_results.extend(result)
                
        logger.info(f"Found {len(all_results)} total results")
        return all_results
    
    async def _search_platform(
        self, 
        platform_obj, 
        platform: Platform, 
        query: str, 
        limit: int
    ) -> List[SearchResult]:
        """Search a specific platform"""
        try:
            return await platform_obj.search(query, limit)
        except Exception as e:
            logger.error(f"Search failed for {platform}: {e}")
            return []
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """
        Download an ebook using the provided download information.
        
        Args:
            download_info: DownloadInfo object with platform-specific details
            save_path: Directory to save the file (if None, uses current directory)
            return_content: If True, returns file content in memory instead of saving
            
        Returns:
            DownloadResult object
            
        Raises:
            DownloadError: If download fails
        """
        platform = download_info.platform
        
        if platform not in self.platforms:
            raise DownloadError(f"Platform {platform} is not enabled", platform.value)
            
        platform_obj = self.platforms[platform]
        
        try:
            result = await platform_obj.download(download_info, save_path, return_content)
            logger.info(f"Successfully downloaded from {platform}: {result.file_name}")
            return result
        except Exception as e:
            logger.error(f"Download failed for {platform}: {e}")
            raise DownloadError(f"Download failed: {str(e)}", platform.value)
    
    async def get_book_info(self, download_info: DownloadInfo) -> Optional[BookInfo]:
        """
        Get detailed information about a book.
        
        Args:
            download_info: DownloadInfo object
            
        Returns:
            BookInfo object or None if not found
        """
        platform = download_info.platform
        
        if platform not in self.platforms:
            return None
            
        platform_obj = self.platforms[platform]
        
        try:
            return await platform_obj.get_book_info(download_info)
        except Exception as e:
            logger.error(f"Failed to get book info from {platform}: {e}")
            return None
    
    def get_enabled_platforms(self) -> List[Platform]:
        """Get list of currently enabled platforms"""
        return list(self.platforms.keys())
    
    def is_platform_enabled(self, platform: Platform) -> bool:
        """Check if a specific platform is enabled"""
        return platform in self.platforms
    
    async def test_platform_connection(self, platform: Platform) -> bool:
        """
        Test connection to a specific platform.
        
        Args:
            platform: Platform to test
            
        Returns:
            True if connection successful, False otherwise
        """
        if platform not in self.platforms:
            return False
            
        platform_obj = self.platforms[platform]
        
        try:
            return await platform_obj.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for {platform}: {e}")
            return False
    
    async def close(self):
        """Close all platform connections and cleanup resources"""
        for platform_obj in self.platforms.values():
            try:
                await platform_obj.close()
            except Exception as e:
                logger.error(f"Error closing platform: {e}")
        
        logger.info("EbooksLibrary closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
