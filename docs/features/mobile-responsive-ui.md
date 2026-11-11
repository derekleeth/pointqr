# Feature Plan: Mobile & Responsive UI

> Added: 2026-11-01
> Status: **In progress** (Phases 1 and 2 done 2026-11-06, Phases 3 and 4 done 2026-11-10; real-device QA left)
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
| 11 | **Fixed 2026-11-10. Dev only:** loading or refreshing `/api-keys` or `/api-docs` directly returns a 500. The Vite proxy key `/api` is a prefix match, so it catches these app routes too. Production looks unaffected from reading the nginx config, which matches `/api/`, but that wasn't tested. | Confirmed with curl: both return 500 while `/settings` returns 200, and the Vite log shows `ECONNREFUSED`. | [vite.config.ts:63](../../frontend/vite.config.ts#L63), use `^/api/` |
| 12 | **Fixed 2026-11-10 (dev only, see Quick fixes):** one uncaught `Cannot read properties of null (reading 'ce')` while navigating to `/admin/users` on the emulated iPhone. It didn't recur on the iPad run or in a later sweep of non-admin pages, and may be a race from how fast the test navigates. | Seen once. Try to reproduce before spending time on it. | Unknown |

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

- [x] Make the preview visible while editing (see open question 3) (#3). Below 1024 px, where the editor is one column, a sticky bar has an Edit/Preview switch and Save, so Save is reachable from anywhere in the form and the downloads sit right under the preview. Each side keeps its own scroll position, and the form keeps its open tab. At 1024 px and up nothing changes
- [x] Make the QR preview scale down to its container, while keeping exports at full size (#6). The on-screen copy shrinks with CSS `zoom`; the 300 px instance that downloads read from is unchanged (PNG export checked at 300x300 at every width)
- [x] Reduce nested padding at phone width and keep the remove button on the same line as its field (#4). Below 640 px the tab and accordion padding drop to 12 px a side. In phone, email and link rows the field and its X are grouped, so when the row wraps the type select moves to its own line and the X stays with its field
- [x] Check the Design tab, color pickers and sliders by touch. On touch devices (`pointer: coarse`) color swatches and the small B / I / alignment buttons are 44 px, and slider handles keep their look but have a 44 px grab area. Checked by emulation only
- [ ] Check the on-screen keyboard doesn't hide the field being typed in. Needs a real phone. Added `interactive-widget=resizes-content` to the viewport meta so Android Chrome shrinks the app shell above the keyboard instead of overlaying it; iOS ignores this and pans to the field itself

**Phase 2 check (2026-11-06, emulated, mocked API, 360/390/430/768 px touch and 1024/1440 px mouse):**

- **#3 resolved.** Switch shows below 1024 px only and stays pinned to the top of the scroll area; switching back to Edit returns to the same scroll position and tab.
- **#4 resolved.** First and last name fields are 134/149/169 px at 360/390/430 (were 106/121 px). The remove button stays on its field's line at every width.
- **#6 resolved.** Preview is 272 px at 360 and full 300 px from 390 up, with no overrun of the card's padding at any width. This also fixes a smaller overrun at exactly 1024 px, where the two-column preview card was too narrow for the 332 px frame.

### Phase 3: Tables

- [x] Dashboard: choose a phone layout (see open question 4) and keep edit and delete reachable (#2). Below 768 px (the same breakpoint as the drawer) the table becomes a list of cards. Each card shows the content-type icon, title, content type and date, the Static/Dynamic tag, the scan count, and 44 px Download, Edit and Delete buttons. Tapping the top of a card opens the download modal, like tapping a table row. Cards can't use sortable headers, so phones get a sort menu (Newest, Oldest, Name, Most scans) next to the content filter. From 768 px up the table stays, with its Actions column pinned to the right
- [x] Apply the same approach to admin users, feedback and monitor, if admin is in scope (see open question 1). Admin tables keep sideways scrolling, with a visible cue: a new `v-scroll-cue` directive fades whichever edge has hidden columns. Admin users and feedback pin their Actions column to the right, so the actions are always on screen and the fade sits just left of them. Monitor has no actions and gets the fade only. On phones the admin pages drop their extra page padding (the app shell already pads), the search box takes a full row, and admin dialogs fit the screen (also the API keys dialogs)

**Phase 3 check (2026-11-10, emulated, mocked API):**

- **#2 resolved.** Dashboard shows cards at 360/390/430 px, and the table at 768 px and up with Actions on screen. Sort, Edit (opens `/editor/:id`) and tapping a card (opens the download modal) all work. Admin users (799 px table) and admin feedback (856 px) keep Actions visible in a 326 px container, the right fade shows until you scroll to the end, and then the left fade shows instead.

### Phase 4: Polish

- [x] Fix the landing page header at 360-430 px (#7). Header buttons no longer wrap. Below 640 px the version badge and the GitHub icon are hidden (GitHub is still in the footer) and spacing is tighter, so the brand, theme toggle, Log in and Get Started fit on one line at 360 px. The same header on the Developers page gets the same fix
- [x] Use 16 px text in the admin search fields (#9). Applies on phones and touch devices, so iPads are covered too
- [x] Recheck tap targets across the remaining pages. On touch devices (`pointer: coarse`), PrimeVue buttons, inputs, selects, select options, toggle buttons and toast close buttons get a 44 px minimum, and icon-only buttons get 44x44. Landing and Developers page buttons, tabs and footer links get the same. A `touch-target` class covers one-off links (used on the API keys page's docs link). Mouse users keep the compact sizes

**Phase 4 check (2026-11-10, emulated, mocked API, 360/390/430/768 px touch and 1024/1440 px mouse):**

- **#7 resolved.** Header is one line at 360/390/430 px with 44 px buttons, and nothing reaches the screen edge.
- **#9 resolved.** No input under 16 px on any page at phone width.
- **Tap targets:** all buttons and inputs are at least 44 px on touch. What's still smaller is inline text links inside paragraphs, a link inside admin table cells and the inner label of PrimeVue selects (the select itself is 44 px).
- **Desktop unchanged:** screenshots at 1024 and 1440 px are pixel-identical before and after on the landing, Developers, settings and monitor pages. The dashboard and admin table pages show no visible difference; the byte-level difference comes from the pinned Actions column.
- No page scrolls sideways at the document level at any width checked.

### Phase 5: QA

- [ ] Rerun the audit at 360, 390, 430 and 768 px, and at desktop widths to confirm no change
- [ ] Test on a real iPhone (Safari) and a real Android phone, including the *(unverified)* items
- [ ] Test landscape

### Quick fixes (any time)

- [x] Fix the Vite proxy prefix (#11). The proxy key is now the regex `^/api/`. Checked with curl: `/api-keys` and `/api-docs` return 200, and `/api/v1/...` is still proxied (the Vite log shows it forwarded as `/v1/...`)
- [x] Try to reproduce the `ce` error (#12). It recurred once, at 360 px on `/admin/users`, on a freshly started dev server. The Vite log showed that, at that moment, it was optimizing `primevue/iconfield` and `primevue/inputicon` (used by the admin search box) and reloading the page. A reload mid-render can leave modules from two dependency builds loaded together, which gives this Vue null-instance error. It never happened again in 40+ further sweeps on a warm server. Fix: added the six PrimeVue packages the app uses but `optimizeDeps.include` was missing (divider, iconfield, inputicon, message, skeleton, textarea). With the dep cache cleared, a sweep of every route, signed in and out, triggered no optimizer reloads and no errors. Dev only; production builds are bundled ahead of time

## Open Questions

1. ~~Should admin pages get the full mobile treatment, or is "reachable and not broken" enough?~~ **Decided 2026-11-10:** reachable and not broken, as recommended: sideways scrolling with a fade cue and a pinned Actions column.
2. ~~Between 768 and 1024 px, should the sidebar use the drawer or default to the 64 px rail?~~ **Decided 2026-11-06:** the rail, since tablets have room for it.
3. ~~How should the phone editor show the preview: a sticky mini preview, a Form/Preview toggle, or a floating button that opens it?~~ **Decided 2026-11-06:** a Form/Preview toggle, as recommended, in a sticky bar with Save.
4. ~~Should dashboard tables become cards on phones, or hide columns?~~ **Decided 2026-11-10:** cards for the dashboard below 768 px, and sideways scrolling with a visible cue for admin tables.

## Progress Log

| Date | Update |
|---|---|
| 2026-11-01 | Plan created from an emulated-device audit of all routes. No fixes made yet. |
| 2026-11-06 | Phase 1 done. Drawer below 768 px, rail with overlay at 768-1024 px, desktop unchanged. Checked with Playwright (headless Edge, mocked API) at 360, 390, 768, 1024 and 1440 px: drawer open/close, Escape, tap outside, close on navigation, focus trap and focus return, 44 px targets, saved preference untouched on phone/tablet. Not yet tried on a real phone. |
| 2026-11-06 | Phase 2 done, except the on-screen keyboard check, which needs a real phone. Edit/Preview switch below 1024 px, preview scales to fit, phone padding trimmed, 44 px touch targets in the editor. Checked with Playwright (headless Edge, mocked API) at 360, 390, 430, 768, 1024 and 1440 px. |
| 2026-11-10 | Phases 3 and 4 done. Dashboard cards on phones; admin tables scroll sideways with a fade cue and pinned Actions; landing header fixed; 16 px admin search; 44 px touch targets app-wide. Checked with Playwright (headless Edge, mocked API) at 360, 390, 430, 768, 1024 and 1440 px, including a before/after screenshot comparison at desktop widths. Not yet tried on a real phone. |
| 2026-11-10 | Quick fixes done. Vite proxy no longer catches `/api-keys` and `/api-docs` (#11). The `ce` error (#12) traced to Vite's dependency optimizer reloading mid-navigation, fixed by pre-bundling the missing PrimeVue packages. |
