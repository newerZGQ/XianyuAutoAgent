from typing import Dict, List
from ebook_repo.ebooks_library.core import EbooksLibrary
from ebook_repo.ebooks_library.models import LibraryConfig, Platform

class EbookModule :
    async def searchBook(title, isbn) -> List[Dict[str, str]]:
        config = LibraryConfig(
            enable_archive=False,
            enable_liber3=False,
            enable_calibre=False,
            enable_zlib=True,
            enable_annas=False,
            timeout=15,
            zlib_email='zhanggq.work@gmail.com',
            zlib_password='Zz316564589'
        )
        library = EbooksLibrary(config)
        # Search on specific platform
        results = await library.search(title, platforms=[Platform.ZLIBRARY], limit=5)
        print(f"{Platform.ZLIBRARY} search title:{title} isbn:{isbn} {results}")