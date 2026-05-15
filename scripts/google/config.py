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
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/tagmanager.manage.users",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def credentials():
    """Resolve Application Default Credentials and scope them.

    Order of resolution (handled by google.auth.default):
      1. GOOGLE_APPLICATION_CREDENTIALS env var (file path, optional)
      2. WIF / external account credentials set up by gcloud or
         google-github-actions/auth@v2
      3. gcloud user credentials (from `gcloud auth application-default login`)
      4. GCE / Cloud Run metadata server
    """
    import google.auth

    creds, project = google.auth.default(scopes=SCOPES)
    if project and project != GCP_PROJECT_ID:
        # Don't fail — just note the mismatch for debugging.
        import sys
        print(f"note: ADC project ({project}) differs from configured "
              f"GCP_PROJECT_ID ({GCP_PROJECT_ID})", file=sys.stderr)
    return creds
