#!/usr/bin/env python3
"""
Quick start script for ebooks-library

This script demonstrates the basic functionality of the ebooks library.
Run this after installing the library to verify everything works correctly.
"""

import asyncio
import sys
from pathlib import Path

try:
    from ebooks_library import EbooksLibrary, LibraryConfig, Platform
    print("✅ ebooks-library imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import ebooks-library: {e}")
    print("Please install the library first:")
    print("  pip install -e .")
    sys.exit(1)


async def quick_demo():
    """Quick demonstration of library capabilities"""
    print("\n" + "="*60)
    print("🚀 EBooks Library Quick Start Demo")
    print("="*60)
    
    # Create library with basic config
    config = LibraryConfig(
        enable_archive=True,
        enable_liber3=True,
        max_results=3,
        timeout=10
    )
    
    async with EbooksLibrary(config) as library:
        # Show enabled platforms
        platforms = library.get_enabled_platforms()
        print(f"\n📚 Enabled platforms: {[p.value for p in platforms]}")
        
        # Test connectivity
        print("\n🔍 Testing platform connectivity...")
        for platform in platforms:
            try:
                connected = await library.test_platform_connection(platform)
                status = "✅ Connected" if connected else "❌ Failed"
                print(f"  {platform.value}: {status}")
            except Exception as e:
                print(f"  {platform.value}: ❌ Error - {e}")
        
        # Perform a search
        print(f"\n🔎 Searching for 'Python tutorial'...")
        try:
            results = await library.search("Python tutorial", limit=3)
            
            if results:
                print(f"✅ Found {len(results)} books:")
                for i, result in enumerate(results, 1):
                    book = result.book_info
                    print(f"\n  {i}. {book.title}")
                    print(f"     Authors: {book.authors or 'Unknown'}")
                    print(f"     Platform: {result.platform.value}")
                    if book.year:
                        print(f"     Year: {book.year}")
                    
                # Try to download the first result to memory
                print(f"\n💾 Attempting to download first book to memory...")
                first_result = results[0]
                
                try:
                    download_result = await library.download(
                        first_result.download_info,
                        return_content=True
                    )
                    
                    if download_result.success:
                        size_mb = len(download_result.content) / (1024 * 1024)
                        print(f"✅ Successfully downloaded {download_result.file_name}")
                        print(f"   Size: {size_mb:.2f} MB")
                    else:
                        print(f"❌ Download failed: {download_result.error_message}")
                        
                except Exception as e:
                    print(f"❌ Download error: {e}")
                    
            else:
                print("❌ No books found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print("\n" + "="*60)
    print("✨ Demo completed!")
    print("\nNext steps:")
    print("  • Check out examples/ directory for more usage examples")
    print("  • Read README_LIBRARY.md for comprehensive documentation")
    print("  • Try the CLI tools: ebooks-search, ebooks-download")
    print("="*60)


if __name__ == "__main__":
    print("Starting ebooks-library quick start demo...")
    try:
        asyncio.run(quick_demo())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Demo failed with error: {e}")
        sys.exit(1)
