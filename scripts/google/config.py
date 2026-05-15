"""Shared config + auth for the bootstrap scripts.

Authentication uses **Application Default Credentials (ADC)**, which works
transparently in three contexts:

  1. GitHub Actions via Workload Identity Federation
     (no JSON key; google-github-actions/auth@v2 sets up ADC for us).
  2. Local development after `gcloud auth application-default login`.
  3. Legacy: a service-account JSON file path in
     GOOGLE_APPLICATION_CREDENTIALS, if you ever need that fallback.

This is the Google-recommended pattern. We deliberately do NOT consume a
JSON key passed via env var — that would defeat the whole point of WIF.
"""

from __future__ import annotations

import os

# Known fixed identifiers for The Crooked House (override via env if they change).
SITE_URL = "https://thecrookedhouse.net"
SITE_NAME = "The Crooked House"
ACCOUNT_NAME = "The Crooked House"
CONTAINER_NAME = "thecrookedhouse.net"

GTM_CONTAINER_ID = os.environ.get("GTM_CONTAINER_ID", "GTM-5JV8JHCH")
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "G-EDCGRNN40D")
GA4_STREAM_ID = os.environ.get("GA4_STREAM_ID", "14886848587")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "charming-hour-496417-p9")
# Property ID is numeric; not provided yet — discovered at runtime via the
# Analytics Admin API if unset.
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID")

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/tagmanager.manage.users",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def credentials():
    """Resolve credentials, preferring the FFC OAuth refresh token if present.

    Order of resolution:
      1. ~/.config/ffc-google/token.json — refresh token from bootstrap-sa-access.py
         (broader scopes than gcloud default; needed for user-management APIs)
      2. GOOGLE_APPLICATION_CREDENTIALS env var (file path, optional)
      3. WIF / external account credentials set up by gcloud or
         google-github-actions/auth@v2
      4. gcloud user credentials (from `gcloud auth application-default login`)
      5. GCE / Cloud Run metadata server
    """
    from pathlib import Path

    ffc_token = Path.home() / ".config" / "ffc-google" / "token.json"
    if ffc_token.exists():
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials.from_authorized_user_file(str(ffc_token), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    import google.auth

    creds, project = google.auth.default(scopes=SCOPES)
    if project and project != GCP_PROJECT_ID:
        import sys
        print(f"note: ADC project ({project}) differs from configured "
              f"GCP_PROJECT_ID ({GCP_PROJECT_ID})", file=sys.stderr)
    return creds
