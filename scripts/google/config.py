"""Shared config + auth for the bootstrap scripts.

Values can come from environment variables (preferred) or fall back to known
defaults below. The service-account key is always loaded from
GOOGLE_APPLICATION_CREDENTIALS or the GOOGLE_SA_KEY env var (JSON contents).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

# Known fixed IDs for The Crooked House (override via env if they change).
SITE_URL = "https://thecrookedhouse.net"
SITE_NAME = "The Crooked House"
ACCOUNT_NAME = "The Crooked House"
CONTAINER_NAME = "thecrookedhouse.net"

GTM_CONTAINER_ID = os.environ.get("GTM_CONTAINER_ID", "GTM-5JV8JHCH")
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "G-EDCGRNN40D")
GA4_STREAM_ID = os.environ.get("GA4_STREAM_ID", "14886848587")
# Property ID is numeric; not provided yet — discovered at runtime via the
# Analytics Admin API if unset.
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID")

# Scopes — superset for both bootstrap scripts.
SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/tagmanager.manage.users",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def credentials():
    """Build google-auth credentials from either GOOGLE_APPLICATION_CREDENTIALS
    (path to JSON) or GOOGLE_SA_KEY (raw JSON contents, used in CI)."""
    from google.oauth2 import service_account

    inline_key = os.environ.get("GOOGLE_SA_KEY")
    if inline_key:
        info = json.loads(inline_key)
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path and Path(key_path).exists():
        return service_account.Credentials.from_service_account_file(
            key_path, scopes=SCOPES
        )

    raise RuntimeError(
        "No service-account credentials found. Set either "
        "GOOGLE_APPLICATION_CREDENTIALS (file path) or GOOGLE_SA_KEY "
        "(JSON contents)."
    )
