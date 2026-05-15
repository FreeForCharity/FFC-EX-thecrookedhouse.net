# Google API automation

Scripts that manage The Crooked House's Google Tag Manager + Google Analytics 4 via API rather than the web UI. They're idempotent: re-running won't duplicate work.

## What's automated

| Script | What it does |
|---|---|
| `bootstrap-gtm.py` | Configures the GTM container (`GTM-5JV8JHCH`): consent-mode v2 defaults, the GA4 Configuration tag, the GTM trigger for "All Pages", outbound-click conversion tracking (`donate_click`, `email_click`), and publishes a new container version. |
| `bootstrap-ga4.py` | Configures the GA4 property: 14-month data retention, Web data stream, Enhanced Measurement settings, conversion events that match what GTM fires, custom dimensions for donor segmentation. |
| `wire-site.py` | Patches the four content pages + `cookie-policy.html` + `404.html` to load the GTM container snippet and removes the legacy direct-gtag loading from `cookie-consent.js`. |

## What's NOT automated (one-time, requires a human)

These cannot be done via API; Google requires a human user (signed in as `clarkemoyer@thecrookedhouse.net`) to do them once:

1. **Accept GTM Terms of Service** by visiting <https://tagmanager.google.com/>
2. **Accept GA4 Terms of Service** by visiting <https://analytics.google.com/>
3. **Create the GTM account + container** (or skip — `bootstrap-gtm.py` can do this *after* ToS is accepted)
4. **Create the GA4 account** (the API can create *properties* under an existing account, but not the account itself)
5. **Add the service account email as a user** on the GTM account (Admin role) and GA4 property (Editor role), in their respective admin UIs

Once those are done, this scripts directory takes over.

## Prerequisites

### 1. GCP project + APIs enabled
See [issue #77](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/77). Project: `thecrookedhouse`. APIs:

- Tag Manager API
- Google Analytics Admin API
- Google Analytics Data API

### 2. Service account
Created in GCP console under `thecrookedhouse` project:

- Name: `ffc-automation`
- Email: `ffc-automation@thecrookedhouse.iam.gserviceaccount.com` (example)
- Roles: none at project level
- Key: JSON, downloaded once

### 3. Service account permissions
Granted in the respective product UIs (not GCP):

- **GTM**: in Tag Manager → Admin → User Management on the account → Add user → service account email → role: Admin
- **GA4**: in Analytics → Admin → Property access management → Add user → service account email → role: Editor (or Administrator if needed)

### 4. GitHub Actions secrets
Required secrets on the repository (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `GOOGLE_SA_KEY` | The full contents of the service account JSON key file |
| `GTM_CONTAINER_ID` | `GTM-5JV8JHCH` |
| `GA4_PROPERTY_ID` | The numeric property ID, e.g. `123456789` (find in Analytics → Admin → Property settings) |
| `GA4_MEASUREMENT_ID` | The `G-XXXXXXXXXX` ID from the Web data stream |

## How to run

### From a local machine (testing)

```bash
cd scripts/google
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set env from a local .env file (not committed)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/ffc-automation-key.json
export GTM_CONTAINER_ID=GTM-5JV8JHCH
export GA4_PROPERTY_ID=123456789
export GA4_MEASUREMENT_ID=G-XXXXXXXXXX

python bootstrap-gtm.py --dry-run    # preview changes
python bootstrap-gtm.py              # apply
python bootstrap-ga4.py --dry-run
python bootstrap-ga4.py
python wire-site.py                  # patches HTML files
```

### From GitHub Actions (CI)

The workflow at `.github/workflows/google-setup.yml` runs on manual dispatch with three job choices: `bootstrap-gtm`, `bootstrap-ga4`, `wire-site`. Trigger it from the Actions tab.

## Idempotence

All three scripts check what's already configured and skip work that's already done. Re-running is safe — they'll log "already exists, skipping" for anything they don't need to change.

## Reading back

After bootstrap, run `python report.py` (TODO) to print the current GTM + GA4 configuration as a sanity check.
