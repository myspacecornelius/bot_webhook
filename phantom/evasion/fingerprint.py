"""
Browser Fingerprint Randomization
Evades fingerprint-based bot detection by randomizing browser characteristics
"""

import random
import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class ScreenConfig:
    """Screen/display configuration"""
    width: int = 1920
    height: int = 1080
    avail_width: int = 1920
    avail_height: int = 1040
    color_depth: int = 24
    pixel_depth: int = 24
    device_pixel_ratio: float = 1.0


@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint"""
    user_agent: str = ""
    platform: str = "Win32"
    vendor: str = "Google Inc."
    language: str = "en-US"
    languages: List[str] = field(default_factory=lambda: ["en-US", "en"])
    timezone: str = "America/New_York"
    timezone_offset: int = 300
    
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    
    # Hardware
    hardware_concurrency: int = 8
    device_memory: int = 8
    max_touch_points: int = 0
    
    # WebGL
    webgl_vendor: str = "Google Inc. (NVIDIA)"
    webgl_renderer: str = "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)"
    
    # Canvas noise seed
    canvas_noise_seed: int = field(default_factory=lambda: random.randint(1, 1000000))
    
    # Audio context
    audio_context_hash: str = ""
    
    # Plugins
    plugins: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "userAgent": self.user_agent,
            "platform": self.platform,
            "vendor": self.vendor,
            "language": self.language,
            "languages": self.languages,
            "timezone": self.timezone,
            "timezoneOffset": self.timezone_offset,
            "screen": {
                "width": self.screen.width,
                "height": self.screen.height,
                "availWidth": self.screen.avail_width,
                "availHeight": self.screen.avail_height,
                "colorDepth": self.screen.color_depth,
                "pixelDepth": self.screen.pixel_depth,
                "devicePixelRatio": self.screen.device_pixel_ratio,
            },
            "hardwareConcurrency": self.hardware_concurrency,
            "deviceMemory": self.device_memory,
            "maxTouchPoints": self.max_touch_points,
            "webglVendor": self.webgl_vendor,
            "webglRenderer": self.webgl_renderer,
            "canvasNoiseSeed": self.canvas_noise_seed,
        }


class FingerprintManager:
    """
    Manages browser fingerprint generation and injection
    Creates realistic, randomized fingerprints to evade detection
    """
    
    # Common screen resolutions
    RESOLUTIONS = [
        (1920, 1080), (2560, 1440), (1366, 768), (1536, 864),
        (1440, 900), (1280, 720), (1600, 900), (3840, 2160),
    ]
    
    # User agent templates
    USER_AGENTS = {
        "chrome_win": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
        ],
        "chrome_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
        ],
        "firefox_win": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}",
        ],
        "safari_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15",
        ],
    }
    
    CHROME_VERSIONS = ["120.0.0.0", "121.0.0.0", "122.0.0.0", "123.0.0.0", "124.0.0.0"]
    FIREFOX_VERSIONS = ["121.0", "122.0", "123.0", "124.0"]
    SAFARI_VERSIONS = ["17.0", "17.1", "17.2", "17.3"]
    
    # WebGL renderers by GPU brand
    WEBGL_RENDERERS = {
        "nvidia": [
            "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Direct3D11 vs_5_0 ps_5_0)",
        ],
        "amd": [
            "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD, AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD, AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)",
        ],
        "intel": [
            "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
        ],
        "apple": [
            "Apple GPU",
            "Apple M1",
            "Apple M2",
        ],
    }
    
    TIMEZONES = [
        ("America/New_York", 300),
        ("America/Chicago", 360),
        ("America/Denver", 420),
        ("America/Los_Angeles", 480),
        ("America/Phoenix", 420),
    ]
    
    def __init__(self):
        self._fingerprint_cache: Dict[str, BrowserFingerprint] = {}
        logger.info("FingerprintManager initialized")
    
    def generate(
        self,
        browser_type: str = "chrome",
        os_type: str = "windows",
        seed: Optional[str] = None
    ) -> BrowserFingerprint:
        """
        Generate a randomized but consistent fingerprint
        Use seed for reproducible fingerprints (e.g., per-task consistency)
        """
        if seed and seed in self._fingerprint_cache:
            return self._fingerprint_cache[seed]
        
        if seed:
            random.seed(hashlib.md5(seed.encode()).hexdigest())
        
        fp = BrowserFingerprint()
        
        # User agent
        if browser_type == "chrome":
            if os_type == "mac":
                template = random.choice(self.USER_AGENTS["chrome_mac"])
                fp.platform = "MacIntel"
            else:
                template = random.choice(self.USER_AGENTS["chrome_win"])
                fp.platform = "Win32"
            fp.user_agent = template.format(version=random.choice(self.CHROME_VERSIONS))
            fp.vendor = "Google Inc."
            
        elif browser_type == "firefox":
            template = random.choice(self.USER_AGENTS["firefox_win"])
            fp.user_agent = template.format(version=random.choice(self.FIREFOX_VERSIONS))
            fp.vendor = ""
            
        elif browser_type == "safari":
            template = random.choice(self.USER_AGENTS["safari_mac"])
            fp.user_agent = template.format(version=random.choice(self.SAFARI_VERSIONS))
            fp.platform = "MacIntel"
            fp.vendor = "Apple Computer, Inc."
        
        # Screen
        resolution = random.choice(self.RESOLUTIONS)
        fp.screen = ScreenConfig(
            width=resolution[0],
            height=resolution[1],
            avail_width=resolution[0],
            avail_height=resolution[1] - random.randint(30, 50),
            device_pixel_ratio=random.choice([1.0, 1.25, 1.5, 2.0]),
        )
        
        # Hardware
        fp.hardware_concurrency = random.choice([4, 6, 8, 12, 16])
        fp.device_memory = random.choice([4, 8, 16, 32])
        
        # WebGL
        if os_type == "mac":
            fp.webgl_vendor = "Apple Inc."
            fp.webgl_renderer = random.choice(self.WEBGL_RENDERERS["apple"])
        else:
            gpu_brand = random.choice(["nvidia", "amd", "intel"])
            fp.webgl_vendor = f"Google Inc. ({gpu_brand.upper()})"
            fp.webgl_renderer = random.choice(self.WEBGL_RENDERERS[gpu_brand])
        
        # Timezone
        tz = random.choice(self.TIMEZONES)
        fp.timezone = tz[0]
        fp.timezone_offset = tz[1]
        
        # Canvas noise
        fp.canvas_noise_seed = random.randint(1, 1000000)
        
        # Reset random seed
        if seed:
            random.seed()
            self._fingerprint_cache[seed] = fp
        
        return fp
    
    def get_injection_script(self, fingerprint: BrowserFingerprint) -> str:
        """
        Generate JavaScript to inject fingerprint into page
        Should be executed before any other scripts
        """
        fp_json = json.dumps(fingerprint.to_dict())
        
        return f"""
        (function() {{
            const fp = {fp_json};
            
            // Override navigator properties
            const navigatorProps = {{
                userAgent: fp.userAgent,
                platform: fp.platform,
                vendor: fp.vendor,
                language: fp.language,
                languages: fp.languages,
                hardwareConcurrency: fp.hardwareConcurrency,
                deviceMemory: fp.deviceMemory,
                maxTouchPoints: fp.maxTouchPoints,
            }};
            
            for (const [key, value] of Object.entries(navigatorProps)) {{
                Object.defineProperty(navigator, key, {{
                    get: () => value,
                    configurable: true
                }});
            }}
            
            // Override screen properties
            const screenProps = fp.screen;
            for (const [key, value] of Object.entries(screenProps)) {{
                Object.defineProperty(screen, key, {{
                    get: () => value,
                    configurable: true
                }});
            }}
            
            // Override devicePixelRatio
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => fp.screen.devicePixelRatio,
                configurable: true
            }});
            
            // Canvas fingerprint noise
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {{
                const ctx = this.getContext('2d');
                if (ctx) {{
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        imageData.data[i] ^= (fp.canvasNoiseSeed % 3);
                    }}
                    ctx.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.apply(this, arguments);
            }};
            
            // WebGL fingerprint
            const getParameterProxyHandler = {{
                apply: function(target, thisArg, args) {{
                    const param = args[0];
                    if (param === 37445) return fp.webglVendor;
                    if (param === 37446) return fp.webglRenderer;
                    return Reflect.apply(target, thisArg, args);
                }}
            }};
            
            try {{
                WebGLRenderingContext.prototype.getParameter = new Proxy(
                    WebGLRenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
                WebGL2RenderingContext.prototype.getParameter = new Proxy(
                    WebGL2RenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
            }} catch(e) {{}}
            
            // Timezone
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...args) {{
                if (!args[1]) args[1] = {{}};
                args[1].timeZone = fp.timezone;
                return new originalDateTimeFormat(...args);
            }};
            
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});
            
            // Chrome-specific
            if (!window.chrome) {{
                window.chrome = {{
                    runtime: {{}},
                    loadTimes: function() {{}},
                    csi: function() {{}},
                    app: {{}}
                }};
            }}
            
            console.log('[Phantom] Fingerprint injected');
        }})();
        """
    
    def get_playwright_context_options(self, fingerprint: BrowserFingerprint) -> Dict[str, Any]:
        """Get Playwright context options for fingerprint"""
        return {
            "user_agent": fingerprint.user_agent,
            "viewport": {
                "width": fingerprint.screen.width,
                "height": fingerprint.screen.height,
            },
            "device_scale_factor": fingerprint.screen.device_pixel_ratio,
            "locale": fingerprint.language,
            "timezone_id": fingerprint.timezone,
            "color_scheme": "light",
        }
