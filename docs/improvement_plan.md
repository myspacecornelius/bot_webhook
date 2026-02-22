# Phantom Bot — Debug & Improvement Plan

## Bugs Fixed (This Session)

### 1. `auto_switch.py` — SwitchReason enum lookup always fell back to MANUAL

**Root cause:** `SwitchReason.__members__` keys are uppercase (`"QUEUE_DETECTED"`) but signal names are lowercase (`"queue_detected"`). Every switch reason was logged as `MANUAL`.  
**Fix:** Replaced the broken `SwitchReason(best_reason) if best_reason in __members__` pattern with a direct `SIGNAL_TO_REASON` dict mapping signal names to enum values.

### 2. `auto_switch.py` — `force_switch` could downgrade a higher-priority mode

**Root cause:** `force_switch = signal in ("preload_available", "queue_detected", "checkpoint_detected")` allowed `queue_detected` (→ NORMAL, priority 2) to override an active PRELOAD session (priority 4), defeating the purpose of preloading.  
**Fix:** Separated signals into two independent tracks — _safety downgrades_ (queue, checkpoint, rate*limit, captcha) always win and pick the most conservative mode; \_upgrade signals* (preload_available, high_demand, etc.) only win if they are strictly higher priority than the current mode.

### 3. `auto_task.py` — `Task()` default sentinel created garbage objects

**Root cause:** `self.task_manager.tasks.get(tid, Task())` instantiated a new `Task` dataclass (with a fresh UUID) for every missing task ID in the success check loop.  
**Fix:** Replaced with walrus-operator pattern `(t := tasks.get(tid)) is not None and t.status == SUCCESS`.

### 4. `auto_task.py` — `delete_after_stop` read from live config, not spawn-time config

**Root cause:** `_stop_after_timeout` read `self.config.delete_after_stop` at timeout time. If `configure()` was called between spawn and timeout, the wrong value was used.  
**Fix:** Added `delete_after_stop: bool` field to `SpawnRecord`, captured at spawn time. Timeout now reads `record.delete_after_stop`.

### 5. `auto_task.py` — `max_spawns_per_product` matched on `product.sku == None`

**Root cause:** The spawn count check compared `r.product_sku == product.sku`. When SKU is `None`, this matched all records with a missing SKU across different products and stores.  
**Fix:** Added `product_key: str` field to `SpawnRecord` (same dedup key as `_product_spawned`). Spawn count check now uses `r.product_key == product_key`.

### 6. `preload.py` — `_submit_shipping` returned `True` with no shipping rate

**Root cause:** If the regex found no `data-shipping-method` attribute, the POST was silently skipped and the function returned `True`, allowing checkout to proceed without a shipping method.  
**Fix:** Returns `False` (with a warning log) when no rate is found. Also now checks the POST response status code.

### 7. `preload.py` — `_refresh_checkout` ignored HTTP error status codes

**Root cause:** Unlike `_create_checkout_session`, `_refresh_checkout` did not check `response.status_code`. A 429 or 503 would be treated as a successful refresh.  
**Fix:** Added `if response.status_code not in (200, 302): return None` with a warning log.

### 8. `preload.py` — HTTP session not nulled after `aclose()` in `swap_and_checkout`

**Root cause:** `swap_and_checkout` closed `preloaded.http_session` in the `finally` block but left the reference intact. If the keepalive task wasn't fully cancelled, it could attempt to use the closed session.  
**Fix:** Set `preloaded.http_session = None` after `aclose()`.

### 9. `preload.py` — Session IDs truncated to 8 characters

**Root cause:** `session_id = str(uuid.uuid4())[:8]` — only ~4 billion possible values. With rapid session creation (e.g. 19 quick tasks), collision probability is non-trivial.  
**Fix:** Use full UUID. Display is truncated to `[:8]` only in log messages and `get_active_sessions()`.

### 10. `nike.py` — `NikeCheckoutMode` was not an Enum

**Root cause:** `class NikeCheckoutMode(str)` is a plain class with string class attributes, not an enum. It cannot be iterated, used in `isinstance` checks, or matched as an enum member.  
**Fix:** Changed to `class NikeCheckoutMode(str, Enum)` and added missing `from enum import Enum` import.

### 11. `nike.py` — `session` variable referenced in `finally` before assignment

**Root cause:** `if "session" in locals()` is fragile — it depends on CPython's `locals()` behavior and is not idiomatic.  
**Fix:** Initialize `session = None` before the try block; check `if session is not None` in finally.

### 12. `engine.py` — Auto-switch evaluated pre-checkout with stale signals

**Root cause:** `_gather_checkout_signals` was called at the start of `_handle_checkout`, before any checkout attempt. At that point `task.status` is always `STARTING`, so `queue_detected`, `captcha_required`, and `declined` were always `False`. Auto-switch never triggered.  
**Fix:** Moved auto-switch evaluation to post-failure path. Renamed to `_gather_result_signals(task, result)` — now reads both `task.status` and `result.error_message` to detect queue, captcha, rate-limit, checkpoint, and timeout conditions from the actual failure.

### 13. `store_database.py` — ~35 corrupted store URLs

**Root cause:** Bulk copy-paste corruption inserted `fr` mid-word in URLs and names (e.g. `drfrewhouse.com`, `pfratta.nl`, `hifrshit.com`, `tfrelfar.net`). All affected stores would fail with DNS errors.  
**Fix:** Corrected all corrupted URLs and the `"Amie Leon Dore"` name typo (`→ "Aime Leon Dore"`). Also normalized Taylor Swift store subdomains to use hyphens (`storeCA.` → `store-ca.`).

---

## Remaining Issues (Not Yet Fixed)

### HIGH — Nike payment tokenization is a stub

`_build_payment_payload` computes a local SHA-256 hash of the card number and calls it a `payment_token`. Nike's actual API requires a real payment instrument token from Braintree/Adyen. This will always result in payment failure for Nike checkouts.  
**Required:** Integrate with Nike's actual payment tokenization endpoint or a supported payment gateway SDK.

### HIGH — `preload.py` imports `ShopifyCheckout` and `CheckoutSession` at call time

The circular import workaround (`from .shopify import ShopifyCheckout, CheckoutSession as ShopifyCS` inside `swap_and_checkout`) is fragile. If `shopify.py` is refactored, this silent runtime import will break with no static analysis warning.  
**Recommended:** Restructure to pass a `ShopifyCheckout` instance into `PreloadEngine` at construction time (dependency injection), eliminating the circular import.

### MEDIUM — `AutoTaskSpawner._preload_engine` is unused

`self._preload_engine = preload_engine` is set in `__init__` but never used. The `_resolve_mode` method assigns `TaskMode.PRELOAD` to the first task without checking whether an actual preload session exists for the target site.  
**Recommended:** Before assigning `TaskMode.PRELOAD`, check `self._preload_engine.sessions` for an active session matching `store.url`. Fall back to `TaskMode.FAST` if none exists.

### MEDIUM — `ProfileRotator.get_profile` ignores `max_rotations` on initial call

When `get_profile` is called for the first time, it creates a `RotationState` with `max_rotations=5` (default), ignoring the `max_rotations` parameter passed to the call. Subsequent calls use the state's stored value correctly.  
**Fix:** Pass `max_rotations` to `_get_or_create_state` on the initial call path.

### MEDIUM — `DeepSearch._compute_url_hash` uses MD5

MD5 is not cryptographically secure. While this is only used for product image deduplication (not security), MD5 has known collision issues that could cause false positive matches between different product images.  
**Recommended:** Switch to SHA-256 or use a purpose-built perceptual hash (e.g. `imagehash` library) for actual image content matching.

### MEDIUM — `TaskManager._site_locks` dict grows unbounded

`_site_locks` and `_site_last_request` accumulate one entry per unique domain forever. With 350+ stores monitored continuously, this is a slow memory leak.  
**Recommended:** Use an LRU cache or periodically evict entries older than a threshold.

### LOW — `store_database.py` has duplicate Supreme entries with different regions

`Supreme US`, `Supreme UK`, and `Supreme Asia` all point to `https://www.supremenewyork.com`. The monitor will hit the same URL three times per poll cycle.  
**Recommended:** Either use region-specific Supreme URLs or add a dedup layer in `MultiStoreMonitor`.

### LOW — `StoreDatabase.load_builtin` uses `store.name.lower().replace(" ", "_")` as key

Store names like `"Kith"` and `"Kith CA"` produce keys `"kith"` and `"kith_ca"` — fine. But names with special characters (e.g. `"Every Now & Then"`) produce `"every_now_&_then"`, which is an awkward dict key. If two stores normalize to the same key, the second silently overwrites the first.  
**Recommended:** Use the store URL as the primary key, or use a slug function that strips special characters.

---

## Performance Improvements

### 1. Parallelize preload session creation

`create_preloaded_session` is fully sequential. When spawning 4+ tasks for a drop, sessions should be created concurrently:

```python
sessions = await asyncio.gather(*[
    engine.create_preloaded_session(site_url=store.url, proxy=proxy)
    for proxy in proxy_pool[:task_count]
])
```

### 2. Cache `products.json` responses in `_find_precart_item`

Every preload session creation fetches `/products.json?limit=250` independently. For the same store, this is the same 250-product payload. Cache it per-domain with a short TTL (60s):

```python
_precart_cache: Dict[str, Tuple[float, List]] = {}  # url → (timestamp, products)
```

### 3. Batch `TaskManager.start_task` calls in `AutoTaskSpawner`

`_spawn_tasks` calls `await self.task_manager.start_task(task.id)` in a loop. Each call creates an `asyncio.Task` but the loop is sequential. Use `asyncio.gather`:

```python
await asyncio.gather(*[self.task_manager.start_task(tid) for tid in record.task_ids])
```

### 4. `DeepSearch._lcs_length` is O(m×n) — avoid on hot paths

The LCS algorithm runs on every product image URL comparison. For 350 stores × N products, this is expensive. The URL similarity check should short-circuit earlier:

- If domains differ → return 0.0 immediately
- If path lengths differ by >50% → return 0.0 immediately
- Only run LCS on paths that share the same domain and similar length

### 5. `StoreDatabase.get_all()` calls `load_builtin()` on every access if not loaded

The `if not self._loaded: self.load_builtin()` guard is correct but `get_all()` is called by every filter method. The list is rebuilt from `self.stores.values()` on every call. Cache the list:

```python
@functools.lru_cache(maxsize=1)
def get_all(self) -> List[ShopifyStore]: ...
```

(Invalidate on `load_builtin`.)

### 6. `engine.get_status()` iterates all tasks on every call

`task_manager.get_stats()` does 5 separate passes over `self.tasks.values()`. For 100+ tasks polled via WebSocket, this is wasteful. Maintain running counters incremented/decremented on status transitions instead of scanning on read.

---

## Architecture Recommendations

### Dependency injection for checkout modules

`PreloadEngine` and `AutoTaskSpawner` both import module-level singletons (`preload_engine`, `auto_switch`) at import time. This makes unit testing impossible without monkey-patching. Pass dependencies through constructors.

### Typed signal protocol for auto-switch

The `signals: Dict[str, bool]` interface is stringly-typed. Define a `CheckoutSignals` dataclass or `TypedDict` so callers get IDE completion and type checking:

```python
class CheckoutSignals(TypedDict, total=False):
    queue_detected: bool
    captcha_required: bool
    rate_limited: bool
    ...
```

### Persist spawn history across restarts

`AutoTaskSpawner._spawn_history` and `_product_spawned` are in-memory only. After a restart, cooldowns and max-spawn limits reset, potentially causing duplicate task spawns for the same product. Persist to the existing SQLite database.

### Add integration tests for the monitor → task pipeline

The `on_product_detected → _spawn_tasks → start_task` pipeline has no tests. Given the number of bugs found in this session (None-SKU dedup, config capture, sentinel object), this path needs coverage with a mock `TaskManager` and `DetectedProduct`.
