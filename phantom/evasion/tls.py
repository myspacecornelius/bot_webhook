"""
TLS Fingerprint Management
Evades JA3/JA4 fingerprint detection by using curl-impersonate
"""

import random
from typing import Optional, Dict, Any
from enum import Enum
import structlog

logger = structlog.get_logger()


class BrowserImpersonation(Enum):
    """Available browser impersonations via curl-cffi"""
    CHROME_99 = "chrome99"
    CHROME_100 = "chrome100"
    CHROME_101 = "chrome101"
    CHROME_104 = "chrome104"
    CHROME_107 = "chrome107"
    CHROME_110 = "chrome110"
    CHROME_116 = "chrome116"
    CHROME_119 = "chrome119"
    CHROME_120 = "chrome120"
    SAFARI_15_3 = "safari15_3"
    SAFARI_15_5 = "safari15_5"
    SAFARI_17_0 = "safari17_0"
    EDGE_99 = "edge99"
    EDGE_101 = "edge101"


class TLSManager:
    """
    Manages TLS fingerprint rotation to evade JA3/JA4 detection
    Uses curl-cffi for impersonating real browser TLS signatures
    """
    
    # JA3 hashes for common browsers (for reference/validation)
    JA3_HASHES = {
        "chrome_120": "773906b0efdefa24a7f2b8eb6985bf37",
        "chrome_116": "c4ed18127e2f69c57dd63b894fdbf8bc",
        "safari_17": "7c02dbae662670040c7af9bd15fb7e2f",
        "firefox_121": "d9bca45b8a7c90c0f92e5f3c9595a8d5",
    }
    
    # HTTP/2 settings for different browsers
    H2_SETTINGS = {
        "chrome": {
            "HEADER_TABLE_SIZE": 65536,
            "ENABLE_PUSH": 0,
            "MAX_CONCURRENT_STREAMS": 1000,
            "INITIAL_WINDOW_SIZE": 6291456,
            "MAX_HEADER_LIST_SIZE": 262144,
        },
        "safari": {
            "HEADER_TABLE_SIZE": 4096,
            "ENABLE_PUSH": 0,
            "MAX_CONCURRENT_STREAMS": 100,
            "INITIAL_WINDOW_SIZE": 2097152,
            "MAX_HEADER_LIST_SIZE": 16384,
        },
        "firefox": {
            "HEADER_TABLE_SIZE": 65536,
            "ENABLE_PUSH": 0,
            "MAX_CONCURRENT_STREAMS": 100,
            "INITIAL_WINDOW_SIZE": 131072,
            "MAX_HEADER_LIST_SIZE": 65536,
        },
    }
    
    def __init__(self):
        self._current_impersonation: Optional[BrowserImpersonation] = None
        self._rotation_count = 0
        logger.info("TLSManager initialized")
    
    def get_impersonation(self, browser_type: str = "chrome") -> BrowserImpersonation:
        """Get a browser impersonation for curl-cffi"""
        if browser_type == "chrome":
            options = [
                BrowserImpersonation.CHROME_119,
                BrowserImpersonation.CHROME_120,
                BrowserImpersonation.CHROME_116,
            ]
        elif browser_type == "safari":
            options = [
                BrowserImpersonation.SAFARI_17_0,
                BrowserImpersonation.SAFARI_15_5,
            ]
        else:
            options = list(BrowserImpersonation)
        
        self._current_impersonation = random.choice(options)
        return self._current_impersonation
    
    def rotate_impersonation(self) -> BrowserImpersonation:
        """Rotate to a different browser impersonation"""
        all_options = list(BrowserImpersonation)
        
        if self._current_impersonation:
            all_options.remove(self._current_impersonation)
        
        self._current_impersonation = random.choice(all_options)
        self._rotation_count += 1
        
        logger.debug(
            "TLS impersonation rotated",
            new=self._current_impersonation.value,
            rotation_count=self._rotation_count
        )
        
        return self._current_impersonation
    
    def get_curl_cffi_session_kwargs(
        self,
        impersonation: Optional[BrowserImpersonation] = None
    ) -> Dict[str, Any]:
        """Get kwargs for curl_cffi AsyncSession"""
        if impersonation is None:
            impersonation = self._current_impersonation or self.get_impersonation()
        
        return {
            "impersonate": impersonation.value,
            "timeout": 30,
        }
    
    def get_headers_order(self, browser_type: str = "chrome") -> list:
        """Get realistic header order for browser type"""
        if browser_type == "chrome":
            return [
                "Host",
                "Connection",
                "sec-ch-ua",
                "sec-ch-ua-mobile",
                "sec-ch-ua-platform",
                "Upgrade-Insecure-Requests",
                "User-Agent",
                "Accept",
                "Sec-Fetch-Site",
                "Sec-Fetch-Mode",
                "Sec-Fetch-User",
                "Sec-Fetch-Dest",
                "Accept-Encoding",
                "Accept-Language",
                "Cookie",
            ]
        elif browser_type == "safari":
            return [
                "Host",
                "Accept",
                "Accept-Language",
                "Accept-Encoding",
                "Connection",
                "User-Agent",
                "Cookie",
            ]
        elif browser_type == "firefox":
            return [
                "Host",
                "User-Agent",
                "Accept",
                "Accept-Language",
                "Accept-Encoding",
                "Connection",
                "Cookie",
                "Upgrade-Insecure-Requests",
            ]
        
        return []
    
    def get_sec_ch_ua(self, impersonation: BrowserImpersonation) -> Dict[str, str]:
        """Get Sec-CH-UA headers for Chrome impersonation"""
        version_map = {
            BrowserImpersonation.CHROME_120: ("120", "120.0.0.0"),
            BrowserImpersonation.CHROME_119: ("119", "119.0.0.0"),
            BrowserImpersonation.CHROME_116: ("116", "116.0.0.0"),
            BrowserImpersonation.CHROME_110: ("110", "110.0.0.0"),
        }
        
        if impersonation not in version_map:
            return {}
        
        major, full = version_map[impersonation]
        
        return {
            "sec-ch-ua": f'"Not_A Brand";v="8", "Chromium";v="{major}", "Google Chrome";v="{major}"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }


def create_stealth_session(browser_type: str = "chrome"):
    """Create a curl-cffi session with stealth settings"""
    try:
        from curl_cffi.requests import AsyncSession
        
        tls_manager = TLSManager()
        impersonation = tls_manager.get_impersonation(browser_type)
        
        session = AsyncSession(**tls_manager.get_curl_cffi_session_kwargs(impersonation))
        
        return session, tls_manager
    except ImportError:
        logger.warning("curl-cffi not available, using standard httpx")
        return None, None
