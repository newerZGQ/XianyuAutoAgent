"""
Liber3 platform implementation
"""

import logging
from typing import List, Optional, Union
from pathlib import Path

from .base import BasePlatform
from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo, Platform
from ..exceptions import SearchError, DownloadError


logger = logging.getLogger(__name__)


class Liber3Platform(BasePlatform):
    """Liber3 platform implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_url = "https://lgate.glitternode.ru/v1/searchV2"
        self.detail_url = "https://lgate.glitternode.ru/v1/book"
        
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search Liber3 for ebooks"""
        try:
            # Search for books
            search_payload = {
                "address": "",
                "word": query
            }
            
            session = await self._get_session()
            async with session.post(
                self.search_url,
                json=search_payload,
                headers={"Content-Type": "application/json"},
                proxy=self.proxy
            ) as response:
                if response.status != 200:
                    raise SearchError(f"Liber3 search returned status {response.status}")
                
                data = await response.json()
                book_data = data.get("data", {}).get("book", [])
                
                if not book_data:
                    return []
                
                # Limit results and get book IDs
                book_data = book_data[:limit]
                book_ids = [item.get("id") for item in book_data if item.get("id")]
                
                if not book_ids:
                    return []
                
                # Get detailed information for books
                detailed_books = await self._get_book_details(session, book_ids)
                
                search_results = []
                for book in book_data:
                    book_id = book.get("id")
                    detail = detailed_books.get(book_id, {}).get("book", {}) if detailed_books else {}
                    
                    book_info = BookInfo(
                        title=book.get('title', 'Unknown'),
                        authors=book.get('author', 'Unknown'),
                        year=str(detail.get('year', 'Unknown')),
                        publisher=detail.get('publisher', 'Unknown'),
                        language=detail.get('language', 'Unknown'),
                        file_size=detail.get('filesize', 'Unknown'),
                        file_type=detail.get('extension', 'Unknown')
                    )
                    
                    download_info = DownloadInfo(
                        platform=Platform.LIBER3,
                        book_id=book_id,
                        additional_params={
                            'ipfs_cid': detail.get('ipfs_cid'),
                            'extension': detail.get('extension'),
                            'title': book.get('title', 'unknown_book').replace(" ", "_")
                        }
                    )
                    
                    search_result = SearchResult(
                        book_info=book_info,
                        download_info=download_info,
                        platform=Platform.LIBER3
                    )
                    
                    search_results.append(search_result)
                
                logger.info(f"Found {len(search_results)} results from Liber3")
                return search_results
                
        except Exception as e:
            logger.error(f"Liber3 search failed: {e}")
            raise SearchError(f"Liber3 search failed: {str(e)}", "liber3")
    
    async def _get_book_details(self, session, book_ids: List[str]) -> Optional[dict]:
        """Get detailed information for multiple books"""
        try:
            payload = {"book_ids": book_ids}
            
            async with session.post(
                self.detail_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                proxy=self.proxy
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to get book details: status {response.status}")
                    return None
                
                data = await response.json()
                return data.get("data", {}).get("book", {})
                
        except Exception as e:
            logger.error(f"Failed to get book details: {e}")
            return None
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """Download ebook from Liber3"""
        try:
            if not download_info.book_id:
                raise DownloadError("Liber3 download requires book_id", "liber3")
            
            # Get book details if not already available
            additional_params = download_info.additional_params or {}
            ipfs_cid = additional_params.get('ipfs_cid')
            extension = additional_params.get('extension')
            title = additional_params.get('title', 'unknown_book')
            
            if not ipfs_cid or not extension:
                # Get details from API
                session = await self._get_session()
                book_details = await self._get_book_details(session, [download_info.book_id])
                
                if not book_details or download_info.book_id not in book_details:
                    raise DownloadError("Could not get book details from Liber3", "liber3")
                
                book_info = book_details[download_info.book_id].get("book", {})
                ipfs_cid = book_info.get("ipfs_cid")
                extension = book_info.get("extension")
                title = book_info.get("title", "unknown_book").replace(" ", "_")
            
            if not ipfs_cid or not extension:
                raise DownloadError("Insufficient book information for download", "liber3")
            
            # Construct download URL
            file_name = f"{title}.{extension}"
            download_url = f"https://gateway-ipfs.st/ipfs/{ipfs_cid}?filename={file_name}"
            
            # Download the file
            session = await self._get_session()
            async with session.get(download_url, proxy=self.proxy) as response:
                if response.status != 200:
                    raise DownloadError(f"Download failed with status {response.status}", "liber3")
                
                file_name = self._truncate_filename(file_name)
                content = await response.read()
                
                if return_content:
                    return DownloadResult(
                        success=True,
                        file_name=file_name,
                        file_size=len(content),
                        content=content
                    )
                
                # Save to file
                if save_path is None:
                    save_path = Path.cwd()
                else:
                    save_path = Path(save_path)
                    
                save_path.mkdir(parents=True, exist_ok=True)
                file_path = save_path / file_name
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                logger.info(f"Successfully downloaded Liber3 book: {file_name}")
                
                return DownloadResult(
                    success=True,
                    file_path=str(file_path),
                    file_name=file_name,
                    file_size=len(content)
                )
                
        except Exception as e:
            logger.error(f"Liber3 download failed: {e}")
            raise DownloadError(f"Liber3 download failed: {str(e)}", "liber3")
    
    async def get_book_info(self, download_info: DownloadInfo) -> Optional[BookInfo]:
        """Get detailed book information from Liber3"""
        try:
            if not download_info.book_id:
                return None
            
            session = await self._get_session()
            book_details = await self._get_book_details(session, [download_info.book_id])
            
            if not book_details or download_info.book_id not in book_details:
                return None
            
            book_info = book_details[download_info.book_id].get("book", {})
            
            return BookInfo(
                title=book_info.get('title', 'Unknown'),
                authors=book_info.get('author', 'Unknown'),
                year=str(book_info.get('year', 'Unknown')),
                publisher=book_info.get('publisher', 'Unknown'),
                language=book_info.get('language', 'Unknown'),
                file_size=book_info.get('filesize', 'Unknown'),
                file_type=book_info.get('extension', 'Unknown')
            )
            
        except Exception as e:
            logger.error(f"Failed to get Liber3 book info: {e}")
            return None
    
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        return "https://lgate.glitternode.ru"
    
    def _is_valid_book_id(self, book_id: str) -> bool:
        """Check if book ID is valid (32-character hex string)"""
        if not book_id or len(book_id) != 32:
            return False
        try:
            int(book_id, 16)
            return True
        except ValueError:
            return False
