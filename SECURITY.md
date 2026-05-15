# Security Policy

## Reporting a Vulnerability

The security of The Crooked House website is important to us. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT** open a public issue
2. Send details to: info@thecrookedhouse.net
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### What to Expect

- We will acknowledge receipt within 48 hours
- We will investigate and respond with our assessment
- We will work to address confirmed vulnerabilities promptly
- We will keep you informed of progress

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Security Measures

This website implements:

- Cookie consent management for user privacy
- Secure HTTPS connections
- Regular security scans via CodeQL
- Content Security Policy (CSP) headers where supported by the hosting platform

## Privacy

Please review our [Cookie Policy](https://thecrookedhouse.net/cookie-policy.html) for information about how we handle cookies and tracking.

## Third-Party Services

This website may use the following third-party services (with user consent):

- **Google Analytics** - Website analytics
- **Microsoft Clarity** - User behavior analytics
- **Meta Pixel** - Marketing analytics

Each service has its own security and privacy policies. Please refer to their respective documentation for more information.

## Updates

This security policy may be updated periodically. Please check back regularly for any changes.

## Incident log

### 2026-05-15 — GitHub Actions OIDC token committed to a PR

**What.** A `gha-creds-*.json` file (Workload Identity Federation credential file written by `google-github-actions/auth@v2`, containing a short-lived GitHub Actions OIDC JWT) was accidentally included in PR #94 by the wire-site step of the Google API setup workflow. GitHub Secret Scanning flagged it.

**Risk.** The leaked artifact was an OIDC JWT (not a Google access token). Until the JWT expired at 2026-05-16 02:09 UTC (~6 hours from the leak), it could have been exchanged via STS for a Google access token impersonating the `githubactions-thecrookedhouse@…` service account.

**Mitigations applied.**

- Service account `githubactions-thecrookedhouse@charming-hour-496417-p9.iam.gserviceaccount.com` was **disabled** via `gcloud iam service-accounts disable` within ~30 minutes of detection. Disabled SAs cannot be impersonated, so any subsequent STS exchange of the leaked JWT failed.
- `.gitignore` updated (commit `01d4acb`) to exclude `gha-creds-*.json` from any future commit.
- The workflow's `peter-evans/create-pull-request` step now uses an explicit `add-paths` allowlist so only intended files (HTML + cookie-consent.js) are committed by automation. Eliminates the leak vector at the source.
- The WIF provider's `attributeCondition` was tightened from `assertion.repository_owner == 'FreeForCharity'` to `assertion.repository == 'FreeForCharity/FFC-EX-thecrookedhouse.net'`. Reduces blast radius — even a leaked OIDC token from a different FreeForCharity repo cannot impersonate this SA.

**No unauthorized API activity** was detected on the GTM / GA accounts during the exposure window.

---

Last Updated: 2026-05-15
