"""
Basic usage examples for ebooks-library
"""

import asyncio
from pathlib import Path
from ebooks_library import EbooksLibrary, LibraryConfig, Platform


async def basic_search_example():
    """Basic search example"""
    print("=== Basic Search Example ===")
    
    # Create library with default config
    library = EbooksLibrary()
    
    try:
        # Search for books
        results = await library.search("Python programming", limit=5)
        
        print(f"Found {len(results)} books:")
        for i, result in enumerate(results, 1):
            book = result.book_info
            print(f"{i}. {book.title}")
            print(f"   Authors: {book.authors}")
            print(f"   Platform: {result.platform.value}")
            print()
            
    finally:
        await library.close()


async def configured_search_example():
    """Search with custom configuration"""
    print("=== Configured Search Example ===")
    
    # Create custom configuration
    config = LibraryConfig(
        enable_archive=True,
        enable_liber3=True,
        max_results=10,
        timeout=30
    )
    
    async with EbooksLibrary(config) as library:
        # Search specific platforms
        results = await library.search(
            "machine learning",
            platforms=[Platform.ARCHIVE_ORG, Platform.LIBER3],
            limit=3
        )
        
        print(f"Found {len(results)} books from specific platforms:")
        for result in results:
            print(f"- {result.book_info.title} ({result.platform.value})")


async def download_example():
    """Download example"""
    print("=== Download Example ===")
    
    config = LibraryConfig(enable_archive=True)
    
    async with EbooksLibrary(config) as library:
        # Search for a book
        results = await library.search("Python", limit=1)
        
        if results:
            result = results[0]
            print(f"Downloading: {result.book_info.title}")
            
            # Create downloads directory
            download_dir = Path("./downloads")
            download_dir.mkdir(exist_ok=True)
            
            try:
                # Download the book
                download_result = await library.download(
                    result.download_info,
                    save_path=download_dir
                )
                
                if download_result.success:
                    print(f"Successfully downloaded: {download_result.file_name}")
                    print(f"File size: {download_result.file_size} bytes")
                else:
                    print(f"Download failed: {download_result.error_message}")
                    
            except Exception as e:
                print(f"Download error: {e}")
        else:
            print("No books found to download")


async def in_memory_download_example():
    """Download to memory example"""
    print("=== In-Memory Download Example ===")
    
    config = LibraryConfig(enable_archive=True)
    
    async with EbooksLibrary(config) as library:
        results = await library.search("programming", limit=1)
        
        if results:
            result = results[0]
            print(f"Downloading to memory: {result.book_info.title}")
            
            try:
                download_result = await library.download(
                    result.download_info,
                    return_content=True
                )
                
                if download_result.success:
                    print(f"Downloaded {len(download_result.content)} bytes to memory")
                    
                    # You can now process the content
                    # For example, save it with a custom name
                    with open(f"custom_name.{result.book_info.file_type}", "wb") as f:
                        f.write(download_result.content)
                    print("Saved with custom name")
                    
            except Exception as e:
                print(f"Download error: {e}")


async def platform_testing_example():
    """Test platform connections"""
    print("=== Platform Testing Example ===")
    
    library = EbooksLibrary()
    
    try:
        enabled_platforms = library.get_enabled_platforms()
        print(f"Enabled platforms: {[p.value for p in enabled_platforms]}")
        
        for platform in enabled_platforms:
            is_connected = await library.test_platform_connection(platform)
            status = "✓ Connected" if is_connected else "✗ Failed"
            print(f"{platform.value}: {status}")
            
    finally:
        await library.close()


async def main():
    """Run all examples"""
    examples = [
        basic_search_example,
        configured_search_example,
        download_example,
        in_memory_download_example,
        platform_testing_example,
    ]
    
    for example in examples:
        try:
            await example()
            print("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"Example failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
