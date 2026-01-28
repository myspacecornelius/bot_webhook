"""
Human Behavior Simulation
Makes bot actions appear more human-like to evade behavioral analysis
"""

import asyncio
import random
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class MouseMovement:
    """A single mouse movement point"""
    x: float
    y: float
    timestamp: float


class Humanizer:
    """
    Simulates human-like behavior patterns for bot evasion
    - Mouse movements with bezier curves
    - Realistic typing with mistakes
    - Random micro-pauses
    - Scroll patterns
    """
    
    def __init__(self):
        self.typing_speed_wpm = random.randint(45, 75)  # Words per minute
        self.mouse_speed = random.uniform(0.8, 1.2)  # Movement speed multiplier
        logger.info("Humanizer initialized", typing_wpm=self.typing_speed_wpm)
    
    async def random_delay(self, min_ms: int = 50, max_ms: int = 200):
        """Add a random human-like delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def thinking_delay(self):
        """Simulate human thinking time"""
        # Humans pause to read/think - follows log-normal distribution
        delay = random.lognormvariate(0, 0.5) * 0.3 + 0.1
        delay = min(delay, 2.0)  # Cap at 2 seconds
        await asyncio.sleep(delay)
    
    def generate_bezier_curve(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        num_points: int = 20
    ) -> List[Tuple[float, float]]:
        """Generate bezier curve points for mouse movement"""
        # Add control points for natural curve
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        # Random control point offsets based on distance
        offset = distance * 0.3
        
        ctrl1 = (
            start[0] + (end[0] - start[0]) * 0.25 + random.uniform(-offset, offset),
            start[1] + (end[1] - start[1]) * 0.25 + random.uniform(-offset, offset)
        )
        ctrl2 = (
            start[0] + (end[0] - start[0]) * 0.75 + random.uniform(-offset, offset),
            start[1] + (end[1] - start[1]) * 0.75 + random.uniform(-offset, offset)
        )
        
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            
            # Cubic bezier formula
            x = (1-t)**3 * start[0] + 3*(1-t)**2*t * ctrl1[0] + 3*(1-t)*t**2 * ctrl2[0] + t**3 * end[0]
            y = (1-t)**3 * start[1] + 3*(1-t)**2*t * ctrl1[1] + 3*(1-t)*t**2 * ctrl2[1] + t**3 * end[1]
            
            # Add slight noise
            x += random.gauss(0, 0.5)
            y += random.gauss(0, 0.5)
            
            points.append((x, y))
        
        return points
    
    def generate_mouse_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> List[MouseMovement]:
        """Generate realistic mouse movement path with timing"""
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        # More points for longer distances
        num_points = max(10, int(distance / 20))
        
        # Base duration based on Fitts' Law approximation
        base_duration = 0.1 + math.log2(distance / 10 + 1) * 0.15
        base_duration *= self.mouse_speed
        
        curve_points = self.generate_bezier_curve(start, end, num_points)
        
        movements = []
        for i, (x, y) in enumerate(curve_points):
            # Non-linear timing (accelerate then decelerate)
            t = i / len(curve_points)
            # Ease in-out function
            timing = t * t * (3 - 2 * t)
            timestamp = timing * base_duration
            
            movements.append(MouseMovement(x=x, y=y, timestamp=timestamp))
        
        return movements
    
    async def type_text(
        self,
        page,  # Playwright page
        selector: str,
        text: str,
        make_mistakes: bool = True
    ):
        """Type text with human-like timing and occasional mistakes"""
        element = await page.query_selector(selector)
        if not element:
            return
        
        await element.click()
        await self.random_delay(100, 300)
        
        # Calculate base delay per character
        chars_per_minute = self.typing_speed_wpm * 5
        base_delay = 60 / chars_per_minute
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Occasional mistake (3% chance)
            if make_mistakes and random.random() < 0.03 and char.isalpha():
                # Type wrong character
                wrong_char = self._get_adjacent_key(char)
                await page.keyboard.type(wrong_char, delay=int(base_delay * 1000 * random.uniform(0.8, 1.2)))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                # Backspace
                await page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Type correct character with variable timing
            delay = base_delay * random.uniform(0.7, 1.4)
            
            # Longer pause after spaces/punctuation
            if i > 0 and text[i-1] in ' .,!?':
                delay *= random.uniform(1.2, 1.8)
            
            await page.keyboard.type(char, delay=int(delay * 1000))
            
            # Occasional micro-pause (thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.2, 0.5))
            
            i += 1
    
    def _get_adjacent_key(self, char: str) -> str:
        """Get an adjacent key on QWERTY keyboard for realistic typos"""
        keyboard = {
            'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg',
            'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
            'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc',
            'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiolm',
            'l': 'kop', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv',
            'v': 'cfgb', 'b': 'vghn', 'n': 'bhjm', 'm': 'njk',
        }
        
        adjacent = keyboard.get(char.lower(), char)
        return random.choice(adjacent) if adjacent else char
    
    async def move_mouse(self, page, x: float, y: float, current_pos: Optional[Tuple[float, float]] = None):
        """Move mouse along a realistic path"""
        if current_pos is None:
            current_pos = (0, 0)
        
        path = self.generate_mouse_path(current_pos, (x, y))
        
        for i, movement in enumerate(path):
            if i > 0:
                delay = movement.timestamp - path[i-1].timestamp
                await asyncio.sleep(delay)
            
            await page.mouse.move(movement.x, movement.y)
    
    async def human_click(self, page, selector: str, current_pos: Optional[Tuple[float, float]] = None):
        """Click with human-like mouse movement"""
        element = await page.query_selector(selector)
        if not element:
            return
        
        box = await element.bounding_box()
        if not box:
            return
        
        # Click somewhere within the element (not always center)
        target_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        target_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
        
        await self.move_mouse(page, target_x, target_y, current_pos)
        
        # Small delay before click
        await self.random_delay(30, 100)
        
        # Click with slight hold
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.12))
        await page.mouse.up()
        
        return (target_x, target_y)
    
    async def human_scroll(self, page, direction: str = "down", amount: int = 300):
        """Scroll with human-like behavior"""
        # Break into smaller scrolls
        remaining = amount
        
        while remaining > 0:
            # Variable scroll amounts
            scroll_amount = min(remaining, random.randint(50, 150))
            
            if direction == "down":
                await page.mouse.wheel(0, scroll_amount)
            else:
                await page.mouse.wheel(0, -scroll_amount)
            
            remaining -= scroll_amount
            
            # Variable delay between scrolls
            await asyncio.sleep(random.uniform(0.02, 0.08))
        
        # Pause after scrolling (reading)
        await asyncio.sleep(random.uniform(0.3, 0.8))
    
    def get_realistic_checkout_timing(self) -> dict:
        """Get realistic timing for checkout flow"""
        return {
            "page_load_wait": random.uniform(0.5, 1.5),
            "form_focus_delay": random.uniform(0.2, 0.5),
            "between_fields": random.uniform(0.3, 0.8),
            "before_submit": random.uniform(0.5, 1.2),
            "read_error": random.uniform(1.0, 2.0),
            "captcha_start": random.uniform(0.5, 1.0),
        }
