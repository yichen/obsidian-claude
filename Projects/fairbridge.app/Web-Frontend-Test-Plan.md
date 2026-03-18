# FairBridge Web Frontend Test Plan

**Document Owner**: frontend-tester
**Version**: 1.0
**Date**: 2026-03-17
**Status**: Draft — awaiting coordination input from web-dev and ux-engineer

---

## Executive Summary

This document specifies the complete web frontend test plan for FairBridge.app. FairBridge is a co-parenting expense tracking and ACH payment application built on React (web) with Stripe Connect and Financial Connections. The web frontend serves two distinct roles: (1) subscription purchase (to avoid Apple IAP 30% cut), and (2) full onboarding and management flows accessible via browser.

Testing is organized around the product's three MVP pillars — ACH payments, append-only expense tracking with SHA-256 hash chain, and custody calendar — plus critical cross-cutting concerns: domestic violence (DV) safety defaults, accessibility (WCAG 2.1 AA), cross-browser compatibility, and responsive layout. Every test area maps to a specific user-facing risk or regulatory requirement. Tests are written so that web-dev and ux-engineer can use them as acceptance criteria during implementation.

---

## 1. Test Environment and Infrastructure

### 1.1 Browser Matrix

All functional tests must pass on the following matrix (latest two stable versions of each):

| Browser | Versions | Platform |
|---------|----------|----------|
| Chrome | 133, 132 | Windows 11, macOS 15 |
| Safari | 18, 17 | macOS 15, iOS 18 (mobile web) |
| Firefox | 135, 134 | Windows 11, macOS 15 |
| Edge | 133, 132 | Windows 11 |

**Mobile web** (Safari on iOS 18, Chrome on Android 14) is required for responsive breakpoint tests. Mobile web is not a substitute for the native apps but must provide a degraded-graceful experience for payee invite link recipients who open the link on a device without the app installed.

### 1.2 Responsive Breakpoints

| Breakpoint | Width | Target Device Class |
|------------|-------|---------------------|
| Mobile | 375px–767px | iPhone 15, Pixel 8 |
| Tablet | 768px–1023px | iPad Air, Surface Pro |
| Desktop | 1024px+ | MacBook, PC |

### 1.3 Test Data Strategy

- **Stripe test mode**: All payment tests use Stripe test API keys and test card/bank numbers. No real ACH transactions are initiated.
- **Stripe test bank accounts**: Use Financial Connections test institution `stripe_bank_account_xxxxx` tokens.
- **Two-account pairing**: Tests require two registered accounts (payer + payee) with separate browser sessions or incognito windows.
- **Seeded test users**: Maintain a fixture set of confirmed payer-payee pairs in the staging environment.
- **PDF hash verification**: Tests capture the SHA-256 hash embedded in the exported PDF and verify it against the API response.

### 1.4 Tooling

| Layer | Tool |
|-------|------|
| E2E automation | Playwright (multi-browser, cross-origin iframe support for Stripe) |
| Component / unit | React Testing Library + Vitest |
| Accessibility | axe-core (automated) + manual screen reader (NVDA/JAWS on Windows, VoiceOver on macOS/iOS) |
| Visual regression | Playwright screenshots + Percy or Chromatic |
| Performance | Lighthouse CI (run on each PR) |
| Contract testing | MSW (Mock Service Worker) for API boundary tests |

---

## 2. Onboarding Flow Tests

Onboarding is the highest-risk user journey. The payee path ("money waiting") is the primary acquisition funnel and must convert at >50%. Each step below maps to a screen transition; tests verify both the happy path and every divergence point.

### 2.1 Payer Signup

**TC-ONB-001: Email signup — valid email**
- Action: Submit signup form with valid email + password (≥8 chars, 1 uppercase, 1 number)
- Expected: Account created, verification email sent, user lands on "Check your email" screen
- Verify: No PII in URL query params; auth token stored in httpOnly cookie, not localStorage

**TC-ONB-002: Email signup — duplicate email**
- Action: Submit with an email already registered
- Expected: Error message "An account with this email already exists" displayed inline (not as a toast that auto-dismisses)
- Verify: No account creation; no email sent

**TC-ONB-003: Email signup — invalid email format**
- Action: Submit `notanemail` as email
- Expected: Inline validation error before form submission (client-side)
- Verify: Network request not sent

**TC-ONB-004: Password strength indicator**
- Action: Type passwords of varying strength
- Expected: Visual strength indicator updates in real time; form submit disabled until minimum strength met

**TC-ONB-005: Email verification link**
- Action: Click verification link from email
- Expected: User lands on app, sees "Email verified" confirmation, proceeds to co-parent pairing step
- Verify: Link is single-use; second click shows "Link already used" error

**TC-ONB-006: Expired verification link**
- Action: Click verification link after 24-hour expiry
- Expected: User sees "Link expired" screen with "Resend verification email" button
- Verify: Resend button sends new email; previous link no longer works

**TC-ONB-007: Google OAuth signup**
- Action: Click "Continue with Google"
- Expected: OAuth popup opens; on success, user is signed up and lands on co-parent pairing
- Verify: Popup does not trigger popup blocker warnings on Chrome/Safari

**TC-ONB-008: Co-parent pairing — asymmetric child verification**
- Action: Payer enters child's first name and date of birth; payee independently enters the same
- Expected: System matches on both entries; pairing confirmed
- Verify: Neither parent can see the other's raw entry before match; mismatch shows generic "Verification failed" without revealing which field mismatched (security requirement)

**TC-ONB-009: Co-parent pairing — mismatch**
- Action: Payer enters "Laurence", DOB 2017-11-09; payee enters "Lawrence", DOB 2017-11-09
- Expected: Pairing fails with "Child information did not match — please check the spelling and date of birth" message
- Verify: No account lockout on single mismatch; three consecutive mismatches trigger a 15-minute cooldown

**TC-ONB-010: Co-parent notification permission gate**
- Action: Complete pairing step
- Expected: Notification permission prompt is shown before proceeding to dashboard; user can skip but sees warning that payment alerts require notifications

### 2.2 Payee Invite Landing Page ("Money Waiting")

The payee invite is the single most important conversion surface. A payer sends an invite link; the payee lands on a page that communicates there is money waiting for them. Every word of friction costs conversion.

**TC-ONB-020: Invite landing page — renders from email link**
- Action: Click invite link from "money waiting" email (format: `app.fairbridge.co/invite/[token]`)
- Expected: Landing page renders within 2 seconds; shows payer's first name, dollar amount pending, "Claim your money" CTA
- Verify: Payer's last name and full financial details are NOT shown on pre-auth page (privacy)

**TC-ONB-021: Invite token validation**
- Action: Visit invite link with valid token
- Expected: Page renders with personalized content
- Action: Mutate one character in token
- Expected: "Invalid or expired invite link" page with "Ask [payer name] to resend" message

**TC-ONB-022: Invite token expiry (7 days)**
- Action: Visit invite link more than 7 days after creation
- Expected: "This invite has expired" page; no ability to proceed without a new link

**TC-ONB-023: Payee signup from invite — minimal friction path**
- Action: On invite landing page, click "Claim your money"; complete signup (email + password); complete co-parent child verification
- Expected: User arrives at bank linking step (Stripe Financial Connections) within 3 screens from landing page click
- Verify: Step count is ≤3 (landing → signup → bank linking); no unnecessary intermediate screens

**TC-ONB-024: Payee signup — existing account**
- Action: Click invite link; enter email of an existing account
- Expected: "Sign in" form is shown (not "already registered" error); after sign-in, existing account is linked to the payer

**TC-ONB-025: Invite link opened on mobile without app installed**
- Action: Open invite link on iOS Safari without FairBridge app installed
- Expected: Mobile-responsive web landing page renders correctly; "Claim your money" CTA works in mobile browser; optional App Store link displayed below primary CTA

**TC-ONB-026: Invite link opened with app installed (deep link)**
- Action: Open invite link on iOS with app installed
- Expected: App opens directly to invite acceptance screen (universal link behavior); web page is not shown

**TC-ONB-027: "Money waiting" email click-through — tracking pixel not leaking activity**
- Action: Open email, click link
- Expected: No activity timestamp or read-receipt metadata is exposed in any DOM element, URL param, or API response visible to the payer
- Verify: Payer cannot determine whether the email was opened (DV safety requirement)

### 2.3 Subscription Purchase Flow

Subscriptions are purchased on web only (not in-app, to avoid Apple IAP 30% fee).

**TC-ONB-030: Subscription page renders**
- Action: Navigate to `/subscribe`
- Expected: Plan options displayed (monthly / annual); pricing shown; Stripe Checkout button visible

**TC-ONB-031: Stripe Checkout — successful purchase**
- Action: Click "Subscribe"; complete Stripe Checkout with test card `4242 4242 4242 4242`
- Expected: User redirected to success URL; subscription record created; app unlocks premium features
- Verify: Stripe `checkout.session.completed` webhook processed; subscription status in UI updates without page refresh (or within one refresh)

**TC-ONB-032: Stripe Checkout — declined card**
- Action: Complete Stripe Checkout with test card `4000 0000 0000 0002` (generic decline)
- Expected: Stripe Checkout displays "Your card was declined"; user can retry; not redirected to app
- Verify: No subscription record created in database

**TC-ONB-033: Stripe Checkout — 3D Secure authentication**
- Action: Complete checkout with `4000 0025 0000 3155` (3DS required card)
- Expected: 3DS authentication modal appears; on completion, subscription succeeds
- Verify: User lands on success URL; subscription active

**TC-ONB-034: Subscription already active — revisit subscribe page**
- Action: Authenticated user with active subscription navigates to `/subscribe`
- Expected: "You already have an active subscription" with link to manage billing (Stripe Customer Portal)

**TC-ONB-035: Stripe Customer Portal — cancel subscription**
- Action: Navigate to billing management; click "Cancel subscription"
- Expected: Stripe Customer Portal opens; cancellation scheduled for end of billing period; user sees "Subscription ending [date]" in app

---

## 3. Expense Submission Tests

### 3.1 Form Validation

**TC-EXP-001: Amount — empty field**
- Action: Submit expense form with amount field blank
- Expected: Inline error "Amount is required"; form not submitted

**TC-EXP-002: Amount — below $5 minimum**
- Action: Enter $4.99
- Expected: Inline error "Minimum expense amount is $5.00"

**TC-EXP-003: Amount — exactly $5.00 (boundary)**
- Action: Enter $5.00
- Expected: Form accepts; no validation error

**TC-EXP-004: Amount — non-numeric input**
- Action: Type "abc" in amount field
- Expected: Input rejects non-numeric characters; field remains empty or shows only valid characters

**TC-EXP-005: Amount — large value**
- Action: Enter $99,999.99
- Expected: Form accepts; verify no integer overflow in display or submission

**TC-EXP-006: Description — empty field**
- Action: Submit with description blank
- Expected: Inline error "Description is required"

**TC-EXP-007: Description — 500 character limit**
- Action: Type exactly 500 characters
- Expected: Field accepts all 500 characters; character counter shows "500/500"
- Action: Type 501st character
- Expected: Input blocked; counter stays at "500/500"

**TC-EXP-008: Description — 499 characters (boundary)**
- Action: Type 499 characters
- Expected: Character counter shows "499/500"; submit succeeds

**TC-EXP-009: Category selection — required**
- Action: Submit without selecting a category
- Expected: Inline error "Please select a category"

**TC-EXP-010: Date — defaults to today**
- Action: Open expense form
- Expected: Date field pre-populated with today's date in user's local timezone

**TC-EXP-011: Date — future date**
- Action: Select a date 30 days in the future
- Expected: Warning shown ("Future expense — are you sure?"); submit still allowed

**TC-EXP-012: Receipt photo upload — valid image**
- Action: Upload a JPEG under 10MB
- Expected: Image preview renders; filename shown; upload progress indicator completes
- Verify: Image stored in R2; URL returned in API response

**TC-EXP-013: Receipt photo upload — file too large**
- Action: Upload a 15MB JPEG
- Expected: Error "File must be under 10MB"; file not uploaded; form still submittable without receipt

**TC-EXP-014: Receipt photo upload — invalid file type**
- Action: Upload a .exe file
- Expected: Error "Only JPG, PNG, and PDF files are accepted"

**TC-EXP-015: Split percentage — default 50/50**
- Action: Open expense form
- Expected: Split defaults to 50% payer / 50% payee

**TC-EXP-016: Split percentage — custom split**
- Action: Set split to 70/30
- Expected: Both fields update; payer amount and payee amount preview updates in real time

**TC-EXP-017: Split percentage — values must sum to 100**
- Action: Set payer to 60, payee to 30 (sum = 90)
- Expected: Inline error "Percentages must add up to 100%"

**TC-EXP-018: External payment flag**
- Action: Check "Paid externally (Venmo/Zelle/check/cash)"; select payment method; enter reference note
- Expected: Expense marked as external; no ACH payment initiated; record shows external payment method

**TC-EXP-019: Append-only constraint — no edit button shown**
- Action: View a submitted expense
- Expected: No "Edit" button present in DOM (not just hidden — must be absent)
- Verify: Direct API call to edit endpoint returns 405 Method Not Allowed or 403 Forbidden

**TC-EXP-020: Hash chain integrity — hash displayed on expense detail**
- Action: Open expense detail view
- Expected: SHA-256 hash of the expense record is displayed; "Verify integrity" tooltip/link explains what it means
- Verify: Displayed hash matches the hash returned by GET /expenses/:id

### 3.2 Expense List and History

**TC-EXP-030: Expense list — pending expenses shown first**
- Action: View expense list with mix of pending and settled expenses
- Expected: Pending expenses appear at top; settled below; clear visual distinction

**TC-EXP-031: Expense list — infinite scroll or pagination**
- Action: Scroll to bottom of expense list with >20 items
- Expected: Next page loads automatically (or pagination controls work); no layout shift on load

**TC-EXP-032: Expense list — filter by status**
- Action: Apply filter "Pending"
- Expected: Only pending expenses shown; count matches badge on tab

**TC-EXP-033: Expense list — filter by date range**
- Action: Select date range January 2026 — March 2026
- Expected: Only expenses in that range shown; expenses outside range not visible

---

## 4. Two-Party Confirmation Flow Tests

### 4.1 Approve Flow

**TC-CONF-001: Payee receives notification of new expense**
- Action: Payer submits expense; check payee's notification inbox
- Expected: In-app notification appears within 60 seconds; email notification within 15 minutes of push failure

**TC-CONF-002: Payee approves expense**
- Action: Payee clicks "Approve" on expense confirmation screen
- Expected: Expense status changes to "Approved"; payer notified; payment initiation offered if bank linked

**TC-CONF-003: Approve — confirmation dialog**
- Action: Click "Approve"
- Expected: Confirmation modal "Approve this $X.XX expense for [description]?" with Cancel and Confirm buttons; accidental tap protection

**TC-CONF-004: Payment initiation after approval**
- Action: Payee approves expense; payee has bank linked
- Expected: "Initiate payment" button appears; clicking initiates ACH transfer; status updates to "Payment pending"

**TC-CONF-005: Payment initiation — bank not linked**
- Action: Payee approves expense; payee has no bank linked
- Expected: Prompt to link bank via Stripe Financial Connections; after successful linking, payment initiation proceeds

### 4.2 Dispute Flow

**TC-CONF-010: Payee disputes expense**
- Action: Payee clicks "Dispute" on expense
- Expected: Dispute form opens with required "Reason" field (dropdown: incorrect amount / not my responsibility / duplicate / other) and optional explanation text area

**TC-CONF-011: Dispute — reason required**
- Action: Submit dispute with reason field empty
- Expected: Inline error "Please select a reason for the dispute"

**TC-CONF-012: Dispute submitted — payer notified**
- Action: Payee submits dispute
- Expected: Expense status changes to "Disputed"; payer receives notification; dispute reason and explanation visible to payer

**TC-CONF-013: Payer responds to dispute — counter-evidence**
- Action: Payer opens disputed expense; uploads counter-evidence (receipt); adds explanation
- Expected: Counter-evidence attachment stored; payee notified of payer's response; both parties see full dispute thread

**TC-CONF-014: Dispute resolution — payer accepts dispute**
- Action: Payer clicks "Accept dispute" after reviewing
- Expected: Expense voided; both parties notified; expense appears in history as "Voided — dispute accepted"

**TC-CONF-015: Dispute resolution — payee agrees after counter-evidence**
- Action: Payee reviews counter-evidence; clicks "Approve"
- Expected: Dispute resolved; expense moves to Approved status; payment flow proceeds normally

**TC-CONF-016: Dispute thread is append-only**
- Action: Submit a dispute comment; attempt to delete or edit via direct API call
- Expected: API returns error; no modification to dispute thread

### 4.3 Mark as Paid Externally

**TC-CONF-020: Mark as paid externally — from confirmed expense**
- Action: Open approved expense; click "Mark as paid externally"; select method (Venmo); enter reference ID
- Expected: Expense status changes to "Settled (external)"; both parties notified; no ACH initiated

**TC-CONF-021: Mark as paid externally — Reg E audit trail**
- Action: Complete external payment marking
- Expected: External payment record stored with: method, reference ID, amount, date, user who marked it, timestamp (stored server-side; not exposed in DOM per DV safety rules)

---

## 5. Calendar Tests

### 5.1 Custody Pattern Rendering

**TC-CAL-001: 2-2-5-5 pattern renders correctly**
- Action: Configure 2-2-5-5 custody schedule starting a known Monday
- Expected: Calendar shows correct parent assignment for each day across a 4-week view; no off-by-one errors at month boundaries

**TC-CAL-002: Week view — color coding**
- Action: View week containing a custody switch day
- Expected: Payer days in one color, payee days in a contrasting color; switch day visually marked; legend present and readable

**TC-CAL-003: Month view — compact custody indicators**
- Action: View month view
- Expected: Each day cell shows custody indicator; days with expenses show a badge; layout does not overflow on 375px mobile screen

**TC-CAL-004: Pattern boundary at month end**
- Action: View a month where a custody block spans the last day of one month and first of next
- Expected: Correct color continuity across month boundary; no visual seam or gap

**TC-CAL-005: Holiday overlay**
- Action: Enable "School holidays" overlay
- Expected: Known holidays (e.g., Thanksgiving, Christmas) overlaid on calendar; holiday label appears on hover/tap; does not obscure custody color coding

**TC-CAL-006: Co-parent confirmation of schedule**
- Action: Payer sets up custody schedule; sends to payee for confirmation
- Expected: Payee receives notification; sees proposed schedule in read-only view with "Confirm" and "Request change" buttons

**TC-CAL-007: Schedule change request**
- Action: Payee clicks "Request change" on proposed schedule
- Expected: Change request form opens; payee specifies which dates and proposed alternative; payer notified; append-only thread started

**TC-CAL-008: Today indicator**
- Action: View any calendar view
- Expected: Today's date is visually highlighted; current custody assignment for today is prominently displayed

**TC-CAL-009: Navigation — prev/next month**
- Action: Click previous/next month navigation
- Expected: Calendar transitions smoothly; no flicker; custody pattern continues correctly

**TC-CAL-010: Navigation — jump to date**
- Action: Click on date picker in calendar header; select a date 6 months in the future
- Expected: Calendar jumps to that month; correct pattern applied

### 5.2 .ics Export

**TC-CAL-020: .ics export — download triggered**
- Action: Click "Export to calendar" button
- Expected: `.ics` file download begins; browser download dialog appears; file is named `fairbridge-custody-schedule.ics`

**TC-CAL-021: .ics file content — correct events**
- Action: Download .ics file; parse with a calendar library
- Expected: Each custody period appears as an all-day event; payer and payee labels correct; events cover at least 6 months from export date

**TC-CAL-022: .ics import into Apple Calendar (manual verification)**
- Action: Import downloaded .ics into Apple Calendar on macOS
- Expected: Events import without errors; custody labels visible in calendar; no duplicate events

**TC-CAL-023: .ics export — cross-browser download**
- Action: Test export on Chrome, Safari, Firefox, Edge
- Expected: Download works on all four browsers; Safari does not open the file inline instead of downloading

---

## 6. Stripe Connect Onboarding Modal Tests

### 6.1 Express Account Onboarding

**TC-STRIPE-001: Payer opens bank linking — modal opens**
- Action: Click "Link your bank account" from payment settings
- Expected: Stripe Connect Express onboarding opens as a full-screen modal overlay (not a new tab); URL does not change (no navigation away from app)

**TC-STRIPE-002: Stripe Connect — successful onboarding**
- Action: Complete Stripe Express onboarding with test data (test SSN `000-00-0000`, test bank account)
- Expected: Modal closes; app shows "Bank account linked"; payer can now send and receive payments
- Verify: Stripe `account.updated` webhook received; account status updated in database

**TC-STRIPE-003: Stripe Connect — failure (identity verification failed)**
- Action: Use test data that triggers identity verification failure (Stripe test persona)
- Expected: Modal shows Stripe's error message; on close, app shows "Verification failed — please try again" with a support link

**TC-STRIPE-004: Stripe Connect — abandonment (user closes modal mid-flow)**
- Action: Open onboarding modal; close it without completing
- Expected: App returns to pre-modal state; "Continue setting up your account" prompt shown on dashboard; progress preserved in Stripe (user can resume)

**TC-STRIPE-005: Stripe Connect — abandonment recovery**
- Action: After abandonment, click "Continue setup"
- Expected: Stripe Connect modal reopens at the point where user left off (not from the beginning)
- Verify: Same Stripe account ID reused; no duplicate accounts created

**TC-STRIPE-006: Stripe Connect — already onboarded**
- Action: User with completed Stripe account clicks "Manage bank account"
- Expected: Stripe Connect dashboard opens (not re-onboarding flow); user can view/update account details

**TC-STRIPE-007: Stripe Connect modal — keyboard accessible**
- Action: Open modal using keyboard (Tab to button, Enter to activate)
- Expected: Modal opens; focus moves inside modal; Tab cycles through modal content only (focus trap); Escape closes modal; focus returns to trigger button on close

**TC-STRIPE-008: Stripe Connect modal — mobile web**
- Action: Open on iOS Safari (375px viewport)
- Expected: Modal renders full-screen; Stripe's embedded UI is not clipped; form fields are usable without horizontal scroll

### 6.2 Stripe Financial Connections (Bank Linking)

**TC-STRIPE-020: Financial Connections — bank search**
- Action: Open bank linking flow; type bank name in search
- Expected: Bank suggestions appear within 1 second; selecting a bank proceeds to OAuth or credentials flow

**TC-STRIPE-021: Financial Connections — OAuth bank success**
- Action: Complete OAuth bank linking with a test institution
- Expected: Bank account linked; last 4 digits of account number displayed; "Linked" status shown

**TC-STRIPE-022: Financial Connections — credentials bank success**
- Action: Complete credentials-based linking with test institution `stripe_test_credentials_bank`
- Expected: Bank account linked; micro-deposit verification step (if required) is explained clearly

**TC-STRIPE-023: Financial Connections — failure (wrong credentials)**
- Action: Enter incorrect credentials for a test institution
- Expected: "Unable to connect to your bank — please check your credentials and try again"; retry button present

**TC-STRIPE-024: Financial Connections — user exits flow**
- Action: Open bank linking; click "Cancel" or close popup
- Expected: User returns to previous state; no partial bank connection created; "Link bank account" button still visible

**TC-STRIPE-025: Financial Connections — retry after failure**
- Action: After a failed bank link attempt, click retry
- Expected: Flow restarts cleanly; previous failed attempt does not cause a persistent error state

---

## 7. PDF Court Export Tests

### 7.1 Generation and Content

**TC-PDF-001: Export initiated from expense history**
- Action: Click "Export for court" button in expense history
- Expected: Date range picker appears; user selects range; "Generate PDF" button available

**TC-PDF-002: PDF generated — downloads successfully**
- Action: Select date range and click "Generate PDF"
- Expected: Loading indicator shown during generation; PDF downloads within 10 seconds for a 12-month range; browser download dialog appears

**TC-PDF-003: PDF content — required fields present**
- Action: Open generated PDF
- Expected: PDF contains:
  - Both co-parents' names (no last names if DV safety mode enabled)
  - Date range covered
  - Each expense: date, description, category, amount, split, status
  - Payment records: date, method, amount, payer
  - Total amounts: submitted, approved, settled, disputed
  - Page numbers and "Confidential — For Court Use" header

**TC-PDF-004: SHA-256 hash verification present**
- Action: Open generated PDF; locate hash verification section
- Expected: PDF includes a section titled "Document Integrity" containing:
  - SHA-256 hash of the document content
  - Instructions for verification
  - Timestamp of generation (UTC, server-side)
- Verify: Hash displayed in PDF matches hash returned by the PDF generation API endpoint

**TC-PDF-005: Hash verification — tamper detection**
- Action: Use a hex editor to modify one byte in the PDF body; re-verify hash
- Expected: Recomputed hash does not match the embedded hash; tamper evident

**TC-PDF-006: PDF includes all expense statuses**
- Action: Generate PDF for a period containing pending, approved, disputed, settled, and voided expenses
- Expected: All statuses represented; legend present; disputed and voided expenses clearly labeled

**TC-PDF-007: PDF — empty date range**
- Action: Select a date range with no expenses
- Expected: PDF generated with "No expenses recorded for this period" message; not an error state

**TC-PDF-008: PDF — large date range (performance)**
- Action: Export 24 months of data with 500+ expenses
- Expected: PDF generates within 30 seconds; no timeout; file size under 10MB

**TC-PDF-009: PDF — cross-browser download**
- Action: Test PDF export on Chrome, Safari, Firefox, Edge
- Expected: PDF downloads correctly on all four; Safari does not render it inline without offering a download option

---

## 8. Accessibility Tests (WCAG 2.1 AA)

Accessibility is a non-negotiable requirement. WCAG 2.1 AA compliance is required for all screens. The following tests combine automated tooling (axe-core) with manual verification for components that automated tools cannot assess.

### 8.1 Automated Accessibility Scan

**TC-A11Y-001: axe-core scan — zero critical/serious violations**
- Action: Run axe-core on every page in the app (onboarding, expense list, expense detail, calendar, PDF export, settings, subscription)
- Expected: Zero violations at "critical" or "serious" severity; "moderate" violations documented and triaged within 30 days

**TC-A11Y-002: Color contrast — AA ratio**
- Action: Use axe-core color contrast check on all text elements
- Expected: All normal text meets 4.5:1 contrast ratio; large text (18pt+) meets 3:1; UI component boundaries meet 3:1

**TC-A11Y-003: Color contrast — custody calendar color coding**
- Action: Check contrast between parent-time colors and background, and between payer and payee colors
- Expected: Both parent colors distinguishable at 3:1 contrast against white background; not differentiated by color alone (pattern or icon also used)

### 8.2 Keyboard Navigation

**TC-A11Y-010: Full keyboard navigation — onboarding flow**
- Action: Complete entire payer signup flow using only keyboard (Tab, Shift+Tab, Enter, Space, arrow keys)
- Expected: Every interactive element reachable; logical tab order; no keyboard trap except modals (which must trap focus correctly)

**TC-A11Y-011: Full keyboard navigation — expense submission**
- Action: Submit an expense using only keyboard
- Expected: Form fields, category dropdown, date picker, and submit button all reachable and operable via keyboard

**TC-A11Y-012: Full keyboard navigation — calendar**
- Action: Navigate calendar using keyboard
- Expected: Arrow keys navigate between dates; Enter selects a date; Tab moves between calendar controls; month navigation buttons keyboard accessible

**TC-A11Y-013: Focus indicator visible**
- Action: Tab through all interactive elements
- Expected: Focus ring visible on every focused element; focus ring meets 3:1 contrast against adjacent colors; no `:focus { outline: none }` without a visible replacement

**TC-A11Y-014: Skip navigation link**
- Action: Press Tab on any page
- Expected: "Skip to main content" link is the first focusable element; pressing Enter moves focus to main content area

**TC-A11Y-015: Modal focus trap**
- Action: Open any modal (confirmation dialog, Stripe Connect, dispute form)
- Expected: Focus is trapped within modal; Tab does not reach elements behind modal; Escape closes modal and returns focus to trigger

### 8.3 Screen Reader Compatibility

**TC-A11Y-020: Screen reader — expense list (NVDA + Chrome)**
- Action: Navigate expense list with NVDA on Windows + Chrome
- Expected: Each expense item announced with: amount, description, status, date; status badges have aria-label (not just color); action buttons labeled (not "button")

**TC-A11Y-021: Screen reader — calendar (VoiceOver + Safari)**
- Action: Navigate calendar with VoiceOver on macOS + Safari
- Expected: Each day cell announced with date, custody assignment ("Payer day" or "Co-parent day"), and expense count if applicable; navigation controls announced correctly

**TC-A11Y-022: Screen reader — form errors**
- Action: Submit expense form with validation errors; navigate with screen reader
- Expected: Error messages announced immediately via aria-live region; errors associated with their fields via aria-describedby; focus moves to first error field

**TC-A11Y-023: Screen reader — Stripe Connect modal**
- Note: Stripe's embedded UI has its own accessibility implementation. Test that the modal wrapper is correctly announced.
- Action: Open Stripe Connect modal with screen reader
- Expected: Modal role announced ("dialog"); modal title read; focus enters modal

**TC-A11Y-024: Images and icons — alt text**
- Action: Inspect all img elements and icon buttons with screen reader
- Expected: Decorative images have `alt=""`; informational images have descriptive alt text; icon buttons have aria-label matching their visual label

### 8.4 ARIA and Semantics

**TC-A11Y-030: Page titles unique and descriptive**
- Action: Navigate between pages; inspect `<title>` element
- Expected: Each page has a unique, descriptive title (e.g., "Expenses — FairBridge", "Calendar — FairBridge"); title updates on client-side navigation (React Router)

**TC-A11Y-031: Landmark regions**
- Action: Inspect HTML structure
- Expected: `<main>`, `<nav>`, `<header>`, `<footer>` landmarks used correctly; no duplicate `<main>` elements

**TC-A11Y-032: Form labels**
- Action: Inspect all form inputs
- Expected: Every input has an associated `<label>` (or aria-label/aria-labelledby); no placeholder-as-label pattern

**TC-A11Y-033: Error messages — ARIA live regions**
- Action: Trigger form validation errors
- Expected: Error container has `aria-live="assertive"` and `role="alert"`; errors announced without user navigation

**TC-A11Y-034: Status messages — non-error feedback**
- Action: Submit expense successfully; approve expense
- Expected: Success messages use `aria-live="polite"`; not announced as alerts

---

## 9. DV Safety Feature Tests

Domestic violence (DV) safety defaults are non-negotiable. These tests verify that the web frontend does not expose activity metadata that an abusive co-parent could weaponize.

### 9.1 No Activity Timestamps in DOM

**TC-DV-001: Expense list — no read timestamps**
- Action: Inspect DOM of expense list page (DevTools Elements panel)
- Expected: No element contains text or data-attributes showing when payee viewed the expense (e.g., "Seen at 2:34 PM", "Read by [name]")
- Verify: Network responses from GET /expenses do not include `viewed_at`, `read_at`, or similar fields

**TC-DV-002: Notification list — no delivery metadata**
- Action: Inspect notification list DOM
- Expected: Notifications show message content and date sent only; no "delivered to device at [time]", "opened at [time]", or push delivery receipt

**TC-DV-003: Invite email — no open-tracking pixel**
- Action: Inspect "money waiting" invite email HTML source
- Expected: No 1x1 tracking pixel; no external URL that could signal email open to the payer
- Verify: Email headers do not include Mailgun/Resend open-tracking headers

**TC-DV-004: Invite click-through — no open notification to payer**
- Action: Payee clicks invite link; payer checks their dashboard
- Expected: Payer's dashboard does not show "Payee viewed your invite" or similar notification; no such event in activity feed

**TC-DV-005: Login activity — not visible to co-parent**
- Action: Payee logs in; payer checks any accessible dashboard area
- Expected: Payer cannot see payee's last login time, device, or location anywhere in the web UI

### 9.2 Screen Content Appropriateness

**TC-DV-010: Screen title — no financial amounts in browser tab**
- Action: Navigate to expense submission page with a pending expense
- Expected: Browser tab title shows "FairBridge" or "Expenses — FairBridge"; does not show dollar amounts that could be visible in taskbar or shared-screen scenarios

**TC-DV-011: Notification preview — no financial details**
- Action: Trigger a notification (in-app notification banner)
- Expected: Notification banner shows generic message ("You have a new expense request") without dollar amount or description in the preview; user must click through to see details

**TC-DV-012: Safety resources — always accessible**
- Action: Navigate to Settings > Safety
- Expected: Safety resources page accessible without entering a password; shows National DV Hotline contact; "Quick exit" button present

**TC-DV-013: Quick exit button**
- Action: Click "Quick exit" button from any page in the app
- Expected: Browser navigates immediately to a neutral page (e.g., Google.com or weather.com); no app state visible; browser back button disabled or redirected (so navigating back does not re-expose the app)

**TC-DV-014: Silent deactivation — account deactivation does not notify co-parent**
- Action: User deactivates account from Settings
- Expected: Co-parent does not receive a notification ("Your co-parent deactivated their account"); app shows degraded state to co-parent without revealing reason

**TC-DV-015: Data export — available without co-parent knowledge**
- Action: Request data export from Settings > Privacy
- Expected: Export request processed silently; no co-parent notification; export link sent only to requesting user's email

**TC-DV-016: Data deletion — complete removal**
- Action: Request account deletion
- Expected: Confirmation dialog warns about data loss; on confirmation, all personal data (name, email, bank linking) deleted; financial records anonymized for audit trail (amounts and dates retained, PII removed); co-parent's view shows "Account closed" without further detail

---

## 10. Cross-Browser and Responsive Tests

### 10.1 Cross-Browser Functional Matrix

The following critical user journeys must be verified on each browser in the matrix (Chrome 133/132, Safari 18/17, Firefox 135/134, Edge 133/132):

| Test ID | Journey | Browsers |
|---------|---------|---------|
| TC-XBRO-001 | Payer signup + co-parent pairing | All 8 |
| TC-XBRO-002 | Expense submission with receipt upload | All 8 |
| TC-XBRO-003 | Expense approve + ACH payment initiation | All 8 |
| TC-XBRO-004 | Calendar month view + custody colors | All 8 |
| TC-XBRO-005 | .ics download | All 8 |
| TC-XBRO-006 | Stripe Connect Express modal | All 8 |
| TC-XBRO-007 | Stripe Financial Connections | All 8 |
| TC-XBRO-008 | PDF export download | All 8 |
| TC-XBRO-009 | Stripe Checkout subscription purchase | All 8 |

**TC-XBRO-010: Safari — cross-origin cookies**
- Action: Test Stripe Connect OAuth on Safari (ITP may block cross-origin cookies)
- Expected: Stripe Connect onboarding completes without cross-origin cookie issues; if ITP blocks, test that Stripe's fallback mechanism works

**TC-XBRO-011: Firefox — file download behavior**
- Action: Test .ics and PDF downloads on Firefox
- Expected: Files download (not open inline); Firefox download manager handles files correctly

**TC-XBRO-012: Edge — Chromium parity**
- Action: Run full functional suite on Edge
- Expected: Results match Chrome; no Edge-specific regressions (Edge is Chromium-based but has different default settings)

### 10.2 Responsive Layout Tests

**TC-RESP-001: Mobile (375px) — expense list readable**
- Action: View expense list at 375px width
- Expected: All expense fields visible without horizontal scroll; action buttons (Approve, Dispute) usable with thumb; no text overflow or clipping

**TC-RESP-002: Mobile (375px) — expense submission form**
- Action: Submit expense on mobile web
- Expected: Form fields full-width; keyboard does not obscure the submit button; date picker is mobile-friendly (native or custom that works with touch)

**TC-RESP-003: Mobile (375px) — calendar month view**
- Action: View calendar in month view at 375px
- Expected: Day cells readable; custody color coding visible; expenses badges visible; navigation arrows accessible by thumb

**TC-RESP-004: Tablet (768px) — two-column layout**
- Action: View expense list and detail at 768px
- Expected: If layout uses two columns at tablet, both panes are readable; no content overlap

**TC-RESP-005: Desktop (1280px) — optimal layout**
- Action: View all major screens at 1280px
- Expected: Content uses available width effectively; no single-column layout that wastes space; sidebars or split-pane layouts used where appropriate

**TC-RESP-006: Landscape mobile (667px × 375px)**
- Action: Rotate to landscape on mobile web
- Expected: Layout adapts; no elements hidden off-screen; Stripe Connect modal not clipped by viewport height

**TC-RESP-007: System font size — large text (200%)**
- Action: Set browser/OS font size to 200%
- Expected: Text scales without layout breaks; no text overlap; scrollable containers remain functional

**TC-RESP-008: Pinch-to-zoom not disabled**
- Action: Check `<meta name="viewport">` tag
- Expected: `user-scalable=no` is NOT present; users can pinch-to-zoom on all pages (accessibility requirement)

---

## 11. Performance and Network Tests

**TC-PERF-001: Time to interactive — initial load**
- Action: Measure TTI on `/` (unauthenticated) and `/dashboard` (authenticated) with Lighthouse CI
- Expected: TTI under 3 seconds on simulated 4G (10 Mbps / 50ms RTT); LCP under 2.5 seconds

**TC-PERF-002: Expense list — 100 items render time**
- Action: Load expense list with 100 items
- Expected: List renders within 500ms; no visible jank on scroll; virtualized rendering if applicable

**TC-PERF-003: Offline — graceful degradation**
- Action: Load dashboard; disable network; attempt to view expense list
- Expected: Cached expenses shown with "Offline — showing cached data" banner; no crash; no blank screen

**TC-PERF-004: Offline — expense submission blocked**
- Action: Disable network; attempt to submit expense
- Expected: Clear error "You're offline — expense saved locally and will submit when reconnected" OR "No network connection — please try again when online"; form not silently lost

**TC-PERF-005: PDF generation — progress indication**
- Action: Initiate PDF export for a large date range
- Expected: Loading spinner or progress bar shown for the duration; user not left with a frozen button; cancel option if generation takes >5 seconds

---

## 12. Security Tests (Frontend Layer)

**TC-SEC-001: Auth tokens — not in localStorage**
- Action: Inspect `localStorage` and `sessionStorage` in DevTools after login
- Expected: No auth tokens, JWTs, or session identifiers stored in client-side storage; tokens in httpOnly cookies only

**TC-SEC-002: Sensitive data — not in URL params**
- Action: Inspect URLs during normal navigation
- Expected: No PII (names, amounts, bank account numbers) in query params or path segments beyond IDs

**TC-SEC-003: Content Security Policy**
- Action: Inspect `Content-Security-Policy` response header on all pages
- Expected: CSP header present; `default-src 'self'`; Stripe domains explicitly allowlisted; no `unsafe-eval` or `unsafe-inline` in script-src

**TC-SEC-004: HTTPS enforced**
- Action: Navigate to `http://` version of the app
- Expected: Immediate redirect to `https://`; HSTS header present with `max-age` ≥ 1 year

**TC-SEC-005: Expense form — XSS prevention**
- Action: Submit an expense with description containing `<script>alert('xss')</script>`
- Expected: Script not executed when expense is rendered anywhere in the UI; text displayed as literal characters

**TC-SEC-006: PDF export — no script injection**
- Action: Create expense with malicious content in description field; export to PDF
- Expected: PDF renders text content only; no JavaScript execution in PDF viewer

---

## 13. Coordination Notes

### Dependencies on Other Teams

| Test Area | Dependency | Team |
|-----------|-----------|------|
| Stripe Connect modal | Stripe Connect Express account creation endpoint | backend-eng |
| Financial Connections | Bank linking token API | backend-eng |
| PDF hash verification | SHA-256 hash in API response | backend-eng |
| Expense append-only | PUT/DELETE endpoint behavior | backend-eng |
| Payee invite landing page | Invite token validation endpoint | backend-eng |
| Calendar custody pattern | Pattern calculation API | backend-eng |
| DV safety — no timestamps | API response field audit | backend-eng |
| UX flow accuracy | Screen transitions match spec | ux-engineer |
| Component test coverage | Component interface contracts | web-dev |

### Open Questions for web-dev

1. Does the Stripe Connect Express modal open as an iframe overlay or navigate to Stripe's hosted URL? This affects how TC-STRIPE-007 (keyboard accessibility) is tested — iframe focus management requires different test logic than in-page modal.
2. Is calendar rendering handled client-side (computed from pattern + start date) or does the API return pre-computed day-by-day assignments? This affects TC-CAL-001 through TC-CAL-004.
3. Does expense list use virtualization (react-window / react-virtual)? Affects TC-PERF-002.

### Open Questions for ux-engineer

1. What is the exact screen count for the payee invite funnel (TC-ONB-023)? The test assumes ≤3 screens from landing page click to bank linking. If the UX spec requires more screens, the test threshold needs updating.
2. Is there a "Quick exit" button specification beyond Settings > Safety? Should it appear on all pages or just certain ones?
3. For TC-DV-011 (notification preview), what is the approved notification copy for expense requests?

---

## Appendix A: Test Coverage Summary

| Section | Test Count | Priority |
|---------|-----------|---------|
| Onboarding | 35 | P0 |
| Expense Submission | 23 | P0 |
| Two-Party Confirmation | 16 | P0 |
| Calendar | 13 | P1 |
| Stripe Connect | 13 | P0 |
| PDF Export | 9 | P1 |
| Accessibility | 24 | P0 |
| DV Safety | 16 | P0 |
| Cross-Browser / Responsive | 20 | P1 |
| Performance / Network | 5 | P2 |
| Security | 6 | P0 |
| **Total** | **180** | |

P0 = blocking for launch. P1 = required before general availability. P2 = required within 30 days of GA.

## Appendix B: Regression Test Suite

For each release, run the following as the automated regression gate (Playwright CI):

1. TC-ONB-001, TC-ONB-020, TC-ONB-023, TC-ONB-031 (onboarding happy paths)
2. TC-EXP-001 through TC-EXP-007 (expense form validation)
3. TC-CONF-002, TC-CONF-010 (approve and dispute happy paths)
4. TC-CAL-001, TC-CAL-020 (calendar render + .ics export)
5. TC-STRIPE-002, TC-STRIPE-021 (Stripe Connect + Financial Connections happy paths)
6. TC-PDF-002, TC-PDF-004 (PDF export + hash verification)
7. TC-DV-001, TC-DV-003, TC-DV-013 (DV safety critical)
8. TC-A11Y-001 (axe-core zero-violation scan on all pages)
9. TC-SEC-001, TC-SEC-003, TC-SEC-005 (auth token, CSP, XSS)

Total automated regression suite: ~35 tests. Target runtime: under 15 minutes in CI.
