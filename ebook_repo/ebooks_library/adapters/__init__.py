"""
Third-party API adapters for ebooks library

This module contains adapters for external ebook services and APIs.
"""

# Import adapters for easier access
try:
    from .Zlibrary import Zlibrary
except ImportError:
    Zlibrary = None

try:
    from . import annas_py
except ImportError:
    annas_py = None

__all__ = ['Zlibrary', 'annas_py']
