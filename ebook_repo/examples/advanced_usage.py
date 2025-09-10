"""
Advanced usage examples for ebooks-library
"""

import asyncio
import json
from pathlib import Path
from ebooks_library import EbooksLibrary, LibraryConfig, Platform


async def calibre_web_example():
    """Example with Calibre-Web configuration"""
    print("=== Calibre-Web Example ===")
    
    config = LibraryConfig(
        enable_calibre=True,
        calibre_web_url="http://localhost:8083",  # Adjust to your server
        max_results=5
    )
    
    async with EbooksLibrary(config) as library:
        if library.is_platform_enabled(Platform.CALIBRE_WEB):
            results = await library.search("science fiction", limit=3)
            
            for result in results:
                if result.platform == Platform.CALIBRE_WEB:
                    book = result.book_info
                    print(f"Title: {book.title}")
                    print(f"Authors: {book.authors}")
                    print(f"Download URL: {result.download_info.download_url}")
                    print()
        else:
            print("Calibre-Web not configured or not accessible")


async def zlibrary_example():
    """Example with Z-Library configuration"""
    print("=== Z-Library Example ===")
    
    # Note: You need valid Z-Library credentials
    config = LibraryConfig(
        enable_zlib=True,
        zlib_email="your_email@example.com",  # Replace with actual credentials
        zlib_password="your_password",         # Replace with actual credentials
        max_results=3
    )
    
    async with EbooksLibrary(config) as library:
        if library.is_platform_enabled(Platform.ZLIBRARY):
            print("Z-Library is enabled (credentials provided)")
            
            # Search example
            results = await library.search("data science", limit=2)
            
            for result in results:
                if result.platform == Platform.ZLIBRARY:
                    book = result.book_info
                    download = result.download_info
                    print(f"Title: {book.title}")
                    print(f"ID: {download.book_id}, Hash: {download.hash_id}")
                    print()
        else:
            print("Z-Library not configured (credentials needed)")


async def batch_download_example():
    """Download multiple books"""
    print("=== Batch Download Example ===")
    
    config = LibraryConfig(
        enable_archive=True,
        enable_liber3=True
    )
    
    async with EbooksLibrary(config) as library:
        # Search for multiple books
        queries = ["Python", "JavaScript", "machine learning"]
        download_dir = Path("./batch_downloads")
        download_dir.mkdir(exist_ok=True)
        
        for query in queries:
            print(f"Searching for: {query}")
            results = await library.search(query, limit=1)
            
            if results:
                result = results[0]
                print(f"Found: {result.book_info.title}")
                
                try:
                    download_result = await library.download(
                        result.download_info,
                        save_path=download_dir
                    )
                    
                    if download_result.success:
                        print(f"Downloaded: {download_result.file_name}")
                    else:
                        print(f"Failed: {download_result.error_message}")
                        
                except Exception as e:
                    print(f"Error downloading {result.book_info.title}: {e}")
            else:
                print(f"No results for: {query}")
            
            print()


async def search_with_filters_example():
    """Search with platform-specific filtering"""
    print("=== Search with Filters Example ===")
    
    library = EbooksLibrary()
    
    try:
        # Search all platforms
        all_results = await library.search("programming", limit=10)
        
        # Group results by platform
        by_platform = {}
        for result in all_results:
            platform = result.platform.value
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(result)
        
        print("Results by platform:")
        for platform, results in by_platform.items():
            print(f"\n{platform}: {len(results)} books")
            for result in results[:2]:  # Show first 2
                print(f"  - {result.book_info.title}")
                
        # Search specific platforms only
        print("\nSearching only Archive.org and Liber3:")
        filtered_results = await library.search(
            "programming",
            platforms=[Platform.ARCHIVE_ORG, Platform.LIBER3],
            limit=5
        )
        
        for result in filtered_results:
            print(f"- {result.book_info.title} ({result.platform.value})")
            
    finally:
        await library.close()


async def error_handling_example():
    """Demonstrate error handling"""
    print("=== Error Handling Example ===")
    
    library = EbooksLibrary()
    
    try:
        # Test with empty query
        try:
            await library.search("")
        except Exception as e:
            print(f"Empty query error: {e}")
        
        # Test with invalid download info
        from ebooks_library.models import DownloadInfo
        
        invalid_download = DownloadInfo(
            platform=Platform.ZLIBRARY,
            book_id="invalid_id"
        )
        
        try:
            await library.download(invalid_download)
        except Exception as e:
            print(f"Invalid download error: {e}")
            
        # Test connection to platforms
        print("\nTesting platform connections:")
        for platform in library.get_enabled_platforms():
            try:
                connected = await library.test_platform_connection(platform)
                print(f"{platform.value}: {'✓' if connected else '✗'}")
            except Exception as e:
                print(f"{platform.value}: Error - {e}")
                
    finally:
        await library.close()


async def configuration_management_example():
    """Configuration management example"""
    print("=== Configuration Management Example ===")
    
    # Create configuration file
    config_data = {
        "enable_archive": True,
        "enable_liber3": True,
        "enable_calibre": False,
        "enable_zlib": False,
        "enable_annas": False,
        "max_results": 15,
        "timeout": 45,
        "proxy": None
    }
    
    config_file = Path("./ebooks_config.json")
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"Created config file: {config_file}")
    
    # Load configuration from file
    with open(config_file, 'r') as f:
        loaded_config = json.load(f)
    
    config = LibraryConfig(**loaded_config)
    
    async with EbooksLibrary(config) as library:
        enabled = library.get_enabled_platforms()
        print(f"Enabled platforms from config: {[p.value for p in enabled]}")
        
        results = await library.search("tutorial", limit=3)
        print(f"Found {len(results)} books with loaded config")
    
    # Clean up
    config_file.unlink()
    print("Cleaned up config file")


async def main():
    """Run all advanced examples"""
    examples = [
        calibre_web_example,
        zlibrary_example,
        batch_download_example,
        search_with_filters_example,
        error_handling_example,
        configuration_management_example,
    ]
    
    for example in examples:
        try:
            await example()
            print("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"Example failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
