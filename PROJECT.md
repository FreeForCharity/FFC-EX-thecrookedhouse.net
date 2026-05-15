# The Crooked House — Project Dashboard

A living view of what's happening on **[thecrookedhouse.net](https://thecrookedhouse.net)** and how Benjamin (owner) and the FFC volunteer team work together on it.

📊 **Kanban board** (drag-and-drop view of every task with status, assignee, priority): **<https://github.com/orgs/FreeForCharity/projects/6>**

If you're Benjamin and you just landed here, read **[For the owner](#for-the-owner)** below — that's the part for you.

---

## Where things stand

| Area | Status |
|---|---|
| Live website | ✅ Up at https://thecrookedhouse.net — mobile, SEO, accessibility, social-share previews all current |
| Cookie consent (GDPR-compliant) | ✅ Live, awaiting GA / GTM IDs to actually start measuring |
| Donations | ⚠️ Still PayPal — moving to **Zeffy** (0% fees) |
| Email / @thecrookedhouse.net | ❌ Not yet on Google Workspace |
| Analytics / measurement | ❌ Not yet — no traffic data being collected |
| Google Ad Grants ($10K/mo) | ❌ Not yet applied |
| YouTube channel | ❌ Not yet set up |
| Custom domain admin / API access | ❌ Not yet |

---

## What just shipped (last few sessions)

The website got an overhaul in May 2026:

- **Performance**: home page went from **3.9 MB → 410 KB** (89 % smaller). Images are lazy-loaded, properly sized, and cached.
- **Mobile**: donor lists no longer squashed into unreadable columns; cookie banner takes a quarter of the screen instead of half; hero logo isn't cropped.
- **Sponsor / grantmaker updates**: new Pennsylvania Creative Industries logo on the donors page, new Centre Gives logo and acknowledgment text in every footer.
- **Become a Friend**: replaced the broken contact form with a working "Email Us" button.
- **Accessibility**: skip-to-content links, descriptive alt text written for every gallery photo, single H1 per page, ARIA on the mobile menu.
- **SEO**: site map, robots, descriptive page titles, social-share preview image, structured data describing the sculpture and its creator.
- **Infrastructure**: real favicon, custom 404 page, https-everywhere on outbound links.

Latest live snapshots are in the repo (search for `postdeploy-*.png` and `live-*.png`).

---

## What's next — the two big tracks

### 🟦 Google Workspace integration → [Tracker #69](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/69)

In execution order:

1. [#62](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/62) — Enroll in Google for Nonprofits (TechSoup / Percent verification)
2. [#63](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/63) — Set up Workspace tenant (Gmail, DNS, DKIM/DMARC)
3. [#76](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/76) — Grant FFC team (clarkemoyer@freeforcharity.org) admin access across all products
4. [#67](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/67) — Google Tag Manager (the central tag manager)
5. [#64](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/64) — Google Analytics 4 (deployed as a GTM tag)
6. [#65](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/65) — Search Console + sitemap submission
7. [#68](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/68) — YouTube Nonprofit Program
8. [#77](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/77) — Google Cloud Project, service account, API access
9. [#66](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/66) — Google Ad Grants ($10K/month in free search ads)

### 🟪 Google services expansion (backlog)

Things that build on the Workspace + GTM + GA4 foundation, in rough value order:

1. [#82](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/82) — Looker Studio dashboard (free) fed by GA4 + Search Console
2. [#83](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/83) — Google Business Profile + Maps embed (local search visibility)
3. [#85](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/85) — Workspace API automation (domain-wide delegation; needed for Gmail/Drive/Calendar scripts)
4. [#84](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/84) — Cloud Storage + scheduled Cloud Functions (daily backups, monthly donor reports)

### 🟧 Zeffy fundraising integration → [Tracker #75](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/75)

1. [#70](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/70) — Sign up + verify 501(c)(3)
2. [#71](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/71) — Configure the donation form
3. [#72](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/72) — Swap PayPal URLs site-wide
4. [#73](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/73) — *(Optional)* Embed Zeffy on /become-a-friend/
5. [#74](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/74) — Donor communication + retire `donate.thecrookedhouse.net`

Why move from PayPal to Zeffy: PayPal charges 2.2 % + $0.30 per donation; Zeffy charges 0 %. On $10 K raised, that's ≈ $275 more landing in The Crooked House account.

---

## For the owner

**Welcome.** You don't need to know any code or git to participate here. The FFC volunteer team handles the technical work; you only need to do a few things, mostly clicking links and granting access.

### What we need from you (one-time)

These are the things only **you** can do, because they require your IRS docs or your authorization:

- [ ] Validate The Crooked House's 501(c)(3) status with **TechSoup** or **Percent** ([#62](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/62))
- [ ] Sign up The Crooked House on **Google for Nonprofits** ([#62](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/62))
- [ ] Sign up The Crooked House on **Zeffy** and link the bank account that receives donations ([#70](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/70))
- [ ] Once Workspace + Zeffy + the Google products are set up, **add clarkemoyer@freeforcharity.org as an admin** on each ([#76](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/76)) — after that, FFC can manage everything without needing you on every call

### What decisions you'll be asked about

When you skim the issue trackers ([#69](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/69) and [#75](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/75)) you'll see a "Decisions for owner" section at the bottom of each. Examples:

- Should we replace PayPal entirely with Zeffy, or run both?
- Suggested donation amounts ($25 / $50 / $100 …) — keep defaults?
- How much access should the FFC team have on Workspace — delegated admin, or full Super Admin?
- Do you want Ad Grants pursued now or after the site has been live longer?

Skim them at your own pace; the team will ask in person when we get to each one.

### How to use this repo as a non-developer

- **Issues** are like a digital to-do list. Every project task lives in one. Click an issue link above to see what it is and where it stands.
- You can **comment** on any issue (button at the bottom) — questions, "yes go ahead", "I prefer X", anything.
- You can **subscribe** to an issue ("Subscribe" button on the right) to get an email whenever something happens on it.
- You don't need to write any code or use git. The FFC team handles all of that.
- Want a status update? Just open this `PROJECT.md` page on the repo's main page — it's the dashboard.

---

## For the FFC team

Quick reference links:

- Live site: <https://thecrookedhouse.net>
- Repo: <https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net>
- Open issues filtered by label:
  - [google-workspace](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues?q=is%3Aissue+label%3Agoogle-workspace+is%3Aopen)
  - [zeffy](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues?q=is%3Aissue+label%3Azeffy+is%3Aopen)
  - [integration](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues?q=is%3Aissue+label%3Aintegration+is%3Aopen)
- Deploy: GitHub Pages, runs automatically on every push to `main` (workflow: `.github/workflows/static.yml`)
- Cookie consent has hooks for GA4, GTM, Meta Pixel, Microsoft Clarity — just needs the IDs (see [#67](https://github.com/FreeForCharity/FFC-EX-thecrookedhouse.net/issues/67))

### Conventions

- Branches: `fix/<issue-number>-short-name`, `feat/<issue-number>-short-name`, `chore/...`, `docs/...`, `perf/...`
- Each PR closes one issue when possible
- Squash merge through the merge queue
- After each PR, verify on the live site before claiming done
- Update this `PROJECT.md` when status changes meaningfully

---

*This dashboard is maintained by hand — it isn't auto-generated. If it feels stale, ping the FFC team or update it directly.*
