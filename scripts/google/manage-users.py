#!/usr/bin/env python3
"""Reconcile GTM + GA4 user access against the roster in users.py.

  * Reads users.py for the desired state
  * Lists existing users on the GTM account + GA4 property
  * For each entry in the roster:
      - If user not present: invite them
      - If user present but role differs: update the role
      - If user present with right role: skip
  * Optionally (--prune) removes users not in the roster

Idempotent. Re-runs safely. Pass --dry-run to log without applying.

Roles map to API enums:
  GTM 'admin' -> ACCOUNT_PERMISSION.ACCOUNT.permission = 'admin'
  GTM 'edit'  -> ... = 'user'
  GA4 'admin' -> Administrator role
  GA4 'editor'-> Editor role
  GA4 'viewer'-> Viewer role
"""

from __future__ import annotations

import argparse
import sys

from google.analytics.admin_v1alpha.types import (
    AccessBinding,
    CreateAccessBindingRequest,
    UpdateAccessBindingRequest,
)
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from googleapiclient.discovery import build

from config import ACCOUNT_NAME, GA4_MEASUREMENT_ID, GA4_PROPERTY_ID, credentials
from users import USERS


# ----- GTM -----

GTM_ROLE_MAP = {
    "admin": "admin",
    "edit": "user",
}


def gtm_reconcile(svc, dry_run: bool, prune: bool) -> None:
    print("\n--- GTM ---")
    accounts = svc.accounts().list().execute().get("account", [])
    account = next((a for a in accounts if a.get("name") == ACCOUNT_NAME), None)
    if not account:
        if len(accounts) == 1:
            account = accounts[0]
        else:
            print("  Could not find a GTM account. Service account not yet granted?")
            return
    print(f"  Account: {account['name']} ({account['path']})")

    existing = svc.accounts().user_permissions().list(parent=account["path"]).execute()
    existing_perms = existing.get("userPermission", [])
    existing_by_email = {p["emailAddress"].lower(): p for p in existing_perms}

    desired_emails = set()
    for user in USERS:
        if not user.get("gtm"):
            continue
        email = user["email"].lower()
        desired_emails.add(email)
        target_role = GTM_ROLE_MAP[user["gtm"]]

        if email in existing_by_email:
            current = existing_by_email[email]
            cur_role = current.get("accountAccess", {}).get("permission")
            if cur_role == target_role:
                print(f"  {email}: already {cur_role}, skipping")
                continue
            if dry_run:
                print(f"  {email}: WOULD UPDATE {cur_role} -> {target_role}")
                continue
            svc.accounts().user_permissions().update(
                path=current["path"],
                body={
                    "emailAddress": current["emailAddress"],
                    "accountAccess": {"permission": target_role},
                    "containerAccess": current.get("containerAccess", []),
                },
            ).execute()
            print(f"  {email}: updated {cur_role} -> {target_role}")
        else:
            if dry_run:
                print(f"  {email}: WOULD INVITE as {target_role}")
                continue
            svc.accounts().user_permissions().create(
                parent=account["path"],
                body={
                    "emailAddress": user["email"],
                    "accountAccess": {"permission": target_role},
                },
            ).execute()
            print(f"  {email}: invited as {target_role}")

    if prune:
        for email, perm in existing_by_email.items():
            if email in desired_emails:
                continue
            # Don't prune the service account itself
            if email.endswith(".iam.gserviceaccount.com"):
                continue
            if dry_run:
                print(f"  {email}: WOULD REMOVE (not in roster)")
                continue
            svc.accounts().user_permissions().delete(path=perm["path"]).execute()
            print(f"  {email}: removed")


# ----- GA4 -----

GA4_ROLE_MAP = {
    "admin": "predefinedRoles/admin",
    "editor": "predefinedRoles/editor",
    "viewer": "predefinedRoles/viewer",
}


def ga4_property_path(client) -> str | None:
    if GA4_PROPERTY_ID:
        return f"properties/{GA4_PROPERTY_ID}"
    for account_summary in client.list_account_summaries():
        for prop in account_summary.property_summaries:
            try:
                streams = client.list_data_streams(parent=prop.property)
            except Exception:
                continue
            for stream in streams:
                wsd = getattr(stream, "web_stream_data", None)
                if wsd and wsd.measurement_id == GA4_MEASUREMENT_ID:
                    return prop.property
    return None


def ga4_reconcile(client, dry_run: bool, prune: bool) -> None:
    print("\n--- GA4 ---")
    property_path = ga4_property_path(client)
    if not property_path:
        print("  No GA4 property accessible to the service account yet.")
        return
    print(f"  Property: {property_path}")

    bindings = list(client.list_access_bindings(parent=property_path))
    bindings_by_user = {}
    for b in bindings:
        user = (getattr(b, "user", None) or "").lower()
        if user:
            bindings_by_user[user] = b

    desired_emails = set()
    for user in USERS:
        if not user.get("ga4"):
            continue
        email = user["email"].lower()
        desired_emails.add(email)
        target_role = GA4_ROLE_MAP[user["ga4"]]

        if email in bindings_by_user:
            existing = bindings_by_user[email]
            if target_role in list(existing.roles):
                print(f"  {email}: already has {target_role}, skipping")
                continue
            if dry_run:
                print(f"  {email}: WOULD UPDATE roles to [{target_role}]")
                continue
            existing.roles[:] = [target_role]
            client.update_access_binding(
                request=UpdateAccessBindingRequest(access_binding=existing)
            )
            print(f"  {email}: updated to {target_role}")
        else:
            if dry_run:
                print(f"  {email}: WOULD INVITE as {target_role}")
                continue
            client.create_access_binding(
                request=CreateAccessBindingRequest(
                    parent=property_path,
                    access_binding=AccessBinding(user=user["email"], roles=[target_role]),
                )
            )
            print(f"  {email}: invited as {target_role}")

    if prune:
        for email, binding in bindings_by_user.items():
            if email in desired_emails:
                continue
            if email.endswith(".iam.gserviceaccount.com"):
                continue
            if dry_run:
                print(f"  {email}: WOULD REMOVE (not in roster)")
                continue
            client.delete_access_binding(name=binding.name)
            print(f"  {email}: removed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Log planned changes without applying them.")
    parser.add_argument("--prune", action="store_true",
                        help="Remove users not in the roster (otherwise additive only).")
    args = parser.parse_args()

    print(f"=== manage-users (dry-run={args.dry_run}, prune={args.prune}) ===")
    print(f"Roster: {len(USERS)} user(s)")
    for u in USERS:
        print(f"  - {u['email']}: GTM={u.get('gtm') or '-'}, GA4={u.get('ga4') or '-'}")

    creds = credentials()
    gtm_svc = build("tagmanager", "v2", credentials=creds, cache_discovery=False)
    gtm_reconcile(gtm_svc, args.dry_run, args.prune)

    ga4_client = AnalyticsAdminServiceClient(credentials=creds)
    ga4_reconcile(ga4_client, args.dry_run, args.prune)

    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
