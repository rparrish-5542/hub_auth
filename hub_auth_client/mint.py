"""
Command-line minting for services without Django (e.g. FastAPI).

    APP_JWT_SECRET=... python -m hub_auth_client.mint checkin_service --aud teams_connector --days 365

Reads the minting service's own secret from the environment (APP_JWT_SECRET by
default, or --secret-env NAME) and prints only the token, so it can be piped.
"""

import argparse
import os
import sys
from typing import List, Optional

from hub_auth_client.minting import mint_app_token


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m hub_auth_client.mint",
        description="Mint an HS256 app token for a calling service.",
    )
    parser.add_argument("sub", help="The calling service's name (token sub)")
    parser.add_argument("--aud", required=True, help="This service's audience (token aud)")
    parser.add_argument("--days", type=int, default=365, help="Lifetime in days (default 365)")
    parser.add_argument("--issuer", default=None, help="iss claim (default: same as --aud)")
    parser.add_argument(
        "--secret-env", default="APP_JWT_SECRET", help="Environment variable holding this service's secret"
    )
    args = parser.parse_args(argv)

    secret = os.environ.get(args.secret_env, "").strip()
    if not secret:
        parser.error(f"{args.secret_env} is not set")
    try:
        token = mint_app_token(
            secret, sub=args.sub, aud=args.aud, expires_in_seconds=args.days * 86400, issuer=args.issuer
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
