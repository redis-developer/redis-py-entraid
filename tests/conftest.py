import os
from enum import Enum

import pytest
from _pytest.fixtures import SubRequest
from redis import CredentialProvider
from redis.auth.idp import IdentityProviderInterface

from redis_entraid.cred_provider import EntraIdCredentialsProvider, TokenAuthConfig
from redis_entraid.identity_provider import ManagedIdentityType, create_provider_from_managed_identity, \
    create_provider_from_service_principal, EntraIDIdentityProvider, ManagedIdentityIdType


class AuthType(Enum):
    MANAGED_IDENTITY = "managed_identity"
    SERVICE_PRINCIPAL = "service_principal"


def get_identity_provider(request) -> EntraIDIdentityProvider:
    if hasattr(request, "param"):
        kwargs = request.param.get("idp_kwargs", {})
    else:
        kwargs = {}

    auth_type = kwargs.pop("auth_type", AuthType.SERVICE_PRINCIPAL)

    if auth_type == AuthType.MANAGED_IDENTITY:
        return _get_managed_identity_provider(request)

    return _get_service_principal_provider(request)


def _get_managed_identity_provider(request):
    authority = os.getenv("AZURE_AUTHORITY")
    resource = os.getenv("AZURE_RESOURCE")
    id_value = os.getenv("AZURE_USER_ASSIGNED_MANAGED_ID", None)

    if hasattr(request, "param"):
        kwargs = request.param.get("idp_kwargs", {})
    else:
        kwargs = {}

    identity_type = kwargs.pop("identity_type", ManagedIdentityType.SYSTEM_ASSIGNED)
    id_type = kwargs.pop("id_type", ManagedIdentityIdType.OBJECT_ID)

    return create_provider_from_managed_identity(
        identity_type=identity_type,
        resource=resource,
        id_type=id_type,
        id_value=id_value,
        authority=authority,
        **kwargs
    )


def _get_service_principal_provider(request):
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_credential = os.getenv("AZURE_CLIENT_SECRET")
    authority = os.getenv("AZURE_AUTHORITY")
    scopes = os.getenv("AZURE_REDIS_SCOPES", [])

    if hasattr(request, "param"):
        kwargs = request.param.get("idp_kwargs", {})
        token_kwargs = request.param.get("token_kwargs", {})
        timeout = request.param.get("timeout", None)
    else:
        kwargs = {}
        token_kwargs = {}
        timeout = None

    if isinstance(scopes, str):
        scopes = scopes.split(',')

    return create_provider_from_service_principal(
        client_id=client_id,
        client_credential=client_credential,
        scopes=scopes,
        timeout=timeout,
        token_kwargs=token_kwargs,
        authority=authority,
        **kwargs
    )


def get_credential_provider(request) -> CredentialProvider:
    if hasattr(request, "param"):
        cred_provider_kwargs = request.param.get("cred_provider_kwargs", {})
    else:
        cred_provider_kwargs = {}

    idp = get_identity_provider(request)
    initial_delay_in_ms = cred_provider_kwargs.get("initial_delay_in_ms", 0)
    block_for_initial = cred_provider_kwargs.get("block_for_initial", False)
    expiration_refresh_ratio = cred_provider_kwargs.get(
        "expiration_refresh_ratio", TokenAuthConfig.DEFAULT_EXPIRATION_REFRESH_RATIO
    )
    lower_refresh_bound_millis = cred_provider_kwargs.get(
        "lower_refresh_bound_millis", TokenAuthConfig.DEFAULT_LOWER_REFRESH_BOUND_MILLIS
    )
    max_attempts = cred_provider_kwargs.get(
        "max_attempts", TokenAuthConfig.DEFAULT_MAX_ATTEMPTS
    )
    delay_in_ms = cred_provider_kwargs.get(
        "delay_in_ms", TokenAuthConfig.DEFAULT_DELAY_IN_MS
    )

    auth_config = TokenAuthConfig(idp)
    auth_config.expiration_refresh_ratio = expiration_refresh_ratio
    auth_config.lower_refresh_bound_millis = lower_refresh_bound_millis
    auth_config.max_attempts = max_attempts
    auth_config.delay_in_ms = delay_in_ms

    return EntraIdCredentialsProvider(
        config=auth_config,
        initial_delay_in_ms=initial_delay_in_ms,
        block_for_initial=block_for_initial,
    )


@pytest.fixture()
def credential_provider(request) -> CredentialProvider:
    return get_credential_provider(request)


@pytest.fixture()
def identity_provider(request) -> EntraIDIdentityProvider:
    return get_identity_provider(request)