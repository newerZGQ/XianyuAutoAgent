"""
Exception classes for ebooks library
"""


class EbooksLibraryError(Exception):
    """Base exception for ebooks library"""
    pass


class SearchError(EbooksLibraryError):
    """Exception raised during search operations"""
    def __init__(self, message: str, platform: str = None):
        self.platform = platform
        super().__init__(message)


class DownloadError(EbooksLibraryError):
    """Exception raised during download operations"""
    def __init__(self, message: str, platform: str = None):
        self.platform = platform
        super().__init__(message)


class AuthenticationError(EbooksLibraryError):
    """Exception raised for authentication failures"""
    def __init__(self, message: str, platform: str = None):
        self.platform = platform
        super().__init__(message)


class ConfigurationError(EbooksLibraryError):
    """Exception raised for configuration issues"""
    pass


class NetworkError(EbooksLibraryError):
    """Exception raised for network-related issues"""
    pass


class PlatformError(EbooksLibraryError):
    """Exception raised for platform-specific issues"""
    def __init__(self, message: str, platform: str = None):
        self.platform = platform
        super().__init__(message)
