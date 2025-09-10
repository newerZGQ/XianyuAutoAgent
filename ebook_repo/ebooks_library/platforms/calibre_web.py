"""
Calibre-Web platform implementation
"""

import re
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional, Union
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus, urljoin, unquote

from .base import BasePlatform
from ..models import SearchResult, DownloadResult, BookInfo, DownloadInfo, Platform
from ..exceptions import SearchError, DownloadError


logger = logging.getLogger(__name__)


class CalibreWebPlatform(BasePlatform):
    """Calibre-Web platform implementation"""
    
    def __init__(self, base_url: str, **kwargs):
        """
        Initialize Calibre-Web platform.
        
        Args:
            base_url: Base URL of the Calibre-Web server
        """
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip('/')
        
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search Calibre-Web for ebooks"""
        try:
            search_url = f"{self.base_url}/opds/search/{quote_plus(query)}"
            
            session = await self._get_session()
            async with session.get(search_url, proxy=self.proxy) as response:
                if response.status != 200:
                    raise SearchError(f"Calibre-Web search returned status {response.status}")
                
                content_type = response.headers.get("Content-Type", "")
                if "application/atom+xml" not in content_type:
                    raise SearchError(f"Unexpected content type from Calibre-Web: {content_type}")
                
                xml_data = await response.text()
                results = self._parse_opds_response(xml_data, limit)
                
                if not results:
                    return []
                
                search_results = []
                for result in results:
                    book_info = BookInfo(
                        title=result.get("title", "Unknown"),
                        authors=result.get("authors", "Unknown"),
                        year=str(result.get("year", "Unknown")),
                        publisher=result.get("publisher", "Unknown"),
                        language=result.get("language", "Unknown"),
                        description=result.get("summary"),
                        cover_url=result.get("cover_link"),
                        file_type=result.get("file_type"),
                        file_size=result.get("file_size")
                    )
                    
                    download_info = DownloadInfo(
                        platform=Platform.CALIBRE_WEB,
                        download_url=result.get("download_link"),
                        file_name=self._extract_filename_from_url(result.get("download_link"))
                    )
                    
                    search_result = SearchResult(
                        book_info=book_info,
                        download_info=download_info,
                        platform=Platform.CALIBRE_WEB
                    )
                    
                    search_results.append(search_result)
                
                logger.info(f"Found {len(search_results)} results from Calibre-Web")
                return search_results
                
        except Exception as e:
            logger.error(f"Calibre-Web search failed: {e}")
            raise SearchError(f"Calibre-Web search failed: {str(e)}", "calibre_web")
    
    def _parse_opds_response(self, xml_data: str, limit: Optional[int] = None) -> List[dict]:
        """Parse OPDS XML response"""
        try:
            # Clean XML data
            xml_data = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', '', xml_data)
            xml_data = re.sub(r'\s+', ' ', xml_data)
            
            root = ET.fromstring(xml_data)
            namespace = {"default": "http://www.w3.org/2005/Atom"}
            entries = root.findall("default:entry", namespace)
            
            results = []
            for entry in entries:
                # Extract title
                title_element = entry.find("default:title", namespace)
                title = title_element.text if title_element is not None else "Unknown"
                
                # Extract authors
                authors = []
                author_elements = entry.findall("default:author/default:name", namespace)
                for author in author_elements:
                    if author.text:
                        authors.append(author.text)
                authors = ", ".join(authors) if authors else "Unknown"
                
                # Extract summary
                summary_element = entry.find("default:summary", namespace)
                summary = summary_element.text if summary_element is not None else "No description"
                
                # Extract publication year
                published_element = entry.find("default:published", namespace)
                year = "Unknown"
                if published_element is not None and published_element.text:
                    try:
                        year = datetime.fromisoformat(published_element.text).year
                    except ValueError:
                        year = "Unknown"
                
                # Extract language
                lang_element = entry.find("default:dcterms:language", namespace)
                language = lang_element.text if lang_element is not None else "Unknown"
                
                # Extract publisher
                publisher_element = entry.find("default:publisher/default:name", namespace)
                publisher = publisher_element.text if publisher_element is not None else "Unknown"
                
                # Extract cover link
                cover_element = entry.find("default:link[@rel='http://opds-spec.org/image']", namespace)
                cover_suffix = cover_element.attrib.get("href", "") if cover_element is not None else ""
                cover_link = ""
                if cover_suffix and re.match(r"^/opds/cover/\d+$", cover_suffix):
                    cover_link = urljoin(self.base_url, cover_suffix)
                
                # Extract download link and file info
                acquisition_element = entry.find("default:link[@rel='http://opds-spec.org/acquisition']", namespace)
                download_link = ""
                file_type = "Unknown"
                file_size = "Unknown"
                
                if acquisition_element is not None:
                    download_suffix = acquisition_element.attrib.get("href", "")
                    if download_suffix and re.match(r"^/opds/download/\d+/[\w]+/$", download_suffix):
                        download_link = urljoin(self.base_url, download_suffix)
                    file_type = acquisition_element.attrib.get("type", "Unknown")
                    file_size = acquisition_element.attrib.get("length", "Unknown")
                
                results.append({
                    "title": title,
                    "authors": authors,
                    "summary": summary,
                    "year": year,
                    "publisher": publisher,
                    "language": language,
                    "cover_link": cover_link,
                    "download_link": download_link,
                    "file_type": file_type,
                    "file_size": file_size
                })
            
            return results[:limit] if limit else results
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse OPDS response: {e}")
            raise SearchError(f"Failed to parse Calibre-Web response: {str(e)}", "calibre_web")
    
    async def download(
        self, 
        download_info: DownloadInfo, 
        save_path: Optional[Union[str, Path]] = None,
        return_content: bool = False
    ) -> DownloadResult:
        """Download ebook from Calibre-Web"""
        try:
            if not download_info.download_url:
                raise DownloadError("Calibre-Web download requires download_url", "calibre_web")
            
            if not self._is_valid_calibre_url(download_info.download_url):
                raise DownloadError("Invalid Calibre-Web download URL", "calibre_web")
            
            session = await self._get_session()
            async with session.get(download_info.download_url, proxy=self.proxy) as response:
                if response.status != 200:
                    raise DownloadError(f"Download failed with status {response.status}", "calibre_web")
                
                # Extract filename from Content-Disposition header
                file_name = self._extract_filename_from_response(response)
                if not file_name:
                    file_name = download_info.file_name or "unknown_book"
                
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
                
                logger.info(f"Successfully downloaded Calibre-Web book: {file_name}")
                
                return DownloadResult(
                    success=True,
                    file_path=str(file_path),
                    file_name=file_name,
                    file_size=len(content)
                )
                
        except Exception as e:
            logger.error(f"Calibre-Web download failed: {e}")
            raise DownloadError(f"Calibre-Web download failed: {str(e)}", "calibre_web")
    
    def _get_test_url(self) -> str:
        """Get URL for connection testing"""
        return self.base_url
    
    def _is_valid_calibre_url(self, url: str) -> bool:
        """Check if URL is a valid Calibre-Web download URL"""
        if not self._is_valid_url(url):
            return False
        return "/opds/download/" in url
    
    def _extract_filename_from_response(self, response) -> Optional[str]:
        """Extract filename from HTTP response headers"""
        content_disposition = response.headers.get("Content-Disposition", "")
        if not content_disposition:
            return None
        
        # Try filename*= first (RFC 6266)
        match = re.search(r'filename\*=(?:UTF-8\'\')?([^;]+)', content_disposition)
        if match:
            return unquote(match.group(1))
        
        # Try regular filename=
        match = re.search(r'filename=["\']?([^;\']+)["\']?', content_disposition)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_filename_from_url(self, url: Optional[str]) -> Optional[str]:
        """Extract potential filename from download URL"""
        if not url:
            return None
        
        # Extract book ID from URL pattern like /opds/download/123/format/
        match = re.search(r'/opds/download/(\d+)/([^/]+)/?$', url)
        if match:
            book_id, format_name = match.groups()
            return f"book_{book_id}.{format_name.lower()}"
        
        return None
