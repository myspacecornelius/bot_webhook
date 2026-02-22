"""
Profile Rotation on Decline — Multi-Profile Retry Strategy

Reverse-engineered from Valor AIO's profile group rotation:
  - When a card is declined, rotate to the next profile in the group
  - Track which profiles have been tried per task
  - Avoid reusing declined profiles
  - Support both sequential and random rotation strategies
  - Configurable max rotations per task

Deep Search — Image URL Matching

Reverse-engineered from Valor AIO's Deep Search feature:
  - Matches products by image URL similarity, not just keywords
  - Downloads product images and computes perceptual hashes
  - Useful for detecting re-listed products under new names
  - Supplements keyword-based matching for higher accuracy
"""

import hashlib
import time
from typing import Optional, Dict, List, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger()


# =================================================================
# PROFILE ROTATION
# =================================================================


class RotationStrategy(Enum):
    SEQUENTIAL = "sequential"  # Try profiles in order
    RANDOM = "random"  # Random selection
    ROUND_ROBIN = "round_robin"  # Cycle through all


@dataclass
class RotationState:
    """Track profile rotation state for a single task"""

    task_id: str
    tried_profile_ids: List[str] = field(default_factory=list)
    declined_profile_ids: Set[str] = field(default_factory=set)
    current_index: int = 0
    max_rotations: int = 5
    last_rotation_time: float = 0.0

    @property
    def rotation_count(self) -> int:
        return len(self.tried_profile_ids)

    @property
    def can_rotate(self) -> bool:
        return self.rotation_count < self.max_rotations


class ProfileRotator:
    """
    Manages profile rotation on payment declines.

    When a checkout is declined, the rotator picks the next unused
    profile from the same profile group. This maximizes checkout
    probability across a pool of payment methods.

    Usage:
        rotator = ProfileRotator()

        # Get initial profile
        profile_id = rotator.get_profile(task_id, profile_group_id, profiles)

        # On decline, rotate to next
        next_profile_id = rotator.rotate_on_decline(task_id, profile_group_id, profiles)
    """

    def __init__(self, strategy: RotationStrategy = RotationStrategy.SEQUENTIAL):
        self.strategy = strategy
        self._states: Dict[str, RotationState] = {}
        self._global_decline_count: Dict[str, int] = {}  # profile_id → decline count

    def get_profile(
        self,
        task_id: str,
        available_profile_ids: List[str],
        max_rotations: int = 5,
    ) -> Optional[str]:
        """Get the current profile for a task, or the initial one."""
        state = self._get_or_create_state(task_id, max_rotations)

        if state.tried_profile_ids:
            # Return current profile
            return state.tried_profile_ids[-1]

        # Pick initial profile
        profile_id = self._select_profile(available_profile_ids, state)
        if profile_id:
            state.tried_profile_ids.append(profile_id)
        return profile_id

    def rotate_on_decline(
        self,
        task_id: str,
        available_profile_ids: List[str],
        declined_profile_id: Optional[str] = None,
    ) -> Optional[str]:
        """Rotate to the next profile after a decline.

        Returns the next profile ID, or None if exhausted.
        """
        state = self._states.get(task_id)
        if not state:
            state = self._get_or_create_state(task_id)

        # Record the decline
        if declined_profile_id:
            state.declined_profile_ids.add(declined_profile_id)
            count = self._global_decline_count.get(declined_profile_id, 0) + 1
            self._global_decline_count[declined_profile_id] = count

            logger.info(
                "Profile declined",
                task_id=task_id[:8],
                profile_id=declined_profile_id[:8],
                total_declines=count,
            )

        # Check if we can still rotate
        if not state.can_rotate:
            logger.warning("Max rotations reached", task_id=task_id[:8])
            return None

        # Find next untried profile
        untried = [
            pid
            for pid in available_profile_ids
            if pid not in state.tried_profile_ids
            and pid not in state.declined_profile_ids
        ]

        if not untried:
            logger.warning("All profiles exhausted", task_id=task_id[:8])
            return None

        # Select next
        next_profile_id = self._select_profile(untried, state)
        if next_profile_id:
            state.tried_profile_ids.append(next_profile_id)
            state.current_index += 1
            state.last_rotation_time = time.time()

            logger.info(
                "Profile rotated",
                task_id=task_id[:8],
                new_profile=next_profile_id[:8],
                rotation=state.rotation_count,
            )

        return next_profile_id

    def _select_profile(
        self, candidates: List[str], state: RotationState
    ) -> Optional[str]:
        """Select a profile based on the rotation strategy"""
        if not candidates:
            return None

        if self.strategy == RotationStrategy.SEQUENTIAL:
            return candidates[0]
        elif self.strategy == RotationStrategy.RANDOM:
            import random

            return random.choice(candidates)
        else:  # ROUND_ROBIN
            idx = state.current_index % len(candidates)
            return candidates[idx]

    def _get_or_create_state(
        self, task_id: str, max_rotations: int = 5
    ) -> RotationState:
        if task_id not in self._states:
            self._states[task_id] = RotationState(
                task_id=task_id,
                max_rotations=max_rotations,
            )
        return self._states[task_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get rotation statistics"""
        return {
            "active_tasks": len(self._states),
            "total_declines": sum(self._global_decline_count.values()),
            "most_declined_profiles": sorted(
                self._global_decline_count.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }

    def cleanup_task(self, task_id: str):
        """Clean up rotation state for a completed task"""
        self._states.pop(task_id, None)


# =================================================================
# DEEP SEARCH — Image-based product matching
# =================================================================


@dataclass
class ImageFingerprint:
    """Perceptual hash of a product image"""

    url: str
    hash_value: str
    product_title: str = ""
    product_sku: str = ""
    store_name: str = ""
    fetched_at: float = field(default_factory=time.time)


class DeepSearch:
    """
    Image-based product matching for detecting re-listed products.

    Valor's Deep Search matches products via image URLs and perceptual
    hashing, catching products that have been renamed or re-listed
    under different SKUs.

    Usage:
        search = DeepSearch()

        # Index a target product's image
        search.add_target("https://cdn.shopify.com/product1.jpg", "Kobe 6 Proto")

        # Check if a detected product matches any target
        match = search.match_product_image("https://cdn.shopify.com/product2.jpg")
        if match:
            print(f"Matched: {match.product_title}")
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.targets: Dict[str, ImageFingerprint] = {}  # hash → fingerprint
        self.similarity_threshold = similarity_threshold
        self._url_cache: Dict[str, str] = {}  # url → hash

    def add_target(
        self,
        image_url: str,
        product_title: str = "",
        product_sku: str = "",
        store_name: str = "",
    ) -> str:
        """Add a target product image to match against.

        Returns the computed hash.
        """
        img_hash = self._compute_url_hash(image_url)

        fingerprint = ImageFingerprint(
            url=image_url,
            hash_value=img_hash,
            product_title=product_title,
            product_sku=product_sku,
            store_name=store_name,
        )

        self.targets[img_hash] = fingerprint
        self._url_cache[image_url] = img_hash

        logger.debug(
            "Deep search target added",
            product=product_title[:30],
            hash=img_hash[:12],
        )

        return img_hash

    def match_product_image(self, image_url: str) -> Optional[ImageFingerprint]:
        """Check if a product image matches any target.

        Uses URL-based hash matching first (fast), then falls back
        to perceptual similarity if available.
        """
        if not self.targets:
            return None

        candidate_hash = self._compute_url_hash(image_url)

        # Exact hash match
        if candidate_hash in self.targets:
            return self.targets[candidate_hash]

        # URL path similarity (catches CDN variants of same image)
        for target in self.targets.values():
            similarity = self._url_similarity(image_url, target.url)
            if similarity >= self.similarity_threshold:
                logger.info(
                    "Deep search match (URL similarity)",
                    candidate_url=image_url[:60],
                    matched=target.product_title[:30],
                    similarity=f"{similarity:.2f}",
                )
                return target

        return None

    def match_product_images(self, image_urls: List[str]) -> Optional[ImageFingerprint]:
        """Check multiple images for a match (e.g. product gallery)"""
        for url in image_urls:
            match = self.match_product_image(url)
            if match:
                return match
        return None

    def _compute_url_hash(self, url: str) -> str:
        """Compute a hash from the significant parts of an image URL.

        Strips CDN prefixes, query params, and size modifiers to
        get to the core image identifier.
        """
        # Normalize: strip protocol, CDN prefix, query params
        normalized = url.split("?")[0]  # Remove query params
        normalized = normalized.split("#")[0]  # Remove fragment

        # Strip common CDN size modifiers
        for pattern in [
            "_small",
            "_medium",
            "_large",
            "_grande",
            "_compact",
            "_1024x1024",
            "_800x",
            "_600x",
            "_400x",
            "_200x",
            "_2048x2048",
            "@2x",
            "@3x",
        ]:
            normalized = normalized.replace(pattern, "")

        # Hash the normalized URL
        return hashlib.md5(normalized.encode()).hexdigest()

    def _url_similarity(self, url1: str, url2: str) -> float:
        """Compute similarity between two image URLs.

        Strips size/format variations and compares the core path.
        Higher = more similar (0.0 to 1.0).
        """
        path1 = self._extract_image_path(url1)
        path2 = self._extract_image_path(url2)

        if path1 == path2:
            return 1.0

        # Check if core filename matches
        file1 = path1.split("/")[-1].split(".")[0] if "/" in path1 else path1
        file2 = path2.split("/")[-1].split(".")[0] if "/" in path2 else path2

        if file1 == file2:
            return 0.95

        # Longest common substring ratio
        common_len = self._lcs_length(path1, path2)
        max_len = max(len(path1), len(path2), 1)

        return common_len / max_len

    @staticmethod
    def _extract_image_path(url: str) -> str:
        """Extract the meaningful path from an image URL"""
        # Remove protocol and domain
        path = url
        if "://" in path:
            path = path.split("://", 1)[1]
            if "/" in path:
                path = path.split("/", 1)[1]

        # Remove query params and fragment
        path = path.split("?")[0].split("#")[0]

        return path

    @staticmethod
    def _lcs_length(s1: str, s2: str) -> int:
        """Compute length of longest common substring"""
        if not s1 or not s2:
            return 0

        m, n = len(s1), len(s2)
        # Use rolling array for memory efficiency
        prev = [0] * (n + 1)
        curr = [0] * (n + 1)
        max_len = 0

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    curr[j] = prev[j - 1] + 1
                    max_len = max(max_len, curr[j])
                else:
                    curr[j] = 0
            prev, curr = curr, [0] * (n + 1)

        return max_len

    def get_targets(self) -> List[Dict[str, str]]:
        """Get all registered targets"""
        return [
            {
                "title": fp.product_title,
                "sku": fp.product_sku,
                "store": fp.store_name,
                "hash": fp.hash_value[:12],
                "url": fp.url[:60],
            }
            for fp in self.targets.values()
        ]

    def remove_target(self, image_url: str) -> bool:
        """Remove a target by its original URL"""
        img_hash = self._url_cache.pop(image_url, None)
        if img_hash:
            self.targets.pop(img_hash, None)
            return True
        return False

    def clear(self):
        """Clear all targets"""
        self.targets.clear()
        self._url_cache.clear()


# Module-level singletons
profile_rotator = ProfileRotator()
deep_search = DeepSearch()
