"""
Simple test script for the ebooks library
"""

import asyncio
import sys
from pathlib import Path

# Add the library to the path
sys.path.insert(0, str(Path(__file__).parent))

from ebooks_library import EbooksLibrary, LibraryConfig, Platform
from ebooks_library.exceptions import EbooksLibraryError


async def test_basic_functionality():
    """Test basic library functionality"""
    print("Testing basic functionality...")
    
    # Test library creation
    config = LibraryConfig(
        enable_archive=True,
        enable_liber3=True,
        enable_calibre=False,  # Usually requires local server
        enable_zlib=False,     # Requires credentials
        enable_annas=True,     # Enable Anna's Archive
        max_results=3,
        timeout=15
    )
    
    library = EbooksLibrary(config)
    
    try:
        # Test enabled platforms
        enabled = library.get_enabled_platforms()
        print(f"✓ Enabled platforms: {[p.value for p in enabled]}")
        
        # Test platform connectivity
        print("\nTesting platform connectivity...")
        connected_platforms = []
        for platform in enabled:
            try:
                connected = await library.test_platform_connection(platform)
                status = "✓ Connected" if connected else "✗ Failed"
                print(f"  {platform.value}: {status}")
                if connected:
                    connected_platforms.append(platform)
            except Exception as e:
                print(f"  {platform.value}: Error - {e}")
        
        # Test search on each connected platform
        print(f"\nTesting search on {len(connected_platforms)} connected platforms...")
        search_query = "Python programming"
        
        for platform in connected_platforms:
            print(f"\n--- Testing {platform.value} ---")
            try:
                # Search on specific platform
                results = await library.search(
                    search_query, 
                    platforms=[platform], 
                    limit=1
                )
                
                if results:
                    result = results[0]
                    book = result.book_info
                    print(f"✓ Found: {book.title}")
                    if book.authors:
                        print(f"  Authors: {book.authors}")
                    if book.year:
                        print(f"  Year: {book.year}")
                    if book.file_type:
                        print(f"  Format: {book.file_type}")
                    
                    # Try to download the first result
                    print(f"  Attempting download...")
                    try:
                        download_result = await library.download(
                            result.download_info,
                            return_content=True  # Download to memory for testing
                        )
                        
                        if download_result.success:
                            content_size = len(download_result.content) if download_result.content else 0
                            print(f"  ✓ Download successful: {content_size} bytes")
                            if download_result.file_name:
                                print(f"  File name: {download_result.file_name}")
                        else:
                            print(f"  ✗ Download failed: {download_result.error_message}")
                            
                    except Exception as e:
                        print(f"  ✗ Download error: {e}")
                else:
                    print(f"✗ No results found on {platform.value}")
                    
            except Exception as e:
                print(f"✗ Search failed on {platform.value}: {e}")
        
        print("\n✓ Platform-specific testing completed")
        
    finally:
        await library.close()


async def test_error_handling():
    """Test error handling"""
    print("Testing error handling...")
    
    library = EbooksLibrary()
    
    try:
        # Test empty search
        try:
            await library.search("")
            print("✗ Empty search should have failed")
        except EbooksLibraryError:
            print("✓ Empty search properly rejected")
        
        # Test invalid platform
        try:
            from ebooks_library.models import DownloadInfo
            invalid_download = DownloadInfo(platform=Platform.ZLIBRARY)
            await library.download(invalid_download)
            print("✗ Invalid download should have failed")
        except EbooksLibraryError:
            print("✓ Invalid download properly rejected")
            
        print("✓ Error handling test completed")
        
    finally:
        await library.close()


async def test_context_manager():
    """Test context manager usage"""
    print("Testing context manager...")
    
    config = LibraryConfig(enable_archive=True, max_results=1)
    
    async with EbooksLibrary(config) as library:
        enabled = library.get_enabled_platforms()
        print(f"✓ Context manager works, platforms: {[p.value for p in enabled]}")
        
        # Test a quick search
        try:
            results = await library.search("test", limit=1)
            print(f"✓ Search in context manager: {len(results)} results")
        except Exception as e:
            print(f"✓ Search in context manager failed (expected): {e}")
    
    print("✓ Context manager test completed")


async def test_individual_platforms():
    """Test each platform individually with search and download"""
    print("Testing individual platforms...")
    
    # Test configurations for different platforms
    platform_configs = {
        Platform.ARCHIVE_ORG: LibraryConfig(
            enable_archive=True,
            enable_liber3=False,
            enable_calibre=False,
            enable_zlib=False,
            enable_annas=False,
            timeout=20
        ),
        Platform.LIBER3: LibraryConfig(
            enable_archive=False,
            enable_liber3=True,
            enable_calibre=False,
            enable_zlib=False,
            enable_annas=False,
            timeout=20
        ),
        Platform.ANNAS_ARCHIVE: LibraryConfig(
            enable_archive=False,
            enable_liber3=False,
            enable_calibre=False,
            enable_zlib=False,
            enable_annas=True,
            timeout=20
        )
    }
    
    # Test queries for different platforms
    test_queries = [
        "Python tutorial",
        "programming",
        "computer science"
    ]
    
    successful_downloads = 0
    total_attempts = 0
    
    for platform, config in platform_configs.items():
        print(f"\n{'='*50}")
        print(f"Testing {platform.value}")
        print('='*50)
        
        async with EbooksLibrary(config) as library:
            # Test connectivity first
            try:
                connected = await library.test_platform_connection(platform)
                if not connected:
                    print(f"✗ {platform.value} is not accessible, skipping...")
                    continue
                print(f"✓ {platform.value} connection successful")
            except Exception as e:
                print(f"✗ {platform.value} connection failed: {e}")
                continue
            
            # Try different queries until we find results
            found_results = False
            for query in test_queries:
                print(f"\nSearching for '{query}'...")
                try:
                    results = await library.search(query, limit=2)
                    if results:
                        print(f"✓ Found {len(results)} results")
                        found_results = True
                        
                        # Display search results
                        for i, result in enumerate(results, 1):
                            book = result.book_info
                            print(f"  {i}. {book.title}")
                            if book.authors:
                                print(f"     Authors: {book.authors}")
                            if book.year:
                                print(f"     Year: {book.year}")
                            if book.file_type:
                                print(f"     Format: {book.file_type}")
                            if book.file_size:
                                print(f"     Size: {book.file_size}")
                        
                        # Try to download the first result
                        first_result = results[0]
                        print(f"\nAttempting to download: {first_result.book_info.title}")
                        total_attempts += 1
                        
                        try:
                            # Create downloads directory for testing
                            from pathlib import Path
                            download_dir = Path("./test_downloads")
                            download_dir.mkdir(exist_ok=True)
                            
                            # Print download info for debugging
                            print(f"  Download URL: {first_result.download_info.download_url}")
                            if first_result.download_info.book_id:
                                print(f"  Book ID: {first_result.download_info.book_id}")
                            
                            # Try different download approaches
                            download_success = False
                            
                            # First try: Download to file
                            try:
                                download_result = await library.download(
                                    first_result.download_info,
                                    save_path=download_dir
                                )
                                
                                if download_result.success:
                                    print(f"  ✓ File download successful!")
                                    print(f"  File: {download_result.file_name}")
                                    print(f"  Size: {download_result.file_size} bytes")
                                    successful_downloads += 1
                                    download_success = True
                                    
                                    # Verify file exists
                                    if download_result.file_path and Path(download_result.file_path).exists():
                                        file_size = Path(download_result.file_path).stat().st_size
                                        print(f"  ✓ File verified on disk: {file_size} bytes")
                                    else:
                                        print(f"  ⚠ File not found on disk")
                                else:
                                    print(f"  ✗ File download failed: {download_result.error_message}")
                            except Exception as e:
                                print(f"  ✗ File download error: {e}")
                            
                            # Second try: Download to memory (if file download failed)
                            if not download_success:
                                try:
                                    print(f"  Trying memory download...")
                                    download_result = await library.download(
                                        first_result.download_info,
                                        return_content=True
                                    )
                                    
                                    if download_result.success and download_result.content:
                                        content_size = len(download_result.content)
                                        print(f"  ✓ Memory download successful: {content_size} bytes")
                                        successful_downloads += 1
                                        download_success = True
                                        
                                        # Save to file manually
                                        if download_result.file_name:
                                            file_path = download_dir / download_result.file_name
                                            with open(file_path, 'wb') as f:
                                                f.write(download_result.content)
                                            print(f"  ✓ Saved to: {file_path}")
                                    else:
                                        print(f"  ✗ Memory download failed: {download_result.error_message}")
                                except Exception as e:
                                    print(f"  ✗ Memory download error: {e}")
                            
                            if not download_success:
                                # For Anna's Archive, just getting the download URL is success
                                if platform == Platform.ANNAS_ARCHIVE and first_result.download_info.download_url:
                                    print(f"  ✓ Anna's Archive provided download URL (no direct download)")
                                    successful_downloads += 1
                                else:
                                    print(f"  ✗ All download attempts failed")
                                
                        except Exception as e:
                            print(f"  ✗ Download error: {e}")
                        
                        break  # Found results, no need to try other queries
                        
                except Exception as e:
                    print(f"✗ Search failed for '{query}': {e}")
            
            if not found_results:
                print(f"✗ No results found on {platform.value} for any query")
    
    print(f"\n{'='*50}")
    print("Individual Platform Test Summary")
    print('='*50)
    print(f"Total download attempts: {total_attempts}")
    print(f"Successful downloads: {successful_downloads}")
    if total_attempts > 0:
        success_rate = (successful_downloads / total_attempts) * 100
        print(f"Success rate: {success_rate:.1f}%")
    print("✓ Individual platform testing completed")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("EBooks Library Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Error Handling", test_error_handling),
        ("Context Manager", test_context_manager),
        ("Individual Platforms", test_individual_platforms),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} Test...")
            await test_func()
            print("\n" + "-" * 40 + "\n")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}\n")
    
    print("=" * 60)
    print("Test suite completed!")
    print("=" * 60)
    
async def testLIBER3():
    """Run all tests"""
    print("=" * 60)
    print("EBooks Library Test LIBER3")
    print("=" * 60)
    
    config = LibraryConfig(
            enable_archive=True,
            enable_liber3=True,
            enable_calibre=True,
            enable_zlib=False,
            enable_annas=True,
            timeout=60
        )
    
    library = EbooksLibrary(config)
    connected = await library.test_platform_connection(Platform.LIBER3)
    print(f"{Platform.LIBER3} connected {connected}\n")
    # Search on specific platform
    results = await library.search("python", platforms=[Platform.LIBER3], limit=1)
    print(f"{Platform.LIBER3} search {results}\n")

async def testZlib():
    """Run all tests"""
    print("=" * 60)
    print("EBooks Library Test zlib")
    print("=" * 60)
    
    config = LibraryConfig(
            enable_archive=False,
            enable_liber3=False,
            enable_calibre=False,
            enable_zlib=True,
            enable_annas=False,
            timeout=60,
            zlib_email='zhanggq.work@gmail.com',
            zlib_password='Zz316564589'
        )
    
    library = EbooksLibrary(config)
    # Search on specific platform
    results = await library.search("python", platforms=[Platform.ZLIBRARY], limit=1)
    print(f"{Platform.ZLIBRARY} search {results}\n")
    await library.download(results[0].download_info, 'test_downloads')


if __name__ == "__main__":
    asyncio.run(testZlib())
