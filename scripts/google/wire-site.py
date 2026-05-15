#!/usr/bin/env python3
"""Patch the static site to load the GTM container instead of direct gtag/js.

What this changes:

  1. Adds the GTM container snippet to the <head> of every content page +
     cookie-policy.html + 404.html (just before </head>, after the existing
     CSP meta).
  2. Adds the matching <noscript> iframe fallback immediately after <body>.
  3. Updates cookie-consent.js to STOP loading gtag/js directly and instead
     emit the GTM consent-mode v2 dataLayer calls (default + update events
     when user accepts/declines categories).

Re-running is safe — the script looks for an already-inserted GTM_CONTAINER_ID
marker and skips files that have it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from config import GTM_CONTAINER_ID

REPO_ROOT = Path(__file__).resolve().parents[2]

PAGES = [
    "index.html",
    "donors/index.html",
    "press/index.html",
    "become-a-friend/index.html",
    "cookie-policy.html",
    "404.html",
]


def gtm_head_snippet() -> str:
    """The official GTM <head> snippet with consent-mode v2 defaults applied
    BEFORE the container loads."""
    return f"""<!-- Google Tag Manager (consent-mode v2 default applied first) -->
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('consent', 'default', {{
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied',
  'analytics_storage': 'denied',
  'functionality_storage': 'granted',
  'security_storage': 'granted',
  'wait_for_update': 500
}});
(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_CONTAINER_ID}');
</script>
<!-- End Google Tag Manager -->"""


def gtm_body_noscript() -> str:
    return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_CONTAINER_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def patch_page(path: Path, dry_run: bool) -> bool:
    """Returns True if file was changed."""
    text = path.read_text(encoding="utf-8")
    if GTM_CONTAINER_ID in text:
        print(f"  {path.relative_to(REPO_ROOT)}: GTM already present, skipping")
        return False

    head_snippet = gtm_head_snippet()
    body_snippet = gtm_body_noscript()

    # Insert head snippet after the CSP meta tag (or before </head> if no CSP)
    csp_re = re.compile(r"(<meta http-equiv=[\"']?content-security-policy[\"']?[^>]*>)",
                        re.IGNORECASE)
    if csp_re.search(text):
        text = csp_re.sub(r"\1" + head_snippet, text, count=1)
    else:
        head_close_re = re.compile(r"(</head\s*>)", re.IGNORECASE)
        if head_close_re.search(text):
            text = head_close_re.sub(head_snippet + r"\1", text, count=1)
        else:
            # Fallback: insert right before <body
            body_re = re.compile(r"(<body\b)", re.IGNORECASE)
            text = body_re.sub(head_snippet + r"\1", text, count=1)

    # Insert noscript iframe immediately after <body...>
    body_open_re = re.compile(r"(<body\b[^>]*>)", re.IGNORECASE)
    text = body_open_re.sub(r"\1" + body_snippet, text, count=1)

    if dry_run:
        print(f"  {path.relative_to(REPO_ROOT)}: WOULD PATCH (head + body)")
        return True

    path.write_text(text, encoding="utf-8")
    print(f"  {path.relative_to(REPO_ROOT)}: patched (head + body)")
    return True


def patch_cookie_consent_js(dry_run: bool) -> bool:
    """Replace the direct gtag/js loading with consent-mode v2 dataLayer
    updates that GTM's container reacts to."""
    js_path = REPO_ROOT / "cookie-consent.js"
    if not js_path.exists():
        print("  cookie-consent.js not found, skipping")
        return False
    text = js_path.read_text(encoding="utf-8")
    if "// GTM consent-mode v2 wired" in text:
        print("  cookie-consent.js: already wired for GTM consent mode, skipping")
        return False
    # We DON'T strip the existing GA-loading code in this scaffolding pass —
    # instead we add the consent-mode update calls and let the GTM container
    # handle the actual GA load. The legacy code is short-circuited because
    # CONFIG.GA_MEASUREMENT_ID will be left as the placeholder.
    # A follow-up PR can fully remove the gtag-loading code.
    addition = """
// GTM consent-mode v2 wired
// Called by the cookie banner whenever the user updates their preferences.
function pushConsentUpdate(consent) {
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'update', {
    'ad_storage': consent.marketing ? 'granted' : 'denied',
    'ad_user_data': consent.marketing ? 'granted' : 'denied',
    'ad_personalization': consent.marketing ? 'granted' : 'denied',
    'analytics_storage': consent.analytics ? 'granted' : 'denied',
    'functionality_storage': consent.functional ? 'granted' : 'denied',
    'security_storage': 'granted'
  });
}
"""
    text = text.rstrip() + "\n" + addition + "\n"
    if dry_run:
        print("  cookie-consent.js: WOULD APPEND consent-update bridge")
        return True
    js_path.write_text(text, encoding="utf-8")
    print("  cookie-consent.js: appended consent-update bridge")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Log planned changes without applying them.")
    args = parser.parse_args()

    print(f"=== wire-site (GTM={GTM_CONTAINER_ID}, dry-run={args.dry_run}) ===\n")

    print("HTML pages:")
    changed_pages = 0
    for rel in PAGES:
        p = REPO_ROOT / rel
        if not p.exists():
            print(f"  {rel}: NOT FOUND, skipping")
            continue
        if patch_page(p, args.dry_run):
            changed_pages += 1

    print("\nJS:")
    js_changed = patch_cookie_consent_js(args.dry_run)

    print(f"\nSummary: {changed_pages} page(s) patched, js wired = {js_changed}")
    print("Don't forget: commit + PR + verify on the live site.")


if __name__ == "__main__":
    sys.exit(main())
