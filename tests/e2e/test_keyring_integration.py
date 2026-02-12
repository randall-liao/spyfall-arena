import keyring
import pytest

from config.api_key_manager import ApiKeyManager


@pytest.mark.e2e
def test_api_key_manager_reads_from_keyring():
    """
    Verifies that ApiKeyManager can retrieve secrets from the system keyring.
    This test requires a functioning keyring backend (like gnome-keyring or SecretService).
    """
    service_name = "spyfall-arena"
    account_name = "openrouter_api_key"
    test_key = "e2e-test-key-12345"

    # valid backends check
    try:
        current_backend = keyring.get_keyring()
        print(f"Current keyring backend: {current_backend}")
    except Exception as e:
        pytest.fail(f"Failed to get keyring backend: {e}")

    try:
        # Pre-populate the keyring
        keyring.set_password(service_name, account_name, test_key)

        # Initialize manager - normally a singleton, so we need to be careful
        # if other tests ran before.
        manager = ApiKeyManager()
        # Force reload to ignore previously cached keys if any
        manager._key_loaded = False
        manager._api_key = None

        retrieved_key = manager.get_api_key()

        assert retrieved_key == test_key, f"Expected {test_key}, got {retrieved_key}"

    finally:
        # Cleanup
        try:
            keyring.delete_password(service_name, account_name)
        except keyring.errors.PasswordDeleteError:
            pass
