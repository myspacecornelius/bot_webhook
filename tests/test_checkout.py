"""
Unit tests for Phantom Bot checkout modules.
Run with: pytest tests/test_checkout.py
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from phantom.checkout.adyen import AdyenEncryptor
from phantom.checkout.session import CheckoutSession
from phantom.core.task import TaskManager, TaskConfig, TaskStatus, TaskResult
from phantom.core.cookies import CookieStore


# ----------------------------------------------------------------------
# Adyen Encryption Tests
# ----------------------------------------------------------------------


@pytest.fixture
def adyen_encryptor():
    # Test key: exponent|modulus (randomly generated for testing)
    public_key = (
        "10001|"
        "C39226507A94D4D83072877B90807E91D3DA405D6C10777B8760B883907796D3"
        "6523927623321580228372605331393685006456722363065600644723020666"
        "0267269007421272671047101037666275811776263592186950275852504358"
        "0229871638661706680453303728646969562916668729580662283084967389"
    )
    return AdyenEncryptor(public_key)


def test_adyen_encryption_format(adyen_encryptor):
    """Verify Adyen CSE encryption format."""
    encrypted = adyen_encryptor.encrypt_card(
        number="4111111111111111",
        expiry_month="12",
        expiry_year="2030",
        cvv="123",
        holder_name="John Doe",
    )

    # Format: adyenjs_0_1_25${rsa_encrypted_aes_key}${aes_encrypted_payload}
    parts = encrypted.split("$")
    assert len(parts) == 3
    assert parts[0] == "adyenjs_0_1_25"
    assert len(parts[1]) > 0  # RSA key
    assert len(parts[2]) > 0  # AES payload


def test_adyen_field_encryption(adyen_encryptor):
    """Verify single field encryption."""
    encrypted = adyen_encryptor.encrypt_field("cvc", "123")
    assert encrypted.startswith("adyenjs_0_1_25$")
    assert len(encrypted.split("$")) == 3


# ----------------------------------------------------------------------
# Task Manager Tests
# ----------------------------------------------------------------------


@pytest.fixture
def task_manager():
    return TaskManager(max_concurrent=5)


@pytest.mark.asyncio
async def test_task_retry_logic(task_manager):
    """Verify tasks retry on error up to max_retries."""
    mock_handler = AsyncMock()
    # Fail twice, then succeed
    mock_handler.side_effect = [
        TaskResult(success=False, error_message="Network Error"),
        TaskResult(success=False, error_message="Timeout"),
        TaskResult(success=True, order_number="ORDER-123"),
    ]

    task_manager.set_checkout_handler(mock_handler)

    config = TaskConfig(
        site_url="https://example.com",
        retry_on_error=True,
        max_retries=3,
        retry_delay=10,  # fast retry for test
    )
    task = task_manager.create_task(config)

    # Patch sleep to speed up test
    with patch("asyncio.sleep", new_callable=AsyncMock):
        await task_manager._run_task(task)

    assert task.status == TaskStatus.SUCCESS
    assert task.result.order_number == "ORDER-123"
    assert mock_handler.call_count == 3
    assert task._retry_count == 2


@pytest.mark.asyncio
async def test_task_rate_limiting(task_manager):
    """Verify per-site rate limiting delays requests."""
    mock_handler = AsyncMock(return_value=TaskResult(success=True))
    task_manager.set_checkout_handler(mock_handler)

    # Configure 0.1s delay
    task_manager._min_site_delay = 0.1

    config = TaskConfig(site_url="https://example.com")
    task1 = task_manager.create_task(config)
    task2 = task_manager.create_task(config)

    start_time = asyncio.get_event_loop().time()

    # Run two tasks concurrently
    await asyncio.gather(task_manager._run_task(task1), task_manager._run_task(task2))

    end_time = asyncio.get_event_loop().time()

    # First runs immediately, second waits 0.1s
    # Total time should be at least 0.1s
    assert (end_time - start_time) >= 0.1


# ----------------------------------------------------------------------
# Cookie Store Tests
# ----------------------------------------------------------------------


def test_cookie_store_persistence():
    store = CookieStore()

    # Save cookies
    store.save("task-1", "example.com", {"session_id": "abc"})

    # Load cookies
    cookies = store.load("task-1", "example.com")
    assert cookies == {"session_id": "abc"}

    # Merge new cookies
    store.save("task-1", "example.com", {"cart": "xyz"})
    cookies = store.load("task-1", "example.com")
    assert cookies == {"session_id": "abc", "cart": "xyz"}

    # Clear cookies
    store.clear("task-1")
    assert store.load("task-1") == {}


# ----------------------------------------------------------------------
# Session Factory Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_creation():
    factory = CheckoutSession()

    # Test with mock curl-cffi
    with (
        patch("phantom.checkout.session.HAS_CURL_CFFI", True),
        patch("phantom.checkout.session.CurlAsyncSession") as MockSession,
    ):
        await factory.create(extra_headers={"Foo": "Bar"})

        assert MockSession.called
        call_kwargs = MockSession.call_args[1]
        assert "impersonate" in call_kwargs
        assert call_kwargs["headers"]["Foo"] == "Bar"


@pytest.mark.asyncio
async def test_session_fallback():
    factory = CheckoutSession()

    # Test fallback to httpx when curl-cffi missing
    with patch("phantom.checkout.session.HAS_CURL_CFFI", False):
        session = await factory.create()
        assert session.__class__.__name__ == "AsyncClient"  # httpx.AsyncClient
