# Feature Plan: Mobile & Responsive UI

> Added: 2026-11-01
> Status: **In progress** (Phase 1 done 2026-11-06)
> Owner: Derek Leeth

## Overview

Make the signed-in app usable on phones. Public pages already hold up at phone width, but every page that uses `AppLayout` is close to unusable there, because the sidebar stays open at 240 px on any screen size and takes about 60% of a 390 px phone.

Fixing the sidebar comes first. It is the biggest problem, and it changes how much room everything else has, so several other items need rechecking afterward.

## Goals

- Every signed-in page is usable at 360-430 px wide, without first having to find the collapse button.
- Users can reach all navigation on a phone, including admin pages.
- Creating a QR code on a phone works from start to finish, including seeing the preview.
- Desktop layouts stay as they are.

## Non-Goals (for this iteration)

- A native app or PWA install.
- Redesigning pages beyond what small screens need.
- Shortening the landing page (it is 11,420 px tall on a phone and 6,312 px on desktop, which is long but works).

## How This Was Tested

Audited on 2026-11-01 against the local Docker stack, with Playwright driving headless Edge in device emulation (iPhone 13, Pixel 5, iPad Mini). All 18 routes were loaded on the iPhone and iPad profiles (Pixel covered 10 of them) and measured for overflow, field widths, tap target sizes and input font sizes. The test account was made an admin for the run and changed back afterward.

**What this doesn't cover:**

- Emulation uses Chromium, not Safari, so iOS-specific behavior is unverified. Items marked *(unverified)* need a real device.
- The on-screen keyboard, landscape orientation and real touch use.
- Analytics charts with real data (the test account has no scans). The empty state looks fine.
- Screens checked by measurement only, not by eye: auth pages, API keys, settings, feedback and the admin settings, monitor and feedback pages.

## Findings

### Critical

| # | Problem | Evidence | Where |
|---|---|---|---|
| 1 | The sidebar stays open at 240 px on every screen size. There is no media query, no drawer and no menu button. | At 390 px the content area is 150 px, the editor form is 118 px and the first name field is 26 px. | [AppSidebar.vue](../../frontend/src/components/sidebar/AppSidebar.vue), [AppLayout.vue](../../frontend/src/layouts/AppLayout.vue), `--sidebar-w` in [main.css](../../frontend/src/assets/main.css) |

Collapsing it by hand helps a lot: the sidebar drops to 64 px and the content area grows to 326 px. Most pages then become readable, but a first-time phone user has to find a 24 px button first. Collapsed is still a permanent rail taking 16% of the screen.

### High

| # | Problem | Evidence | Where |
|---|---|---|---|
| 2 | Wide tables hide their right-hand columns on phones. They scroll sideways, but nothing signals that, and the Actions column starts off screen. Tapping a dashboard row still opens the download modal, but edit and delete are hard to reach. | With the sidebar collapsed: dashboard 634 px in a 294 px container, admin users 757 px in 244 px, admin feedback 798 px in 244 px. | `DashboardView.vue`, `AdminUsersView.vue`, `AdminFeedbackView.vue`, `AdminMonitorView.vue` |
| 3 | On phones the live preview sits below the entire form, so you can't see the QR change while typing. Save is at the top of the page and the download buttons are at the bottom. | The editor grid drops to one column below 1024 px. | `QREditorView.vue` |
| 4 | Nested padding squeezes the contact form. Page, tab panel and accordion padding leave about 189 px for fields, even with the sidebar collapsed, so a phone row's remove (X) button wraps onto its own line. | First and last name fields are 89 px wide. Recheck after #1, which should add about 64 px. | `ContactForm.vue`, `QREditorView.vue` |

### Medium

| # | Problem | Evidence | Where |
|---|---|---|---|
| 5 | Tap targets are too small, against the usual 44 px guideline. | Sidebar toggle 24x24, collapsed nav items 47x32, Light mode and Logout 31 px tall. | `AppSidebar.vue` |
| 6 | The QR preview is a fixed 300 px and barely fits a phone. Its frame fills the whole content area and overruns the card's padding. | At 150 px of content the canvas overflows its card by 91 px; collapsed, it only just fits. | `QRCanvas.vue` (`width: 300`) |
| 7 | The landing page header is crowded at 390 px. "Log in" and "Get Started" each wrap to two lines, and "Get Started" touches the screen edge. | Seen in the iPhone 13 screenshot. | `HomeView.vue` |
| 8 | Admin nav items get cut off in the collapsed sidebar on short screens. | The admin icon is clipped by the footer section at 664 px tall. Check whether it scrolls; #1 may make this moot. | `AppSidebar.vue` |
| 9 | Admin search fields use text under 16 px, which makes iOS Safari zoom the page on focus *(unverified)*. Every other input measured is at least 16 px. | One field each on admin users and admin feedback. | `AdminUsersView.vue`, `AdminFeedbackView.vue` |
| 10 | `AppLayout` uses `height: 100vh`, which can put the bottom of the page behind the mobile browser's address bar *(unverified)*. This would hide Logout. `100dvh` is the usual fix. | From reading the code, not seen in emulation. | [AppLayout.vue:25](../../frontend/src/layouts/AppLayout.vue#L25) |

### Other bugs found along the way

| # | Problem | Evidence | Where |
|---|---|---|---|
| 11 | **Dev only:** loading or refreshing `/api-keys` or `/api-docs` directly returns a 500. The Vite proxy key `/api` is a prefix match, so it catches these app routes too. Production looks unaffected from reading the nginx config, which matches `/api/`, but that wasn't tested. | Confirmed with curl: both return 500 while `/settings` returns 200, and the Vite log shows `ECONNREFUSED`. | [vite.config.ts:63](../../frontend/vite.config.ts#L63), use `^/api/` |
| 12 | **Unconfirmed:** one uncaught `Cannot read properties of null (reading 'ce')` while navigating to `/admin/users` on the emulated iPhone. It didn't recur on the iPad run or in a later sweep of non-admin pages, and may be a race from how fast the test navigates. | Seen once. Try to reproduce before spending time on it. | Unknown |

### Already fine

- Public and auth pages have no sideways overflow at phone width.
- No page scrolls sideways at the document level, even at the worst sizes.
- The download modal fits a phone (351 px wide on a 390 px screen) and stays usable.
- Tablet (768 px) is workable, with no fields cut off, though the sidebar still takes 240 px and tables scroll.

## Implementation Phases & Progress

### Phase 1: App shell

The prerequisite for everything else.

- [x] Below 768 px, replace the sidebar with an off-canvas drawer and a top bar with a menu button
- [x] Close the drawer on navigation, on tapping outside it and with Escape; trap focus while it's open
- [x] Decide the 768-1024 px behavior (see open question 2): a fixed 64 px rail; its expand button opens the full sidebar as an overlay, which closes the same way as the drawer
- [x] Keep the saved desktop collapse preference separate from the drawer state, so using a phone doesn't change it
- [x] Use `100dvh` in `AppLayout` (#10), with a `100vh` fallback. Still needs a real-device check
- [x] Bring sidebar and drawer tap targets to 44 px (#5). Desktop with a mouse keeps the compact rows; touch devices (`pointer: coarse`) get 44 px everywhere. The desktop collapse button keeps its 24 px look but has a 44 px hit area
- [x] Recheck #4, #6 and #8 and close any this resolves (see the Phase 1 recheck below)

**Phase 1 recheck (2026-11-06, emulated, mocked API):**

- **#8 resolved.** Admin items scroll into view in the tablet rail (checked at 768x1024 and 1024x768) and in the phone drawer. On phones the whole drawer now scrolls as one column, so the footer no longer squeezes the nav.
- **#4 partly resolved.** The content area is now the full screen width (360/390 px). First and last name fields are 106/121 px (were 89 px), and the phone row's remove button stays on the same line. The nested padding is still there, so Phase 2's padding item stays open.
- **#6 not resolved.** The QR preview frame is 332 px (300 px canvas plus padding), which still overruns the card's padding at 390 px and sticks out about 2 px past the card's edges at 360 px. Still a Phase 2 item.

### Phase 2: Editor on phones

- [ ] Make the preview visible while editing (see open question 3) (#3)
- [ ] Make the QR preview scale down to its container, while keeping exports at full size (#6)
- [ ] Reduce nested padding at phone width and keep the remove button on the same line as its field (#4)
- [ ] Check the Design tab, color pickers and sliders by touch
- [ ] Check the on-screen keyboard doesn't hide the field being typed in

### Phase 3: Tables

- [ ] Dashboard: choose a phone layout (see open question 4) and keep edit and delete reachable (#2)
- [ ] Apply the same approach to admin users, feedback and monitor, if admin is in scope (see open question 1)

### Phase 4: Polish

- [ ] Fix the landing page header at 360-430 px (#7)
- [ ] Use 16 px text in the admin search fields (#9)
- [ ] Recheck tap targets across the remaining pages

### Phase 5: QA

- [ ] Rerun the audit at 360, 390, 430 and 768 px, and at desktop widths to confirm no change
- [ ] Test on a real iPhone (Safari) and a real Android phone, including the *(unverified)* items
- [ ] Test landscape

### Quick fixes (any time)

- [ ] Fix the Vite proxy prefix (#11). A one-line, dev-only change that doesn't need to wait for the rest of this plan
- [ ] Try to reproduce the `ce` error (#12)

## Open Questions

1. Should admin pages get the full mobile treatment, or is "reachable and not broken" enough? Recommendation: the latter, since admins will mostly use a desktop.
2. ~~Between 768 and 1024 px, should the sidebar use the drawer or default to the 64 px rail?~~ **Decided 2026-11-06:** the rail, since tablets have room for it.
3. How should the phone editor show the preview: a sticky mini preview, a Form/Preview toggle, or a floating button that opens it? Recommendation: a Form/Preview toggle, since it's the simplest and a 300 px QR won't fit beside a form anyway.
4. Should dashboard tables become cards on phones, or hide columns? Recommendation: cards for the dashboard, since it's the main screen, and sideways scrolling with a visible cue for admin tables.

## Progress Log

| Date | Update |
|---|---|
| 2026-11-01 | Plan created from an emulated-device audit of all routes. No fixes made yet. |
| 2026-11-06 | Phase 1 done. Drawer below 768 px, rail with overlay at 768-1024 px, desktop unchanged. Checked with Playwright (headless Edge, mocked API) at 360, 390, 768, 1024 and 1440 px: drawer open/close, Escape, tap outside, close on navigation, focus trap and focus return, 44 px targets, saved preference untouched on phone/tablet. Not yet tried on a real phone. |
