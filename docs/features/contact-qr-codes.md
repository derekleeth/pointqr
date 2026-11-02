# Feature Plan: Contact QR Codes (vCard)

> Added: 2026-11-01
> Status: **In progress** (Phases 1-2 built; Phase 2 tested in desktop browsers, phone testing pending)
> Owner: Derek Leeth

## Overview

Let users create QR codes that share contact details. Scanning the code offers to save the contact straight to the phone's address book, so nobody has to type a name, number or email by hand.

Contact codes come in both of the existing QR types:

| Type | What the QR encodes | Editable after printing? | Scan analytics? |
|---|---|---|---|
| **Static** | The full vCard text, embedded in the code | No | No |
| **Dynamic** | `https://<redirect_base_url>/r/{short_code}`, which serves a hosted contact page with a "Save contact" (`.vcf`) button | Yes | Yes |

Dynamic contact codes count toward the user's `max_dynamic_qrs` tier limit ([limits.py](../../backend/app/limits.py)), the same as dynamic URL codes.

## Goals

- A structured contact form in the editor instead of hand-typing vCard text into the content box.
- A spec-compliant vCard that imports cleanly on iOS, Android, Outlook and Google Contacts.
- The live preview keeps working, and so do all current design options (colors, logo, labels, print sheet, exports).
- Dynamic contact codes can be edited and tracked the same way dynamic URL codes are.

## Non-Goals (for this iteration)

- Contact photos embedded in **static** codes (a base64 photo makes the code too dense to scan).
- Importing contacts from a phone, CSV or Google/Microsoft accounts.
- Other structured types (WiFi, SMS, email, calendar event). The data model below leaves room for them.
- Bulk/batch generation of contact codes (tracked as a stretch goal in Phase 5).

---

## Current State (what we're building on)

- `QRCode` ([models/qrcode.py](../../backend/app/models/qrcode.py)) has only `type` (STATIC/DYNAMIC), `target_url` and `design_config.content`. There's no concept of a content type.
- Dynamic codes always resolve through `GET /r/{short_code}` ([redirect.py](../../backend/app/api/v1/redirect.py)), which returns a 302 to `target_url` and caches the result for 60 s.
- [ContentPanel.vue](../../frontend/src/components/editor/ContentPanel.vue) is a single textarea. Its label already says "URL, text, vCard…", so users can paste raw vCard text today, but nothing helps them write it.
- Rendering: `qr-code-styling` on the frontend and `segno` on the backend. Both take an arbitrary string, but neither defaulted to UTF-8, so non-ASCII contact data needed a fix (see the Phase 2 log entry).
- The latest Alembic migration is `008_rename_enterprise_tier_to_max.py`.

---

## Design Decisions

### 1. Encoding format

- **Default: vCard 3.0.** It has the widest support on scanners and address books (iOS and Android both import it natively). vCard 4.0 support is less consistent and gives us nothing we need.
- **Optional: MECARD**, as a "compact" toggle for static codes. Its payload is much shorter, so the QR is less dense, but it supports fewer fields (no org/title on some readers).
- Encoding rules for vCard (these must be unit tested):
  - Lines end with CRLF (`\r\n`).
  - Escape `\` `,` `;` and newlines in text values.
  - Fold lines longer than 75 octets (counting UTF-8 bytes, not characters).
  - Always emit `N` and `FN`. `FN` is derived from the name parts when the user leaves it empty.
  - Omit empty properties completely. Never emit blank `TEL:` lines.

### 2. Data model

Add a content-type discriminator and a structured payload, instead of overloading `target_url`:

| Column | Type | Notes |
|---|---|---|
| `content_type` | enum `qrcontenttype`: `URL`, `TEXT`, `VCARD` | Default `URL`. Backfill existing rows as `URL`. Store uppercase values, as with `qrcodetype`. |
| `content_data` | JSONB, nullable | Structured fields for non-URL types (the contact fields for `VCARD`) |

For static vCard codes, `design_config.content` still holds the encoded vCard string, so the renderers and exporters work unchanged. The backend **regenerates** that string from `content_data` on create and update, so the two can't drift apart.

### 3. Contact fields (`ContactData` schema)

| Group | Fields |
|---|---|
| Name | `prefix`, `first_name`*, `last_name`, `suffix`, `display_name` (FN override) |
| Work | `organization`, `job_title` |
| Phones | list of `{ type: mobile \| work \| home \| fax \| other, number }`, max 5 |
| Emails | list of `{ type: work \| home \| other, address }`, max 3 |
| Web | `website` (URL), plus optional `social_links` list (dynamic only) |
| Address | `street`, `city`, `region`, `postal_code`, `country`, `type` (work/home) |
| Other | `note` (max 500 chars), `birthday` (date) |
| Dynamic only | `photo_url` (reuses the logo upload/storage path), `theme_color` for the hosted page |

\* At least one of `first_name`, `last_name`, `organization` is required.

### 4. Dynamic contact delivery

`/r/{short_code}` currently redirects every time. For `VCARD` codes it needs to branch:

- **`GET /r/{short_code}`** → a small hosted **contact landing page**: name, photo, tap-to-call / tap-to-email links, and a **Save contact** button. It's rendered server-side (a Jinja template or a static SPA route) so it loads fast on mobile without the full app bundle.
- **`GET /r/{short_code}.vcf`** (or `/r/{short_code}/vcard`) → `Content-Type: text/vcard; charset=utf-8`, `Content-Disposition: attachment; filename="<name>.vcf"`.
- The scan event fires on the landing page hit only, not on the `.vcf` download, so a scan isn't counted twice.
- The redirect cache value has to carry `content_type` too, so the branch can be decided without a DB hit.

Why a landing page rather than serving the `.vcf` directly: iOS Safari shows a contact preview for a `.vcf`, but Android Chrome often just downloads the file silently. A landing page behaves the same on every platform.

### 5. Privacy & safety

- Contact data is PII. Hosted contact pages send `X-Robots-Tag: noindex, nofollow`, and `/r/` stays out of `sitemap.xml` and is disallowed in `robots.txt`.
- An inactive code (`is_active = false`) returns 404 and doesn't show the contact data.
- Deleting a QR code removes its `content_data` with it (it's on the same row, so this is already true).
- Escape every field on the landing page (no raw HTML), and validate `website`/`social_links` as `http(s)` URLs only. That blocks `javascript:` links.

### 6. Scannability

- Show a **density meter** in the editor: payload byte length plus the estimated QR version at the current error correction level.
- Warn when the payload exceeds ~300 bytes at ECC `H`. Suggest dropping fields, lowering ECC (when there's no logo), switching to MECARD, or using a dynamic code. A dynamic code's payload is always a short URL.

---

## Implementation Phases & Progress

Legend: `[ ]` not started · `[~]` in progress · `[x]` done

### Phase 1: Backend foundation

- [x] Add `QRContentType` enum and `content_type` / `content_data` columns to `QRCode` model
- [x] Alembic migration `009_add_qr_content_type.py` (create enum, add columns, backfill `URL`, downgrade path)
- [x] `ContactData` Pydantic schemas with validation (phone/email/URL formats, list caps, at least one name field)
- [x] Add `content_type` + `content_data` to `QRCodeCreate`, `QRCodeUpdate`, `QRCodeRead`
- [x] `services/vcard.py`: `build_vcard(contact) -> str` and `build_mecard(contact) -> str`
- [x] Unit tests for the encoder: escaping, folding, CRLF, UTF-8 names, empty-field omission, FN derivation
- [x] On create/update of a static `VCARD` code, regenerate `design_config.content` from `content_data`
- [x] API tests in `tests/test_qrcodes.py` for create/update/read of static and dynamic contact codes

### Phase 2: Editor UI

- [x] Content type selector in `ContentPanel.vue` (URL / Text / Contact)
- [x] `ContactForm.vue` component (grouped, collapsible sections; repeatable phone/email rows)
- [x] Shared TS types + client-side vCard builder for live preview (mirrors `services/vcard.py`)
- [x] Extend `qrEditor` store with `contentType` / `contentData`; include them in `loadFromQRCode` / `resetToDefaults` / save
- [x] Density meter and too-dense warning
- [x] MECARD "compact" toggle (static only)
- [x] "Download .vcf" button in the editor so users can check the contact on their own phone
- [x] Dashboard: content-type icon/badge on QR cards and a filter

### Phase 3: Dynamic contact pages

- [ ] Carry `content_type` through the redirect cache; branch `/r/{short_code}` for `VCARD`
- [ ] Hosted contact landing page template (mobile-first, light/dark, uses `theme_color`)
- [ ] `.vcf` download endpoint with correct headers and filename sanitizing
- [ ] Optional contact photo upload (reuse logo upload limits & storage under `/storage/logos/`)
- [ ] `noindex` headers; confirm `robots.txt` / sitemap exclusions
- [ ] Scan event fires once per landing view, not on `.vcf` download
- [ ] Respect tier limits for dynamic contact codes
- [ ] Enable Dynamic for contact codes in `ContentPanel.vue` (`canBeDynamic`) and add "use a dynamic code" to the suggestions in `DensityMeter.vue`

### Phase 4: QA & device testing

- [ ] Scan-and-import matrix (see below) passes
- [ ] Exports (PNG/SVG/PDF/EPS) and print sheet work with vCard payloads
- [ ] Logo + ECC `H` + full contact still scans on the static path at 300 px and in print
- [ ] Accessibility pass on the contact form and landing page (labels, focus order, contrast)
- [ ] Test the contact form on real phones (reminder from Derek): layout and usability of the form fields, not just scanning
- [ ] Show the contact name instead of raw vCard text (`BEGIN:VCARD VERSI...`) in the dashboard download modal (`DownloadModal.vue`)
- [ ] Phone layout depends on the app shell work in [mobile-responsive-ui.md](mobile-responsive-ui.md); decide whether real-phone form testing waits for it

### Phase 5: Docs & launch

- [ ] Add the "Contact" use case to `HomeView.vue` and the product tour
- [ ] Document new fields in `APIDocsView.vue` / OpenAPI examples
- [ ] Update `docs/project-plan.md` schema table and `docs/changelog.md`
- [ ] Stretch: CSV batch import of contacts → zipped contact codes via `qr_batch` queue

---

## Device Test Matrix

| Scanner | Static vCard | Static MECARD | Dynamic (landing → Save) |
|---|---|---|---|
| iOS Camera (latest) | [ ] | [ ] | [ ] |
| Android, Google Lens / Camera | [ ] | [ ] | [ ] |
| Samsung Camera | [ ] | [ ] | [ ] |
| Import into Google Contacts (desktop) | [ ] | n/a | [ ] |
| Import into Outlook | [ ] | n/a | [ ] |

Test with a name that has accents (e.g. `José Ñúñez`), a comma in the organization, and a multi-line note.

---

## Open Questions

1. Should `TEXT` become its own content type in this work, or stay as "URL with non-URL content" the way it works today?
2. For the hosted contact page: server-rendered template from FastAPI, or a lightweight public route in the Vue SPA served by nginx?
3. Should a dynamic contact code be able to switch to a URL code later (and the reverse), or is `content_type` fixed once the code is created?
4. Is the photo on dynamic contact pages available on every tier, or Pro and up only?

## Progress Log

| Date | Update |
|---|---|
| 2026-11-01 | Plan created. |
| 2026-11-01 | Phase 1 done. `content_type` / `content_data` columns (migration 009), `ContactData` schemas, `services/vcard.py` (vCard 3.0 + MECARD), and the server now owns `design_config.content` for static contact codes. Choices made along the way: MECARD is selected with `content_data.encoding`; static codes reject `social_links` / `photo_url` / `theme_color` with a 422; contact codes always store `target_url = NULL`; for now, `PATCH` lets a code switch between URL and VCARD (open question 3 is still open). |
| 2026-11-01 | Phase 2 built: not yet tested in a browser. Choices made along the way: the editor only offers Dynamic for URL codes until Phase 3, because `/r/{short_code}` would send a dynamic contact code to an empty redirect; Static/Dynamic is locked once a code is saved, because the API ignores changes to it; `TEXT` is its own content type (open question 1), static only; the dashboard filter runs on the loaded rows, since the dashboard only loads the first 20. UTF-8 fix: `qr-code-styling` encoded each character as one byte and `segno` preferred Latin-1, so `toQRData` and `encoding="utf-8"` now produce UTF-8 in the preview, downloads, print sheet and server exports. |
| 2026-11-01 | Editor polish from local testing: a new contact code takes its title from the contact until the user types their own, and saved titles stay put. The form panel now gets 3/5 of the editor, with a 23rem minimum for the preview so the 300 px QR fits. Contact form rows wrap instead of overflowing. |
