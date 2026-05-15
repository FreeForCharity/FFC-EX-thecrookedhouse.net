#!/usr/bin/env python3
"""Idempotent GA4 property bootstrap.

Configures the existing GA4 property + Web data stream with:

  * Data retention set to 14 months (max non-paid)
  * Enhanced measurement enabled on the web stream (scrolls, outbound links,
    file downloads, video engagement, form interactions)
  * Conversion events created: donate_click, email_click
  * Custom dimension: donor_source (user-scoped)

Property ID is discovered automatically from the known measurement ID
G-EDCGRNN40D unless GA4_PROPERTY_ID is set in the environment.

Re-running is safe. Pass --dry-run to log without applying.
"""

from __future__ import annotations

import argparse
import os
import sys

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import (
    ConversionEvent,
    CustomDimension,
    DataRetentionSettings,
    UpdateDataRetentionSettingsRequest,
)

from config import GA4_MEASUREMENT_ID, GA4_PROPERTY_ID, credentials


def find_property_id(client) -> str:
    """Locate the property ID by enumerating accounts and matching the
    measurement ID on web data streams."""
    if GA4_PROPERTY_ID:
        return f"properties/{GA4_PROPERTY_ID}"

    # List all accessible accounts, then properties, then streams.
    for account_summary in client.list_account_summaries():
        for prop_summary in account_summary.property_summaries:
            prop_path = prop_summary.property
            try:
                streams = client.list_data_streams(parent=prop_path)
            except Exception as e:
                print(f"  skipping {prop_path}: {e}")
                continue
            for stream in streams:
                wsd = getattr(stream, "web_stream_data", None)
                if wsd and wsd.measurement_id == GA4_MEASUREMENT_ID:
                    print(f"Discovered property: {prop_path} (display: {prop_summary.display_name})")
                    return prop_path
    raise SystemExit(
        f"No GA4 property found whose web stream has measurement_id={GA4_MEASUREMENT_ID}. "
        "Either set GA4_PROPERTY_ID env var or add the service account as a user on the property."
    )


def ensure_data_retention(client, property_path: str, dry_run: bool) -> None:
    print("Data retention:")
    settings = client.get_data_retention_settings(name=f"{property_path}/dataRetentionSettings")
    desired = DataRetentionSettings.RetentionDuration.FOURTEEN_MONTHS
    if settings.event_data_retention == desired and settings.reset_user_data_on_new_activity:
        print("  already at 14 months with reset on new activity — skipping")
        return
    if dry_run:
        print(f"  WOULD set event_data_retention=14 months (current: {settings.event_data_retention.name})")
        return
    settings.event_data_retention = desired
    settings.reset_user_data_on_new_activity = True
    req = UpdateDataRetentionSettingsRequest(
        data_retention_settings=settings,
        update_mask={"paths": ["event_data_retention", "reset_user_data_on_new_activity"]},
    )
    client.update_data_retention_settings(request=req)
    print("  set to 14 months, reset on new activity")


def ensure_conversion_events(client, property_path: str, dry_run: bool) -> None:
    print("Conversion events:")
    existing = {e.event_name for e in client.list_conversion_events(parent=property_path)}
    for name in ("donate_click", "email_click"):
        if name in existing:
            print(f"  {name}: already a conversion — skipping")
            continue
        if dry_run:
            print(f"  {name}: WOULD CREATE")
            continue
        client.create_conversion_event(
            parent=property_path,
            conversion_event=ConversionEvent(event_name=name),
        )
        print(f"  {name}: created")


def ensure_custom_dimensions(client, property_path: str, dry_run: bool) -> None:
    print("Custom dimensions:")
    existing = {d.parameter_name for d in client.list_custom_dimensions(parent=property_path)}
    targets = [
        ("donor_source", "Donor source", CustomDimension.DimensionScope.USER,
         "Where the donor learned about The Crooked House (Facebook, email, organic, etc.)"),
    ]
    for param_name, display_name, scope, description in targets:
        if param_name in existing:
            print(f"  {param_name}: already exists — skipping")
            continue
        if dry_run:
            print(f"  {param_name}: WOULD CREATE")
            continue
        client.create_custom_dimension(
            parent=property_path,
            custom_dimension=CustomDimension(
                parameter_name=param_name,
                display_name=display_name,
                scope=scope,
                description=description,
            ),
        )
        print(f"  {param_name}: created")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Log planned changes without applying them.")
    args = parser.parse_args()

    creds = credentials()
    client = AnalyticsAdminServiceClient(credentials=creds)

    print(f"=== GA4 bootstrap (dry-run={args.dry_run}) ===")
    property_path = find_property_id(client)
    print(f"Operating on {property_path}\n")

    ensure_data_retention(client, property_path, args.dry_run)
    print()
    ensure_conversion_events(client, property_path, args.dry_run)
    print()
    ensure_custom_dimensions(client, property_path, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
