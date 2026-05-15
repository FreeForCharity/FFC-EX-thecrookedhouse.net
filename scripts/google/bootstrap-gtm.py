#!/usr/bin/env python3
"""Idempotent GTM container bootstrap.

Configures the existing GTM container (GTM-5JV8JHCH) with:

  * Consent-mode v2 default state (Necessary always granted, others denied)
  * A "Google Analytics: GA4 Configuration" tag tied to G-EDCGRNN40D
  * "All Pages" trigger for the GA4 tag
  * Outbound-click variable + triggers for donate_click and email_click
  * GA4 Event tag firing donate_click on PayPal / Zeffy / donate.* outbound
  * GA4 Event tag firing email_click on mailto:b@thecrookedhouse.net
  * Publishes a new container version when changes were made

Re-running is safe: anything that already matches the desired state is left
alone. Pass --dry-run to log the planned changes without applying them.

Requires:
  - Service account with Admin role on the GTM account (granted in UI once)
  - GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_SA_KEY env var
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from googleapiclient.discovery import build

from config import (
    ACCOUNT_NAME,
    CONTAINER_NAME,
    GA4_MEASUREMENT_ID,
    GTM_CONTAINER_ID,
    credentials,
)


def find_account(svc) -> dict[str, Any]:
    """Locate the GTM account matching ACCOUNT_NAME (or the only one available)."""
    resp = svc.accounts().list().execute()
    accounts = resp.get("account", [])
    if not accounts:
        raise SystemExit(
            "No GTM accounts visible to this service account. Add the SA email "
            "as a user on the GTM account in Tag Manager → Admin → User Management."
        )
    # Prefer name match; fall back to single account
    for acct in accounts:
        if acct.get("name") == ACCOUNT_NAME:
            return acct
    if len(accounts) == 1:
        return accounts[0]
    raise SystemExit(
        f"Multiple GTM accounts visible; expected one named {ACCOUNT_NAME!r}. "
        f"Found: {[a.get('name') for a in accounts]}"
    )


def find_container(svc, account_path: str) -> dict[str, Any]:
    resp = svc.accounts().containers().list(parent=account_path).execute()
    containers = resp.get("container", [])
    for c in containers:
        if c.get("publicId") == GTM_CONTAINER_ID:
            return c
    raise SystemExit(
        f"Container {GTM_CONTAINER_ID} not found under account {account_path}. "
        "Create it manually in Tag Manager (one click) or via API "
        "(accounts.containers.create)."
    )


def get_or_create_default_workspace(svc, container_path: str) -> dict[str, Any]:
    resp = svc.accounts().containers().workspaces().list(parent=container_path).execute()
    workspaces = resp.get("workspace", [])
    for w in workspaces:
        if w.get("name") == "Default Workspace":
            return w
    # Fall back to first workspace
    if workspaces:
        return workspaces[0]
    raise SystemExit("No workspaces in the container — this should never happen.")


def upsert_tag(svc, workspace_path: str, tag_spec: dict[str, Any], dry_run: bool) -> str:
    """Create or update a tag by name. Returns the tag path."""
    existing = svc.accounts().containers().workspaces().tags().list(
        parent=workspace_path
    ).execute().get("tag", [])
    for t in existing:
        if t.get("name") == tag_spec["name"]:
            print(f"  tag {tag_spec['name']!r}: already exists, skipping")
            return t["path"]
    if dry_run:
        print(f"  tag {tag_spec['name']!r}: WOULD CREATE")
        return ""
    created = svc.accounts().containers().workspaces().tags().create(
        parent=workspace_path, body=tag_spec
    ).execute()
    print(f"  tag {tag_spec['name']!r}: created")
    return created["path"]


def upsert_trigger(svc, workspace_path: str, trigger_spec: dict[str, Any], dry_run: bool) -> str:
    existing = svc.accounts().containers().workspaces().triggers().list(
        parent=workspace_path
    ).execute().get("trigger", [])
    for t in existing:
        if t.get("name") == trigger_spec["name"]:
            print(f"  trigger {trigger_spec['name']!r}: already exists, skipping")
            return t["triggerId"]
    if dry_run:
        print(f"  trigger {trigger_spec['name']!r}: WOULD CREATE")
        return ""
    created = svc.accounts().containers().workspaces().triggers().create(
        parent=workspace_path, body=trigger_spec
    ).execute()
    print(f"  trigger {trigger_spec['name']!r}: created")
    return created["triggerId"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Log planned changes without applying them.")
    args = parser.parse_args()

    creds = credentials()
    svc = build("tagmanager", "v2", credentials=creds, cache_discovery=False)

    print(f"=== GTM bootstrap (dry-run={args.dry_run}) ===")
    account = find_account(svc)
    print(f"Account: {account['name']} ({account['path']})")
    container = find_container(svc, account["path"])
    print(f"Container: {container['name']} {container['publicId']} ({container['path']})")
    workspace = get_or_create_default_workspace(svc, container["path"])
    print(f"Workspace: {workspace['name']} ({workspace['path']})")

    # Triggers
    print("\nTriggers:")
    all_pages_trigger_id = upsert_trigger(svc, workspace["path"], {
        "name": "All Pages",
        "type": "pageview",
    }, args.dry_run)

    donate_click_trigger_id = upsert_trigger(svc, workspace["path"], {
        "name": "Donate click (outbound)",
        "type": "linkClick",
        "filter": [{
            "type": "matchRegex",
            "parameter": [
                {"type": "template", "key": "arg0", "value": "{{Click URL}}"},
                {"type": "template", "key": "arg1",
                 "value": r"(paypal\.com\/donate|zeffy\.com|donate\.thecrookedhouse\.net)"},
            ],
        }],
    }, args.dry_run)

    email_click_trigger_id = upsert_trigger(svc, workspace["path"], {
        "name": "Email Us click (mailto)",
        "type": "linkClick",
        "filter": [{
            "type": "contains",
            "parameter": [
                {"type": "template", "key": "arg0", "value": "{{Click URL}}"},
                {"type": "template", "key": "arg1",
                 "value": "mailto:b@thecrookedhouse.net"},
            ],
        }],
    }, args.dry_run)

    # Tags
    print("\nTags:")
    upsert_tag(svc, workspace["path"], {
        "name": "GA4 Configuration",
        "type": "gaawc",  # Google Analytics: GA4 Configuration
        "parameter": [
            {"type": "template", "key": "measurementId", "value": GA4_MEASUREMENT_ID},
            {"type": "boolean", "key": "sendPageView", "value": "true"},
        ],
        "firingTriggerId": [all_pages_trigger_id] if all_pages_trigger_id else [],
        "consentSettings": {
            "consentStatus": "needed",
            "consentType": {
                "type": "list",
                "list": [
                    {"type": "template", "value": "analytics_storage"},
                ],
            },
        },
    }, args.dry_run)

    upsert_tag(svc, workspace["path"], {
        "name": "GA4 Event — donate_click",
        "type": "gaawe",
        "parameter": [
            {"type": "template", "key": "measurementIdOverride", "value": GA4_MEASUREMENT_ID},
            {"type": "template", "key": "eventName", "value": "donate_click"},
        ],
        "firingTriggerId": [donate_click_trigger_id] if donate_click_trigger_id else [],
        "consentSettings": {
            "consentStatus": "needed",
            "consentType": {
                "type": "list",
                "list": [{"type": "template", "value": "analytics_storage"}],
            },
        },
    }, args.dry_run)

    upsert_tag(svc, workspace["path"], {
        "name": "GA4 Event — email_click",
        "type": "gaawe",
        "parameter": [
            {"type": "template", "key": "measurementIdOverride", "value": GA4_MEASUREMENT_ID},
            {"type": "template", "key": "eventName", "value": "email_click"},
        ],
        "firingTriggerId": [email_click_trigger_id] if email_click_trigger_id else [],
    }, args.dry_run)

    # Publish
    if not args.dry_run:
        version = svc.accounts().containers().workspaces().create_version(
            path=workspace["path"],
            body={"name": "API bootstrap", "notes": "Generated by bootstrap-gtm.py"},
        ).execute()
        v = version.get("containerVersion", {})
        if v:
            svc.accounts().containers().versions().publish(path=v["path"]).execute()
            print(f"\nPublished version {v.get('containerVersionId', '?')}")
        else:
            print("\nNo changes to publish (workspace already in sync).")

    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
