"""
Advanced Keyword Matching Engine
Supports positive/negative keywords, SKU matching, regex patterns
"""

import re
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class KeywordSet:
    """Set of keywords for matching"""
    positive: Set[str]  # Must contain at least one
    negative: Set[str]  # Must not contain any
    required: Set[str]  # Must contain all
    sku_patterns: Set[str]  # Exact SKU matches
    regex_patterns: List[re.Pattern]  # Regex patterns
    
    @classmethod
    def from_string(cls, keyword_string: str) -> 'KeywordSet':
        """
        Parse keyword string into KeywordSet
        Format:
            +keyword = positive (include)
            -keyword = negative (exclude)
            *keyword = required (must have)
            SKU:ABC123 = exact SKU match
            /regex/ = regex pattern
        """
        positive = set()
        negative = set()
        required = set()
        sku_patterns = set()
        regex_patterns = []
        
        for part in keyword_string.split(','):
            part = part.strip()
            if not part:
                continue
            
            if part.startswith('+'):
                positive.add(part[1:].lower().strip())
            elif part.startswith('-'):
                negative.add(part[1:].lower().strip())
            elif part.startswith('*'):
                required.add(part[1:].lower().strip())
            elif part.upper().startswith('SKU:'):
                sku_patterns.add(part[4:].strip().upper())
            elif part.startswith('/') and part.endswith('/'):
                try:
                    regex_patterns.append(re.compile(part[1:-1], re.IGNORECASE))
                except re.error:
                    logger.warning("Invalid regex pattern", pattern=part)
            else:
                # Default to positive keyword
                positive.add(part.lower().strip())
        
        return cls(
            positive=positive,
            negative=negative,
            required=required,
            sku_patterns=sku_patterns,
            regex_patterns=regex_patterns
        )
    
    def to_string(self) -> str:
        """Convert back to keyword string"""
        parts = []
        parts.extend(f"+{k}" for k in self.positive)
        parts.extend(f"-{k}" for k in self.negative)
        parts.extend(f"*{k}" for k in self.required)
        parts.extend(f"SKU:{s}" for s in self.sku_patterns)
        parts.extend(f"/{p.pattern}/" for p in self.regex_patterns)
        return ', '.join(parts)


class KeywordMatcher:
    """
    Intelligent keyword matching for product monitoring
    """
    
    # Common sneaker brand keywords for auto-expansion
    BRAND_EXPANSIONS = {
        "jordan": ["jordan", "aj", "air jordan"],
        "dunk": ["dunk", "sb dunk", "dunk low", "dunk high"],
        "yeezy": ["yeezy", "yzy", "adidas yeezy"],
        "nike": ["nike"],
        "adidas": ["adidas", "adi"],
        "new balance": ["new balance", "nb", "newbalance"],
        "af1": ["air force 1", "af1", "air force one", "forces"],
    }
    
    # Size keywords
    SIZE_PATTERNS = [
        r"size\s*(\d+(?:\.\d+)?)",
        r"sz\s*(\d+(?:\.\d+)?)",
        r"us\s*(\d+(?:\.\d+)?)",
    ]
    
    def __init__(self, keywords: Optional[KeywordSet] = None):
        self.keywords = keywords or KeywordSet(set(), set(), set(), set(), [])
        self._compiled_size_patterns = [re.compile(p, re.IGNORECASE) for p in self.SIZE_PATTERNS]
    
    @classmethod
    def from_string(cls, keyword_string: str) -> 'KeywordMatcher':
        """Create matcher from keyword string"""
        return cls(KeywordSet.from_string(keyword_string))
    
    def matches(
        self,
        title: str,
        sku: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, float]:
        """
        Check if product matches keywords
        Returns (matches: bool, confidence: float 0-1)
        """
        title_lower = title.lower()
        combined_text = title_lower
        
        if description:
            combined_text += " " + description.lower()
        
        # Check SKU patterns first (highest priority)
        if sku and self.keywords.sku_patterns:
            sku_upper = sku.upper()
            for pattern in self.keywords.sku_patterns:
                if pattern in sku_upper or sku_upper in pattern:
                    return True, 1.0
        
        # Check negative keywords (instant reject)
        for neg in self.keywords.negative:
            if neg in combined_text:
                return False, 0.0
        
        # Check required keywords (must all be present)
        for req in self.keywords.required:
            if req not in combined_text:
                return False, 0.0
        
        # Check regex patterns
        for pattern in self.keywords.regex_patterns:
            if pattern.search(combined_text):
                return True, 0.9
        
        # Check positive keywords
        if self.keywords.positive:
            matched_positive = sum(1 for pos in self.keywords.positive if pos in combined_text)
            if matched_positive == 0:
                return False, 0.0
            
            # Confidence based on how many positive keywords matched
            confidence = min(1.0, 0.5 + (matched_positive / len(self.keywords.positive)) * 0.5)
            return True, confidence
        
        # No keywords specified - match everything (monitor mode)
        if not self.keywords.positive and not self.keywords.sku_patterns:
            return True, 0.5
        
        return False, 0.0
    
    def extract_size(self, text: str) -> Optional[str]:
        """Extract size from product text"""
        for pattern in self._compiled_size_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None
    
    def expand_brand_keywords(self) -> 'KeywordMatcher':
        """Expand brand keywords to include variations"""
        expanded_positive = set(self.keywords.positive)
        
        for keyword in list(self.keywords.positive):
            for brand, variations in self.BRAND_EXPANSIONS.items():
                if brand in keyword or keyword in brand:
                    expanded_positive.update(variations)
        
        new_keywords = KeywordSet(
            positive=expanded_positive,
            negative=self.keywords.negative,
            required=self.keywords.required,
            sku_patterns=self.keywords.sku_patterns,
            regex_patterns=self.keywords.regex_patterns
        )
        
        return KeywordMatcher(new_keywords)
    
    @staticmethod
    def generate_keywords_for_product(
        product_name: str,
        sku: Optional[str] = None,
        brand: Optional[str] = None
    ) -> str:
        """Auto-generate optimal keywords for a product"""
        keywords = []
        
        # Add SKU if available
        if sku:
            keywords.append(f"SKU:{sku}")
        
        # Extract key terms from product name
        name_lower = product_name.lower()
        
        # Remove common filler words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = [w for w in name_lower.split() if w not in stopwords and len(w) > 2]
        
        # Add brand if specified
        if brand:
            keywords.append(f"+{brand.lower()}")
        
        # Add significant words as required keywords
        for word in words[:3]:  # Top 3 words
            if word.isalnum():
                keywords.append(f"*{word}")
        
        # Add negative keywords for common unwanted items
        keywords.extend(["-gs", "-gradeschool", "-toddler", "-infant", "-ps"])
        
        return ', '.join(keywords)
    
    def get_stats(self) -> dict:
        """Get keyword statistics"""
        return {
            "positive_count": len(self.keywords.positive),
            "negative_count": len(self.keywords.negative),
            "required_count": len(self.keywords.required),
            "sku_count": len(self.keywords.sku_patterns),
            "regex_count": len(self.keywords.regex_patterns),
            "keywords_string": self.keywords.to_string(),
        }
