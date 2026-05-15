# FFC pattern: bootstrapping service-account access to Google products

A recurring problem across FFC sites: **GTM and GA's user-management UIs reject service account emails** ("This email doesn't match a Google Account"). The product APIs accept SA emails fine, but the required scopes (`tagmanager.manage.users`, `analytics.manage.users`) aren't in gcloud's whitelisted set.

The fix below is the canonical FFC pattern. Use it on every new site.

## One-time per FFC-managed GCP project

### 1. Configure the OAuth consent screen (if not already done)

1. <https://console.cloud.google.com/apis/credentials/consent> → select the project
2. User Type: **Internal** (the project is in a Workspace org → internal-only is fine)
3. App information:
   - App name: `FFC API Admin`
   - User support email: the project owner's Workspace email
   - Developer contact: same
4. Scopes: skip (we'll request specific scopes at OAuth flow time)
5. Save and continue

### 2. Create the OAuth client

1. <https://console.cloud.google.com/apis/credentials> → select the project
2. **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `FFC API Admin (local)`
5. Click **Create**
6. **Download JSON** from the popup — save it as `client_secret_ffc-api-admin.json`

> ⚠️ Despite the name, "client secrets" for Desktop OAuth apps are **not real secrets**; Google's docs explicitly note this. They can't be exfiltrated to do harm because Google still requires user consent in a browser. But still keep the file out of git.

### 3. Run the bootstrap script

```bash
cd scripts/google
pip install -r requirements.txt

python bootstrap-sa-access.py \
  --client-secrets ~/Downloads/client_secret_ffc-api-admin.json \
  --sa-email <SA_EMAIL> \
  --gtm-account "<GTM_ACCOUNT_NAME>" \
  --ga4-measurement-id <G-XXXXXXXXXX> \
  --gtm-role admin \
  --ga4-role editor
```

The first run opens a browser. Sign in as a user who is **Admin on the GTM account** and **Administrator on the GA4 property**, click **Allow**. A refresh token is cached at `~/.config/ffc-google/token.json` — subsequent runs don't need the browser.

The script is idempotent. Re-running reports "already granted" for anything already configured.

## When to re-run

- New service account that needs API access on a product → run the script with that SA
- Re-rotating the OAuth refresh token → delete `~/.config/ffc-google/token.json` and re-run

## When NOT to use this

For granting **human user** access — that works fine in the GTM and GA UIs. Use the UIs for people; reserve this script for service accounts.

## FFC-wide reuse

This OAuth client lives in the project's own GCP space. If FFC wants a single shared OAuth client across all sites, host it in a dedicated `ffc-shared` GCP project; the client_secrets JSON then becomes a shared FFC artifact rather than per-site.

## Per-site usage

| Site | SA email | GTM account | GA4 measurement | Bootstrap command |
|---|---|---|---|---|
| thecrookedhouse.net | `githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com` | "The Crooked House" | `G-EDCGRNN40D` | see above |

Add a row for each new FFC site as it's onboarded.
