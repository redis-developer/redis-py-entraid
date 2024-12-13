import asyncio
from time import sleep

import pytest
from redis.auth.token import TokenInterface

from entraid.cred_provider import EntraIdCredentialsProvider


class TestEntraIdCredentialsProvider:
    def test_get_credentials(self, credential_provider: EntraIdCredentialsProvider):
        credentials = credential_provider.get_credentials()
        assert len(credentials) == 2

    @pytest.mark.parametrize(
        "credential_provider",
        [
            {
                "cred_provider_kwargs": {"block_for_initial": False},
            },
            {
                "cred_provider_kwargs": {"block_for_initial": True},
            }
        ],
        ids=["Non-blocking", "Blocking"],
        indirect=True,
    )
    @pytest.mark.asyncio
    async def test_get_credentials_async(self, credential_provider: EntraIdCredentialsProvider):
        credentials = await credential_provider.get_credentials_async()
        assert len(credentials) == 2

    @pytest.mark.parametrize(
        "credential_provider",
        [
            {
                "cred_provider_kwargs": {"expiration_refresh_ratio": 0.00001},
            }
        ],
        indirect=True,
    )
    def test_get_credentials_executes_on_next(self, credential_provider: EntraIdCredentialsProvider):
        tokens = []

        def on_next(token: TokenInterface):
            nonlocal tokens
            tokens.append(token)

        credential_provider.on_next(on_next)

        # Run token manager
        credential_provider.get_credentials()
        sleep(0.3)

        assert len(tokens) == 1

    @pytest.mark.parametrize(
        "credential_provider",
        [
            {
                "cred_provider_kwargs": {"expiration_refresh_ratio": 0.00001},
            }
        ],
        indirect=True,
    )
    @pytest.mark.asyncio
    async def test_get_credentials_async_executes_on_next(self, credential_provider: EntraIdCredentialsProvider):
        tokens = []

        def on_next(token: TokenInterface):
            nonlocal tokens
            tokens.append(token)

        credential_provider.on_next(on_next)

        # Run token manager
        await credential_provider.get_credentials_async()
        await asyncio.sleep(0.3)

        assert len(tokens) == 1

    @pytest.mark.parametrize(
        "credential_provider",
        [
            {
                "cred_provider_kwargs": {"expiration_refresh_ratio": 0.00001},
            }
        ],
        indirect=True,
    )
    def test_get_credentials_executes_on_error(self, credential_provider: EntraIdCredentialsProvider):
        errors = []

        def on_next(token: TokenInterface):
            raise Exception("Some exception")

        def on_error(error: Exception):
            nonlocal errors
            errors.append(error)
            raise error

        credential_provider.on_next(on_next)
        credential_provider.on_error(on_error)

        # Run token manager
        credential_provider.get_credentials()
        sleep(0.3)

        assert len(errors) == 1
        assert str(errors[0]) == "Some exception"

    @pytest.mark.parametrize(
        "credential_provider",
        [
            {
                "cred_provider_kwargs": {"expiration_refresh_ratio": 0.00001},
            }
        ],
        indirect=True,
    )
    @pytest.mark.asyncio
    async def test_get_credentials_async_executes_on_error(self, credential_provider: EntraIdCredentialsProvider):
        errors = []

        async def on_next(token: TokenInterface):
            raise Exception("Some exception")

        async def on_error(error: Exception):
            nonlocal errors
            errors.append(error)
            raise error

        credential_provider.on_next(on_next)
        credential_provider.on_error(on_error)

        # Run token manager
        await credential_provider.get_credentials_async()
        await asyncio.sleep(0.3)

        assert len(errors) == 1
        assert str(errors[0]) == "Some exception"