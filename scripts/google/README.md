# Google API automation

Scripts that manage The Crooked House's Google Tag Manager + Google Analytics 4 via API rather than the web UI. They're idempotent: re-running won't duplicate work.

## What's automated

| Script | What it does |
|---|---|
| `bootstrap-gtm.py` | Configures the GTM container (`GTM-5JV8JHCH`): consent-mode v2 defaults, the GA4 Configuration tag, the GTM trigger for "All Pages", outbound-click conversion tracking (`donate_click`, `email_click`), and publishes a new container version. |
| `bootstrap-ga4.py` | Configures the GA4 property: 14-month data retention, Web data stream, Enhanced Measurement settings, conversion events that match what GTM fires, custom dimensions for donor segmentation. |
| `manage-users.py` | Reconciles GTM + GA4 user access against the declarative roster in `users.py`. Idempotent: invites missing users, updates roles that drifted, optionally prunes users not in the roster (`--prune`). |
| `wire-site.py` | Patches the four content pages + `cookie-policy.html` + `404.html` to load the GTM container snippet and removes the legacy direct-gtag loading from `cookie-consent.js`. |

To add or remove team members, edit `users.py` (one Python dict per person) and re-run `manage-users.py`. No code changes required.

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
Created in GCP console under the `charming-hour-496417-p9` project:

- Name: `githubactions-thecrookedhouse`
- Email: `githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com`
- Roles at project level: none (we grant per-product in the UIs)
- **No JSON key needed** — we use Workload Identity Federation instead.

### 3. Workload Identity Federation (auth without JSON keys)

WIF lets GitHub Actions impersonate the service account with a short-lived OIDC token instead of a long-lived JSON key — Google's recommended pattern.

One-time setup in GCP:

```bash
# 1. Create the workload identity pool (free)
gcloud iam workload-identity-pools create github-actions \
  --project=charming-hour-496417-p9 \
  --location=global \
  --display-name="GitHub Actions"

# 2. Create the GitHub OIDC provider in that pool
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=charming-hour-496417-p9 \
  --location=global \
  --workload-identity-pool=github-actions \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'FreeForCharity'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 3. Allow the GitHub repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com \
  --project=charming-hour-496417-p9 \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions/attribute.repository/FreeForCharity/FFC-EX-thecrookedhouse.net"
```

Get the project number for the last command:
```bash
gcloud projects describe charming-hour-496417-p9 --format='value(projectNumber)'
```

The full WIF provider path you'll need for the `WIF_PROVIDER` env variable:
```
projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions/providers/github-provider
```

### 4. Service account permissions (granted in product UIs, not GCP)

- **GTM**: Tag Manager → Admin → User Management on the account → Add user → `githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com` → role: **Admin**
- **GA4**: Analytics → Admin → Property access management → Add user → same email → role: **Editor** (or Administrator)

### 5. GitHub Actions environment

The scripts run in the **`google-prod`** GitHub environment (Settings → Environments → google-prod). IDs are public — they ship in the page HTML — so they live as **variables** (visible in logs).

| Type | Name | Value |
|---|---|---|
| variable | `GCP_PROJECT_ID` | `charming-hour-496417-p9` |
| variable | `GTM_CONTAINER_ID` | `GTM-5JV8JHCH` |
| variable | `GA4_MEASUREMENT_ID` | `G-EDCGRNN40D` |
| variable | `GA4_STREAM_ID` | `14886848587` |
| variable | `GOOGLE_SA_NAME` | `githubactions-thecrookedhouse` |
| variable | `GOOGLE_SA_EMAIL` | `githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com` |
| variable | `WIF_PROVIDER` | full path from step 3 |
| secret (optional) | `GA4_PROPERTY_ID` | numeric — auto-discovered if unset |

**No `GOOGLE_SA_KEY` needed.** That's the whole point of WIF.

## How to run

### From a local machine (testing)

```bash
cd scripts/google
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Authenticate as your Google user via ADC (one-time per machine)
gcloud auth application-default login

# IDs default to baked-in values in config.py; override only if needed.

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
