import pytest

from invoiceflow.config import ConfigError, Settings


def test_missing_password_is_a_clear_error() -> None:
    settings = Settings(_env_file=None, postgres_password=None)
    with pytest.raises(ConfigError, match="POSTGRES_PASSWORD"):
        settings.postgres_conninfo()


def test_conninfo_includes_the_settings() -> None:
    settings = Settings(
        _env_file=None,
        postgres_host="db.local",
        postgres_port=6543,
        postgres_password="not-a-real-password",  # noqa: S106 - test value
    )
    info = settings.postgres_conninfo()
    assert "host=db.local" in info
    assert "port=6543" in info
