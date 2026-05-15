"""Declarative roster of people who should have access to GTM + GA4.

Edit this file (no code changes) when adding/removing team members. The
manage-users.py script reads it and reconciles the live state idempotently.

Roles:
  GTM   - 'admin' or 'edit' (account-level)
  GA4   - 'admin' or 'editor' or 'viewer' (property-level)
"""

USERS = [
    {
        "email": "clarkemoyer@freeforcharity.org",
        "display": "Clarke Moyer (FFC volunteer team)",
        "gtm": "admin",
        "ga4": "editor",
    },
    # Add more users below — format follows the dict above.
    # Example:
    # {
    #     "email": "boardmember@thecrookedhouse.net",
    #     "display": "Board member name",
    #     "gtm": None,        # No GTM access
    #     "ga4": "viewer",    # Read-only GA4
    # },
]
