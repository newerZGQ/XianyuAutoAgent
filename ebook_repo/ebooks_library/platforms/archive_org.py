"""
Archive.org platform implementation
"""

import asyncio
import logging
import re
from typing import List, Optional, Union
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .base import BasePlatform
from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo, Platform
from ..exceptions import SearchError, DownloadError


logger = logging.getLogger(__name__)


class ArchiveOrgPlatform(BasePlatform):
    """Archive.org platform implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_search_url = "https://archive.org/advancedsearch.php"
        self.base_metadata_url = "https://archive.org/metadata/"
        self.supported_formats = ("pdf", "epub")
        
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search Archive.org for ebooks"""
        try:
            params = {
                "q": f'title:"{query}" mediatype:texts',
                "fl[]": "identifier,title",
                "sort[]": "downloads desc",
                "rows": limit + 10,  # Get extra to account for filtering
                "page": 1,
                "output": "json"
            }
            
            session = await self._get_session()
            async with session.get(
                self.base_search_url, 
                params=params, 
                proxy=self.proxy
            ) as response:
                if response.status != 200:
                    raise SearchError(f"Archive.org search returned status {response.status}")
                    
                result_data = await response.json()
                docs = result_data.get("response", {}).get("docs", [])
                
                if not docs:
                    return []
                
                # Get metadata for each book
                tasks = [
                    self._fetch_metadata(session, self.base_metadata_url + doc["identifier"])
                    for doc in docs
                ]
                
                metadata_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                search_results = []
                for doc, metadata in zip(docs, metadata_results):
                    if isinstance(metadata, Exception):
                        logger.error(f"Failed to get metadata for {doc['identifier']}: {metadata}")
                        continue
                        
                    if not metadata:
                        continue
                        
                    book_info = BookInfo(
                        title=doc.get("title", "Unknown"),
                        authors=metadata.get("authors", "Unknown"),
                        year=metadata.get("year", "Unknown"),
                        publisher=metadata.get("publisher", "Unknown"),
                        language=metadata.get("language", "Unknown"),
                        description=metadata.get("description"),
                        cover_url=metadata.get("cover")
                    )
                    
                    download_info = DownloadInfo(
                        platform=Platform.ARCHIVE_ORG,
                        download_url=metadata.get("download_url"),
                        file_name=metadata.get("file_name")
                    )
                    
                    search_result = SearchResult(
                        book_info=book_info,
                        download_info=download_info,
                        platform=Platform.ARCHIVE_ORG
                    )
                    
                    search_results.append(search_result)
                    
                    if len(search_results) >= limit:
                        break
                
                logger.info(f"Found {len(search_results)} results from Archive.org")
                return search_results
                
        except Exception as e:
            logger.error(f"Archive.org search failed: {e}")
            raise SearchError(f"Archive.org search failed: {str(e)}", "archive_org")
    
    async def _fetch_metadata(self, session, url: str) -> Optional[dict]:
        """Fetch metadata for a specific book"""
        try:
            async with session.get(url, proxy=self.proxy) as response:
                if response.status != 200:
                    return None
                    
                book_detail = await response.json()
                
                identifier = book_detail.get("metadata", {}).get("identifier")
                if not identifier:
                    return None
                    
                metadata = book_detail.get("metadata", {})
                files = book_detail.get("files", [])
                
                # Extract basic info
                description = metadata.get("description", "No description")
                authors = metadata.get("creator", "Unknown")
                language = metadata.get("language", "Unknown")
                publisher = metadata.get("publisher", "Unknown")
                
                # Extract year from publication date
                year = "Unknown"
                pub_date = metadata.get("publicdate")
                if pub_date:
                    year = pub_date[:4] if len(pub_date) >= 4 else "Unknown"
                
                # Clean description if it's HTML
                if isinstance(description, str) and self._is_html(description):
                    description = self._parse_html_to_text(description)
                
                # Truncate description
                if isinstance(description, str) and len(description) > 300:
                    description = description[:300] + "..."
                
                # Find downloadable file
                download_url = None
                file_name = None
                
                for file in files:
                    file_name_candidate = file.get("name", "")
                    if any(file_name_candidate.lower().endswith(fmt) for fmt in self.supported_formats):
                        download_url = f"https://archive.org/download/{identifier}/{file_name_candidate}"
                        file_name = file_name_candidate
                        break
                
                if not download_url:
                    return None
                
                return {
                    "cover": f"https://archive.org/services/img/{identifier}",
                    "authors": authors,
                    "year": year,
                    "publisher": publisher,
                    "language": language,
                    "description": description,
                    "download_url": download_url,
                    "file_name": file_name
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch metadata from {url}: {e}")
            return None
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """Download ebook from Archive.org"""
        try:
            if not download_info.download_url:
                raise DownloadError("Archive.org download requires download_url", "archive_org")
            
            if not self._is_valid_archive_url(download_info.download_url):
                raise DownloadError("Invalid Archive.org download URL", "archive_org")
            
            session = await self._get_session()
            async with session.get(
                download_info.download_url,
                allow_redirects=True,
                proxy=self.proxy
            ) as response:
                if response.status != 200:
                    raise DownloadError(f"Download failed with status {response.status}", "archive_org")
                
                # Get filename from URL or Content-Disposition
                file_name = download_info.file_name
                if not file_name:
                    # Try to extract from URL
                    parsed_url = urlparse(str(response.url))
                    file_name = parsed_url.path.split('/')[-1] or "unknown_book"
                
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
                
                logger.info(f"Successfully downloaded Archive.org book: {file_name}")
                
                return DownloadResult(
                    success=True,
                    file_path=str(file_path),
                    file_name=file_name,
                    file_size=len(content)
                )
                
        except Exception as e:
            logger.error(f"Archive.org download failed: {e}")
            raise DownloadError(f"Archive.org download failed: {str(e)}", "archive_org")
    
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        return "https://archive.org"
    
    def _is_valid_archive_url(self, url: str) -> bool:
        """Check if URL is a valid Archive.org download URL"""
        if not self._is_valid_url(url):
            return False
        return "archive.org/download/" in url
    
    def _is_html(self, content: str) -> bool:
        """Check if content is HTML"""
        return bool(re.search(r'<[^>]+>', content))
    
    def _parse_html_to_text(self, html_content: str) -> str:
        """Parse HTML content to plain text"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text().strip()
        except Exception:
            return html_content
