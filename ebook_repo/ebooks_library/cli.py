"""
Command line interface for ebooks library
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .core import EbooksLibrary
from .models import LibraryConfig, Platform
from .exceptions import EbooksLibraryError


async def search_books(
    query: str,
    platforms: Optional[list] = None,
    limit: int = 20,
    config_file: Optional[str] = None
):
    """Search for books"""
    config = load_config(config_file)
    
    async with EbooksLibrary(config) as library:
        try:
            platform_list = None
            if platforms:
                platform_list = [Platform(p) for p in platforms]
                
            results = await library.search(query, platform_list, limit)
            
            if not results:
                print("No books found.")
                return
                
            print(f"Found {len(results)} books:")
            print("-" * 80)
            
            for i, result in enumerate(results, 1):
                book = result.book_info
                download = result.download_info
                
                print(f"{i}. {book.title}")
                if book.authors:
                    print(f"   Authors: {book.authors}")
                if book.year:
                    print(f"   Year: {book.year}")
                if book.publisher:
                    print(f"   Publisher: {book.publisher}")
                if book.description:
                    desc = book.description[:100] + "..." if len(book.description) > 100 else book.description
                    print(f"   Description: {desc}")
                    
                print(f"   Platform: {result.platform.value}")
                if download.download_url:
                    print(f"   Download URL: {download.download_url}")
                elif download.book_id:
                    print(f"   Book ID: {download.book_id}")
                    if download.hash_id:
                        print(f"   Hash: {download.hash_id}")
                        
                print("-" * 80)
                
        except EbooksLibraryError as e:
            print(f"Search failed: {e}")
            sys.exit(1)


async def download_book(
    identifier: str,
    save_path: str = "./downloads",
    platform: Optional[str] = None,
    hash_id: Optional[str] = None,
    config_file: Optional[str] = None
):
    """Download a book"""
    config = load_config(config_file)
    
    async with EbooksLibrary(config) as library:
        try:
            # Determine platform and create download info
            if platform:
                platform_enum = Platform(platform)
            else:
                # Try to auto-detect platform from identifier
                platform_enum = detect_platform(identifier)
                
            from .models import DownloadInfo
            
            if identifier.startswith('http'):
                download_info = DownloadInfo(
                    platform=platform_enum,
                    download_url=identifier
                )
            else:
                download_info = DownloadInfo(
                    platform=platform_enum,
                    book_id=identifier,
                    hash_id=hash_id
                )
                
            result = await library.download(download_info, save_path)
            
            if result.success:
                print(f"Successfully downloaded: {result.file_name}")
                print(f"Saved to: {result.file_path}")
                print(f"File size: {result.file_size} bytes")
            else:
                print(f"Download failed: {result.error_message}")
                sys.exit(1)
                
        except EbooksLibraryError as e:
            print(f"Download failed: {e}")
            sys.exit(1)


def detect_platform(identifier: str) -> Platform:
    """Auto-detect platform from identifier"""
    if identifier.startswith('http'):
        if 'archive.org' in identifier:
            return Platform.ARCHIVE_ORG
        elif 'opds/download' in identifier:
            return Platform.CALIBRE_WEB
        else:
            raise ValueError("Cannot detect platform from URL")
    elif len(identifier) == 32 and identifier.startswith('L'):
        return Platform.LIBER3
    elif len(identifier) == 32 and identifier.startswith('A'):
        return Platform.ANNAS_ARCHIVE
    elif identifier.isdigit():
        return Platform.ZLIBRARY
    else:
        raise ValueError("Cannot detect platform from identifier")


def load_config(config_file: Optional[str] = None) -> LibraryConfig:
    """Load configuration from file or environment"""
    config = LibraryConfig()
    
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            
        # Update config with file data
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return config


def search_command():
    """CLI command for searching books"""
    parser = argparse.ArgumentParser(description="Search for ebooks")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-p", "--platforms", nargs="+", 
                       choices=[p.value for p in Platform],
                       help="Platforms to search")
    parser.add_argument("-l", "--limit", type=int, default=20,
                       help="Maximum number of results")
    parser.add_argument("-c", "--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    asyncio.run(search_books(
        args.query,
        args.platforms,
        args.limit,
        args.config
    ))


def download_command():
    """CLI command for downloading books"""
    parser = argparse.ArgumentParser(description="Download an ebook")
    parser.add_argument("identifier", help="Book identifier (URL, ID, etc.)")
    parser.add_argument("-s", "--save-path", default="./downloads",
                       help="Directory to save the file")
    parser.add_argument("-p", "--platform", choices=[p.value for p in Platform],
                       help="Platform (auto-detected if not specified)")
    parser.add_argument("--hash", help="Hash ID (for Z-Library)")
    parser.add_argument("-c", "--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    asyncio.run(download_book(
        args.identifier,
        args.save_path,
        args.platform,
        args.hash,
        args.config
    ))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        sys.argv.pop(1)
        search_command()
    elif len(sys.argv) > 1 and sys.argv[1] == "download":
        sys.argv.pop(1)
        download_command()
    else:
        print("Usage: python -m ebooks_library.cli [search|download] ...")
        sys.exit(1)
