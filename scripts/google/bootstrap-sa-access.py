#!/usr/bin/env python3
"""One-time bootstrap: grant a service account access to GTM + GA4 + (later)
Search Console via API, bypassing the UIs that reject SA emails as
"not a Google Account".

Why this script exists:
  - GTM and GA's user-management UIs validate that the email looks like a
    "real" Google user account and reject *.iam.gserviceaccount.com addresses.
  - The APIs accept SA emails fine, but the required user-management scopes
    (tagmanager.manage.users, analytics.manage.users) are NOT in gcloud's
    default OAuth client's whitelist.
  - So we bring our own OAuth client, run an InstalledAppFlow once to get a
    refresh token with the broader scopes, and call the APIs ourselves.

This is meant to be a **reusable FFC-wide tool**. The same pattern works for
any FFC site that needs to bootstrap SA access to Google products. See
docs/ffc-google-sa-bootstrap.md.

Usage:

  # First time (or re-auth):
  python bootstrap-sa-access.py \
      --client-secrets ~/Downloads/client_secret_xxx.json \
      --sa-email githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com \
      --gtm-account "The Crooked House" \
      --ga4-measurement-id G-EDCGRNN40D \
      --gtm-role admin --ga4-role editor

  # Re-runs use the cached refresh token at ~/.config/ffc-google/token.json.

Idempotent: if the SA already has the desired role, the script reports
"already granted" and exits cleanly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# These imports are lazy where possible to keep --help fast.
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    sys.exit(
        "Missing dependencies. Run: pip install -r requirements.txt"
    )

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.manage.users",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.readonly",
]

TOKEN_DIR = Path.home() / ".config" / "ffc-google"
TOKEN_PATH = TOKEN_DIR / "token.json"


def get_creds(client_secrets_path: Path) -> Credentials:
    """Load cached credentials or run the OAuth flow."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_path), SCOPES
        )
        # Try a local server first; fall back to manual code paste.
        try:
            creds = flow.run_local_server(port=0, prompt="consent")
        except Exception:
            creds = flow.run_console()
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        print(f"Cached refresh token to {TOKEN_PATH}")
    return creds


# ---------- GTM ----------

GTM_ROLE_MAP = {"admin": "admin", "edit": "user"}


def grant_gtm(creds, sa_email: str, account_name: str, role: str) -> None:
    print(f"\n--- GTM: grant {sa_email} as {role} on '{account_name}' ---")
    svc = build("tagmanager", "v2", credentials=creds, cache_discovery=False)
    accounts = svc.accounts().list().execute().get("account", [])
    account = next((a for a in accounts if a.get("name") == account_name), None)
    if not account and len(accounts) == 1:
        account = accounts[0]
        print(f"  using only available account: {account.get('name')}")
    if not account:
        sys.exit(
            f"No GTM account named {account_name!r}. Found: "
            f"{[a.get('name') for a in accounts]}"
        )

    # Check whether SA is already a user.
    perms = svc.accounts().user_permissions().list(parent=account["path"]).execute()
    existing = next(
        (p for p in perms.get("userPermission", [])
         if p.get("emailAddress", "").lower() == sa_email.lower()),
        None,
    )
    target_perm = GTM_ROLE_MAP[role]
    if existing:
        current = existing.get("accountAccess", {}).get("permission")
        if current == target_perm:
            print(f"  already granted ({current}). Done.")
            return
        print(f"  updating: {current} -> {target_perm}")
        svc.accounts().user_permissions().update(
            path=existing["path"],
            body={
                "emailAddress": existing["emailAddress"],
                "accountAccess": {"permission": target_perm},
                "containerAccess": existing.get("containerAccess", []),
            },
        ).execute()
    else:
        print(f"  inviting as {target_perm}")
        svc.accounts().user_permissions().create(
            parent=account["path"],
            body={
                "emailAddress": sa_email,
                "accountAccess": {"permission": target_perm},
            },
        ).execute()
    print("  done.")


# ---------- GA4 ----------

GA4_ROLE_MAP = {
    "admin": "predefinedRoles/admin",
    "editor": "predefinedRoles/edit",
    "viewer": "predefinedRoles/read",
}


def grant_ga4(creds, sa_email: str, measurement_id: str, role: str) -> None:
    print(f"\n--- GA4: grant {sa_email} as {role} on property w/ measurement {measurement_id} ---")
    from google.analytics.admin import AnalyticsAdminServiceClient
    from google.analytics.admin_v1beta.types import (
        AccessBinding,
        CreateAccessBindingRequest,
    )

    client = AnalyticsAdminServiceClient(credentials=creds)
    property_path = None
    for account_summary in client.list_account_summaries():
        for prop in account_summary.property_summaries:
            try:
                streams = client.list_data_streams(parent=prop.property)
            except Exception:
                continue
            for stream in streams:
                wsd = getattr(stream, "web_stream_data", None)
                if wsd and wsd.measurement_id == measurement_id:
                    property_path = prop.property
                    print(f"  property: {property_path} ({prop.display_name})")
                    break
            if property_path:
                break
        if property_path:
            break
    if not property_path:
        sys.exit(f"No GA4 property has a web stream with measurement_id={measurement_id}")

    target_role = GA4_ROLE_MAP[role]
    bindings = client.list_access_bindings(parent=property_path)
    for b in bindings:
        if (getattr(b, "user", "") or "").lower() == sa_email.lower():
            if target_role in list(b.roles):
                print(f"  already granted ({target_role}). Done.")
                return
            print(f"  updating roles: {list(b.roles)} -> [{target_role}]")
            b.roles[:] = [target_role]
            from google.analytics.admin_v1beta.types import UpdateAccessBindingRequest
            client.update_access_binding(
                request=UpdateAccessBindingRequest(access_binding=b)
            )
            print("  done.")
            return

    print(f"  inviting as {target_role}")
    client.create_access_binding(
        request=CreateAccessBindingRequest(
            parent=property_path,
            access_binding=AccessBinding(user=sa_email, roles=[target_role]),
        )
    )
    print("  done.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--client-secrets", required=True, type=Path,
                        help="Path to OAuth client_secret_*.json downloaded from "
                             "console.cloud.google.com/apis/credentials")
    parser.add_argument("--sa-email", required=True,
                        help="Service account email to grant access to.")
    parser.add_argument("--gtm-account", default=None,
                        help="GTM account name (if multiple). Skip GTM grant if omitted.")
    parser.add_argument("--gtm-role", default="admin", choices=["admin", "edit"],
                        help="GTM role for the SA (default: admin).")
    parser.add_argument("--ga4-measurement-id", default=None,
                        help="GA4 measurement ID (G-XXXXXXXXXX). Skip GA4 grant if omitted.")
    parser.add_argument("--ga4-role", default="editor",
                        choices=["admin", "editor", "viewer"],
                        help="GA4 role for the SA (default: editor).")
    args = parser.parse_args()

    if not args.client_secrets.exists():
        sys.exit(f"client-secrets file not found: {args.client_secrets}")

    print(f"Granting access for SA: {args.sa_email}")
    creds = get_creds(args.client_secrets)

    if args.gtm_account:
        grant_gtm(creds, args.sa_email, args.gtm_account, args.gtm_role)
    else:
        print("\n(Skipping GTM — no --gtm-account specified.)")

    if args.ga4_measurement_id:
        grant_ga4(creds, args.sa_email, args.ga4_measurement_id, args.ga4_role)
    else:
        print("\n(Skipping GA4 — no --ga4-measurement-id specified.)")

    print("\nAll done.")


if __name__ == "__main__":
    sys.exit(main())
