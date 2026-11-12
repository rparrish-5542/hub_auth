"""mint_app_token, its Django command, and the python -m entry point."""

import io
import time

import jwt
import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from hub_auth_client import AppTokenValidator, mint_app_token
from hub_auth_client.mint import main as mint_main
from hub_auth_client.validators.app import AppTokenValidator as PackagedAppTokenValidator

SECRET = "teams-connector-own-secret-at-least-32-bytes"


def test_minted_token_passes_app_token_validator():
    token = mint_app_token(SECRET, sub="checkin_service", aud="teams_connector")

    ok, claims, error = AppTokenValidator(secret=SECRET, audience="teams_connector").validate_token(token)

    assert ok, error
    assert claims["sub"] == "checkin_service"
    assert claims["iss"] == "teams_connector"
    assert claims["jti"]


def test_minted_token_passes_the_validators_package_copy_too():
    token = mint_app_token(SECRET, sub="checkin_service", aud="teams_connector")
    ok, _claims, error = PackagedAppTokenValidator(secret=SECRET, audience="teams_connector").validate_token(token)
    assert ok, error


def test_lifetime_and_issuer():
    before = int(time.time())
    token = mint_app_token(SECRET, sub="a", aud="b", expires_in_seconds=600, issuer="custom-iss")
    claims = jwt.decode(token, SECRET, algorithms=["HS256"], audience="b")
    assert before + 600 <= claims["exp"] <= int(time.time()) + 600
    assert claims["iss"] == "custom-iss"
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_tokens_are_unique():
    assert mint_app_token(SECRET, sub="a", aud="b") != mint_app_token(SECRET, sub="a", aud="b")


def test_other_service_secret_or_audience_is_rejected():
    token = mint_app_token(SECRET, sub="checkin_service", aud="teams_connector")
    other_secret = "employee-manage-own-secret-at-least-32-bytes"
    assert not AppTokenValidator(secret=other_secret, audience="teams_connector").validate_token(token)[0]
    assert not AppTokenValidator(secret=SECRET, audience="employee_manage").validate_token(token)[0]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"secret": ""},
        {"secret": "too-short"},
        {"sub": ""},
        {"aud": ""},
        {"expires_in_seconds": 0},
        {"expires_in_seconds": -5},
    ],
)
def test_bad_arguments_raise(kwargs):
    args = {"secret": SECRET, "sub": "a", "aud": "b", **kwargs}
    secret = args.pop("secret")
    with pytest.raises(ValueError):
        mint_app_token(secret, **args)


@override_settings(APP_JWT_SECRET=SECRET, APP_JWT_AUDIENCE="teams_connector", APP_JWT_ISSUER=None)
def test_management_command_uses_service_settings():
    out = io.StringIO()
    call_command("mint_app_token", "checkin_service", "--days", "30", stdout=out)

    token = out.getvalue().strip()
    ok, claims, error = AppTokenValidator(secret=SECRET, audience="teams_connector").validate_token(token)
    assert ok, error
    assert claims["sub"] == "checkin_service"
    assert claims["exp"] - claims["iat"] == 30 * 86400


@override_settings(APP_JWT_SECRET=SECRET, APP_JWT_AUDIENCE="teams_connector", APP_JWT_ISSUER="teams-iss")
def test_management_command_matches_configured_issuer():
    out = io.StringIO()
    call_command("mint_app_token", "checkin_service", stdout=out)
    validator = AppTokenValidator(secret=SECRET, audience="teams_connector", issuer="teams-iss")
    assert validator.validate_token(out.getvalue().strip())[0]


@override_settings(APP_JWT_SECRET="", APP_JWT_AUDIENCE="teams_connector")
def test_management_command_needs_secret():
    with pytest.raises(CommandError):
        call_command("mint_app_token", "checkin_service")


@override_settings(APP_JWT_SECRET=SECRET, APP_JWT_AUDIENCE=None)
def test_management_command_needs_audience():
    with pytest.raises(CommandError):
        call_command("mint_app_token", "checkin_service")


def test_cli_reads_secret_from_env(monkeypatch, capsys):
    monkeypatch.setenv("APP_JWT_SECRET", SECRET)

    assert mint_main(["bouma_checkin", "--aud", "checkin_service", "--days", "7"]) == 0

    token = capsys.readouterr().out.strip()
    ok, claims, error = AppTokenValidator(secret=SECRET, audience="checkin_service").validate_token(token)
    assert ok, error
    assert claims["sub"] == "bouma_checkin"


def test_cli_without_secret_exits(monkeypatch):
    monkeypatch.delenv("APP_JWT_SECRET", raising=False)
    with pytest.raises(SystemExit):
        mint_main(["bouma_checkin", "--aud", "checkin_service"])
