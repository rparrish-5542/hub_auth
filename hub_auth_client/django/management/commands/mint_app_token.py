"""
Mint an HS256 app token for a service that calls this one.

Uses this service's own settings, so the token matches what its
AppTokenValidator / MSALAuthentication app-token path checks:
APP_JWT_SECRET signs, APP_JWT_AUDIENCE is the default aud, APP_JWT_ISSUER (if
set) is the iss.

Usage:
    python manage.py mint_app_token checkin_service
    python manage.py mint_app_token checkin_service --aud teams_connector --days 365

Prints only the token. Give it to the calling service (e.g. its .env); never
give out the secret.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from hub_auth_client.minting import mint_app_token


class Command(BaseCommand):
    help = "Mint an HS256 app token (signed with APP_JWT_SECRET) for a calling service."

    def add_arguments(self, parser):
        parser.add_argument("sub", help="The calling service's name (token sub)")
        parser.add_argument("--aud", default=None, help="Token aud (default: settings.APP_JWT_AUDIENCE)")
        parser.add_argument("--days", type=int, default=365, help="Lifetime in days (default 365)")

    def handle(self, *args, **options):
        secret = getattr(settings, "APP_JWT_SECRET", "") or ""
        aud = options["aud"] or getattr(settings, "APP_JWT_AUDIENCE", None)
        if not secret:
            raise CommandError("settings.APP_JWT_SECRET is not set")
        if not aud:
            raise CommandError("Pass --aud or set settings.APP_JWT_AUDIENCE")
        try:
            token = mint_app_token(
                secret,
                sub=options["sub"],
                aud=aud,
                expires_in_seconds=options["days"] * 86400,
                issuer=getattr(settings, "APP_JWT_ISSUER", None),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(token)
