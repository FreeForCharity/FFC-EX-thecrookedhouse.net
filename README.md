# FFC-EX-thecrookedhouse.net

This repository contains the static website for The Crooked House project at Homecoming Park.

## About

The Crooked House is a sculpture by Benjamin Fehl, preserving the façade of a historic house in Milesburg in concrete as a permanent art installation at Homecoming Park.

## Repository

- **Repository URL**: [https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net)
- **Organization**: FreeForCharity
- **Website**: [https://thecrookedhouse.net](https://thecrookedhouse.net)

## Development

This is a static HTML website hosted on GitHub Pages.

### Deployment

The site is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

See `.github/workflows/static.yml` for deployment configuration.

## Structure

- `index.html` - Main homepage
- `cookie-policy.html` - Cookie policy page
- `cookie-consent.js` - Cookie consent management system
- `cookie-consent.css` - Cookie consent styling
- `become-a-friend/` - Information about becoming a Friend of The Crooked House
- `donors/` - Donor information and recognition
- `press/` - Press and media information
- `.github/workflows/` - GitHub Actions workflows for deployment and security

## Features

### Cookie Consent Management

The website includes a GDPR-compliant cookie consent system that:

- Allows users to accept, decline, or customize cookie preferences
- Supports necessary, functional, analytics, and marketing cookies
- Provides conditional loading of third-party scripts based on user consent
- Stores preferences in localStorage for 12 months
- Includes a detailed cookie policy page

**Third-party services** (loaded only with user consent):
- Google Analytics (analytics)
- Microsoft Clarity (analytics)
- Meta Pixel (marketing)

### Security

- CodeQL security scanning
- Static site deployment via GitHub Pages
- See [SECURITY.md](SECURITY.md) for security policies

## Privacy

For information about cookies and privacy, see:
- [Cookie Policy](https://thecrookedhouse.net/cookie-policy.html)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting changes.

See also [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community guidelines.

## License

All content is copyright The Crooked House project and FreeForCharity.
