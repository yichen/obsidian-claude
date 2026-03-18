# FairBridge Web Frontend Specification

**Author**: Web Frontend Engineer
**Date**: 2026-03-17
**Status**: Draft v1
**Task**: #3 — Web app architecture and components

---

## 1. Overview & Guiding Principles

FairBridge is a cooperative coparenting schedule + payment app targeting **non-court-ordered parents** who want a clean, modern alternative to OurFamilyWizard. The web app serves two primary purposes:

1. **Subscription management hub** — Web-only purchase flow to avoid Apple IAP 30% fee. All billing happens here; mobile apps deep-link here for upgrades.
2. **Full-featured web client** — Mirror of mobile functionality for desktop users (payers, payees, shared expense tracking, calendar, court export).

### Guiding Principles

- **Two-party UX**: Every feature must account for both parents. Never assume one is the "primary" user.
- **DV (domestic violence) safety first**: No contact info exposure; safety exit button always visible; no shared-device indicators.
- **Progressive disclosure**: Onboarding is step-by-step; don't overwhelm new users.
- **Stripe as the trust layer**: Payment confirmation, bank linking, and identity verification all flow through Stripe UI — FairBridge never handles raw financial data.
- **Court-ready outputs**: Every PDF export must be tamper-evident (SHA-256 hash).

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | React 18 + TypeScript | Type safety, ecosystem maturity |
| State management | Zustand (global) + React Query (server) | Lightweight; React Query handles caching/sync for API calls |
| Routing | React Router v6 | File-based routes via `createBrowserRouter` |
| Styling | Tailwind CSS + shadcn/ui | Utility-first; shadcn gives accessible primitives |
| Forms | React Hook Form + Zod | Schema-driven validation; works well with TypeScript |
| PDF generation | `@react-pdf/renderer` | React-idiomatic; server-side rendering possible for court exports |
| Calendar | `@fullcalendar/react` | Rich event model; supports custom rendering for custody color-coding |
| Charts (minor) | Recharts | For expense summary breakdowns |
| Testing | Vitest + React Testing Library | Unit + integration; Playwright for E2E |
| Build | Vite | Fast HMR; good code splitting |
| Hosting | Vercel (preferred) or Netlify | Edge functions for PDF signing; CDN for assets |

---

## 3. App Architecture

```
src/
├── app/                    # Router config, providers, global layout
│   ├── router.tsx
│   ├── AppProviders.tsx    # Auth, React Query, Zustand, Stripe
│   └── Layout.tsx          # Shell: nav, DV exit button, toast container
├── pages/                  # Route-level components (thin wrappers)
│   ├── auth/               # Login, signup, magic link landing
│   ├── onboarding/         # Step-by-step onboarding wizard
│   ├── dashboard/          # Home: upcoming payments, schedule summary
│   ├── calendar/           # Calendar view
│   ├── expenses/           # Expense list, submission, confirmation
│   ├── payments/           # Payment history, initiate payment
│   ├── settings/           # Subscription, bank account, profile, notifications
│   └── export/             # Court PDF export
├── features/               # Domain-organized feature modules
│   ├── auth/
│   ├── onboarding/
│   ├── calendar/
│   ├── expenses/
│   ├── payments/
│   ├── export/
│   └── subscription/
├── components/             # Shared UI components
│   ├── ui/                 # shadcn primitives (Button, Card, Dialog, etc.)
│   ├── SafetyExitButton.tsx
│   ├── ParentAvatar.tsx    # Color-coded (blue/green) avatar
│   ├── CustodyBadge.tsx
│   └── StripeModal.tsx
├── hooks/                  # Custom React hooks
├── lib/                    # API client, Stripe.js init, utils
│   ├── api.ts              # Typed fetch wrapper
│   ├── stripe.ts           # loadStripe singleton
│   └── pdf.ts              # PDF generation helpers
└── types/                  # Shared TypeScript interfaces
```

---

## 4. Authentication

### 4.1 Auth Strategy
- Magic link (email) as primary — avoids password management, reduces friction
- Optional: Google OAuth for faster signup
- JWT access token (15 min) + refresh token (30 days) stored in httpOnly cookie
- No localStorage for tokens — XSS protection

### 4.2 Auth Pages

**`/login`**
- Email input → "Send magic link" button
- Google OAuth button (secondary)
- On magic link click → `/auth/verify?token=...` → issue session → redirect to `/onboarding` (new) or `/dashboard` (existing)

**`/auth/verify`**
- Auto-processes token on mount; shows spinner then redirects
- On error: clear message + "Resend link" button

---

## 5. Onboarding Flows

Onboarding is the most critical UX. Both parents must complete their side before any features unlock.

### 5.1 Payer Onboarding (`/onboarding/payer`)

**Step 1 — Welcome & Role**
```
"Welcome to FairBridge. Let's get you set up."
[I send child support / spousal support payments]
[I receive payments from my co-parent]
```
- Role selection determines flow; payer = initiating bank account + Stripe Connect setup

**Step 2 — Connect Bank Account (Stripe Financial Connections)**
- Trigger: `stripe.collectBankAccountToken()` in a full-screen modal
- Shows: institution picker → account selector → micro-deposit verify OR instant verification
- On success: display `****1234 (Chase Checking)` with green checkmark
- On error: retry prompt + "Use manual routing/account number" fallback

**Step 3 — Invite Co-Parent**
- Input: co-parent email
- System sends invite email with "money is waiting" landing page link (see section 5.3)
- Shows estimated schedule: "Payments will begin once [name] accepts"
- "Skip for now" allowed — reminders sent at 3, 7, 14 days

**Step 4 — Payment Schedule Setup**
- Frequency: Monthly / Bi-weekly / Weekly / Custom
- Amount: dollar input with live preview ("$1,254.00 every month")
- Start date picker (first payment date)
- Optional memo field (e.g., "Child support per parenting plan")

**Step 5 — Review & Confirm**
- Summary card: bank, co-parent, amount, frequency, first payment date
- "Looks good — Start FairBridge" CTA → dashboard

### 5.2 Payee Onboarding (`/onboarding/payee`)

Triggered when payee clicks invite link from email.

**Step 1 — Landing / "Money is Waiting"** (see section 5.3)

**Step 2 — Create Account or Sign In**
- Email pre-filled from invite link param
- Magic link or Google OAuth

**Step 3 — Connect Bank Account (Stripe Financial Connections)**
- Same Financial Connections modal as payer
- Emphasize: "This is where you'll receive payments"

**Step 4 — Confirm Details**
- Show payer's configured schedule: "John will send you $1,254.00 monthly starting April 1"
- "Accept & Activate" button — triggers backend to link the Stripe accounts and schedule first payment

**Step 5 — Dashboard Welcome**
- First-time empty state: next payment date, countdown

### 5.3 Payee Invite Landing Page (`/invite/:token`)

This page is the "hook" for payee acquisition. Critical for conversion.

**Layout**:
```
[FairBridge logo]

💸 You have money waiting.

[FirstName] has set up automatic payments for you
through FairBridge.

  Amount: $1,254.00 / month
  Starting: April 1, 2026
  From: John D.  ****  (masked)

To receive your payments, create a free account
and connect your bank — takes 3 minutes.

[Get My Money]  ← primary CTA, bright color

Already have an account? [Sign in]
```

**Design notes**:
- Must be fast (< 1s LCP) — payee may be on mobile data
- Token expires in 7 days; expired page shows "Ask [FirstName] to resend"
- DV safety: never shows payer's full name or location on this page; first name + masked surname only

---

## 6. Dashboard (`/dashboard`)

Post-login home screen. Adapts to user role (payer vs. payee).

### 6.1 Payer Dashboard
```
┌─────────────────────────────────────┐
│  Next Payment                       │
│  $1,254.00  →  Sarah M.            │
│  Due: April 1, 2026  [3 days away] │
│  [Pay Now]  [View History]          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Pending Expenses (2)               │
│  • School supplies  $87.40  [View]  │
│  • Dentist copay   $120.00  [View]  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  This Week (Calendar preview)       │
│  [mini 7-day strip — color coded]   │
└─────────────────────────────────────┘
```

### 6.2 Payee Dashboard
```
┌─────────────────────────────────────┐
│  Incoming Payment                   │
│  $1,254.00  ←  John D.             │
│  Expected: April 1, 2026           │
│  [View History]                     │
└─────────────────────────────────────┘

[Same expense and calendar panels]
```

---

## 7. Calendar View (`/calendar`)

### 7.1 Custody Pattern Color-Coding

| Color | Meaning |
|---|---|
| Blue | Parent A (payer) custody |
| Green | Parent B (payee) custody |
| White/stripe | Transition day |
| Yellow dot | Payment due date |
| Orange dot | Pending expense |

### 7.2 View Modes

**Week View** (default on desktop)
- 7-column grid
- Each day cell: custody color background, events as pills
- Click day → day detail panel (side drawer on desktop, full screen on mobile)

**Month View**
- Standard calendar grid
- Day cells: colored left border (3px) = custody; event dots for payments/expenses
- "Today" highlighted with ring

**Implementation** (`@fullcalendar/react`):
```typescript
<FullCalendar
  plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
  initialView="dayGridMonth"
  events={custodyEvents}
  dayCellDidMount={(info) => {
    // Apply custody color class based on schedule pattern
    const custody = getCustodyForDate(info.date, schedule);
    info.el.classList.add(`custody-${custody}`);  // 'parent-a' | 'parent-b' | 'transition'
  }}
  eventContent={renderEventContent}
/>
```

### 7.3 Custody Pattern Engine
- 2-2-5-5 and 2-2-3 patterns computed client-side from `schedule.startDate` + `schedule.pattern`
- `getCustodyForDate(date, schedule): 'parent-a' | 'parent-b' | 'transition'`
- Stored in Zustand, recomputed when schedule changes
- Override support: individual day overrides (holidays, vacation) stored in DB, merged on render

### 7.4 Calendar Components

```
CalendarPage
├── CalendarToolbar         # Week/Month toggle, prev/next, today, export button
├── FullCalendar            # Core calendar
├── DayDetailDrawer         # Slide-in panel for day detail
│   ├── CustodyBadge        # "Parent A's Day" / "Parent B's Day"
│   ├── PaymentEventCard    # If payment due
│   └── ExpenseEventCard    # If expense logged
└── LegendBar               # Color key at bottom
```

---

## 8. Expense Submission & Two-Party Confirmation

### 8.1 Expense Submission (`/expenses/new`)

**Form fields**:
- Category (dropdown): Medical, Education, Activities, Clothing, Other
- Description (text input, max 200 chars)
- Amount (currency input)
- Date incurred (date picker, defaults today)
- Split ratio (pre-set or custom): 50/50 | 60/40 | 70/30 | Custom
- Receipt upload (image or PDF, max 10MB) — stored in S3, URL saved to DB
- Notes (optional textarea)

**Validation** (Zod schema):
```typescript
const expenseSchema = z.object({
  category: z.enum(['medical', 'education', 'activities', 'clothing', 'other']),
  description: z.string().min(3).max(200),
  amount: z.number().positive().max(50000),
  dateIncurred: z.date().max(new Date()),
  splitRatio: z.object({ submitter: z.number(), other: z.number() })
    .refine(s => s.submitter + s.other === 100),
  receiptUrl: z.string().url().optional(),
  notes: z.string().max(500).optional(),
});
```

**On submit**: POST to `/api/expenses` → expense created in `pending_confirmation` state → push notification + email to other parent

### 8.2 Expense List (`/expenses`)

- Tabs: Pending | Approved | Rejected | All
- Each row: category icon, description, amount (your share), date, status badge, action button
- Filter: date range, category, status
- Sort: date (default), amount, status

### 8.3 Two-Party Confirmation UI

When the other parent receives an expense notification and taps "Review":

**`/expenses/:id`**
```
┌─────────────────────────────────────┐
│  Expense from Sarah                 │
│  Medical — Dentist copay            │
│                                     │
│  Total:        $240.00              │
│  Split:        50 / 50              │
│  Your share:   $120.00              │
│  Date:         March 15, 2026       │
│                                     │
│  [View Receipt]                     │
│                                     │
│  Notes: "Annual cleaning + x-ray"   │
│                                     │
│  [Approve & Pay $120]  [Decline]    │
└─────────────────────────────────────┘
```

- "Approve & Pay" → triggers Stripe payment (ACH pull from payer's linked account)
- "Decline" → opens reason dialog (required field, 10+ chars) → submitter notified
- Approved expenses appear in payment history with expense reference
- Receipt stored immutably; URL never changes after submission

### 8.4 Expense State Machine
```
submitted → pending_confirmation → approved → payment_initiated → payment_completed
                                → declined (with reason)
                                → disputed (escalation path — future feature)
```

---

## 9. Payments (`/payments`)

### 9.1 Payment History Table

Columns: Date | Type | Amount | Direction | Status | Actions

- Type: `Scheduled` | `Expense Reimbursement` | `Manual`
- Direction: arrow icon (sent / received)
- Status: `Scheduled` | `Processing` | `Completed` | `Failed` | `Refunded`
- Actions: `View Receipt` | `Download PDF`

### 9.2 Manual Payment Initiation

For ad-hoc payments outside the schedule:
- Amount input
- Memo field
- "Send Now" → Stripe ACH debit
- Confirmation modal before executing

### 9.3 Failed Payment Handling

- Banner on dashboard: "Payment failed — [reason]. [Retry] [Update bank account]"
- Retry attempts: 2 automatic (D+1, D+3) then requires manual action
- Both parents notified of failure

---

## 10. Subscription Management (`/settings/subscription`)

**This is the web-only purchase flow.** Mobile apps show a web link here instead of an in-app purchase screen (to avoid Apple IAP 30% cut).

### 10.1 Plans UI

```
┌──────────────────┐  ┌──────────────────┐
│   Free            │  │   Pro  ✓          │
│                  │  │                  │
│  Payments: ✓     │  │  Payments: ✓     │
│  Expenses: 3/mo  │  │  Expenses: ∞     │
│  Calendar: basic │  │  Calendar: full  │
│  Export: —       │  │  PDF Export: ✓   │
│  History: 3 mo   │  │  History: ∞      │
│                  │  │                  │
│  Free forever    │  │  $9.99/mo        │
│                  │  │  or $79/yr       │
│  [Current Plan]  │  │  [Upgrade]       │
└──────────────────┘  └──────────────────┘
```

### 10.2 Stripe Checkout Integration

- Click "Upgrade" → Stripe Checkout session created (backend) → redirect to `stripe.com/pay/...`
- On success: Stripe redirects to `/settings/subscription?success=true`
- Success page: confetti, plan confirmation, "Go to Dashboard"
- Cancellation: `?canceled=true` → back to subscription page with "No worries" message
- **Mobile flow**: Web deep link opens `fairbridge.app/settings/subscription` in Safari/Chrome; completes there; app re-fetches subscription status on return

### 10.3 Subscription Status

- Current plan badge
- Next billing date
- Payment method (last 4 digits of card on file)
- "Cancel Subscription" link → confirmation dialog → cancellation scheduled for period end
- "Update Payment Method" → Stripe Customer Portal redirect

---

## 11. Stripe Connect Express Onboarding Modal

Used during payer onboarding (Step 2) and settings bank update.

### 11.1 Modal Design

```
┌───────────────────────────────────────────────┐
│  Connect Your Bank Account                 [X] │
│                                               │
│  FairBridge uses Stripe to securely link     │
│  your bank. Your credentials go directly to  │
│  Stripe — FairBridge never sees them.        │
│                                               │
│  [Stripe Financial Connections embedded UI]  │
│   ┌─────────────────────────────────────┐    │
│   │  [Chase]  [Bank of America]  [Wells] │    │
│   │  [Fidelity]  [More banks...]         │    │
│   └─────────────────────────────────────┘    │
│                                               │
│  🔒 Secured by Stripe                        │
└───────────────────────────────────────────────┘
```

### 11.2 Implementation

```typescript
// lib/stripe.ts
import { loadStripe } from '@stripe/stripe-js';
export const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PK);

// In StripeConnectModal.tsx
const stripe = await stripePromise;
const { financialConnectionsSession } = await stripe!.collectBankAccountToken({
  clientSecret,  // from backend: POST /api/stripe/financial-connections/session
  params: {
    payment_method_type: 'us_bank_account',
    payment_method_data: { billing_details: { email: user.email } },
  },
  expand: ['payment_method'],
});
```

- Modal is a `<Dialog>` (shadcn) with `z-index: 9999`
- On mobile web: same modal, full-screen on small viewports (`max-h-screen rounded-none`)
- On iOS app: triggers deep link `fairbridge://stripe-connect` → app opens Safari for Connect onboarding
- No Chrome Custom Tabs on web (web-only concern; Android handles that in native app spec)

### 11.3 Stripe Connect Express (for payee receiving payments)

- Payee onboarding Step 3 triggers Stripe Connect Express account creation
- Redirect to `connect.stripe.com/express/...` with `redirect_uri=fairbridge.app/onboarding/payee/step-4`
- On return: backend confirms account active, enables payment routing to payee

---

## 12. PDF Court Export (`/export`)

### 12.1 Export UI

```
┌─────────────────────────────────────────────┐
│  Generate Court Report                      │
│                                             │
│  Date Range:  [Jan 1, 2025] → [Dec 31, 2025]│
│                                             │
│  Include:                                   │
│  ☑ Payment history                          │
│  ☑ Expense log (approved only)              │
│  ☑ Custody calendar                         │
│  ☐ Declined expenses (with reasons)         │
│                                             │
│  Format:  ● PDF   ○ CSV                     │
│                                             │
│  [Generate Report]                          │
└─────────────────────────────────────────────┘
```

### 12.2 PDF Contents

1. **Cover page**: Report generated date, date range, both parents' names (first + last initial), FairBridge logo, SHA-256 hash of report body
2. **Payment Summary**: Total sent/received, per-month breakdown table
3. **Payment Detail**: Chronological table — Date | Description | Amount | Status | Transaction ID
4. **Expense Log**: Date | Category | Description | Total | Split | Status | Payer of record
5. **Custody Calendar**: Month-by-month calendar pages with color-coded custody blocks
6. **Verification Footer** (every page): `Document hash: abc123... | Generated: 2026-03-17 | Verify at fairbridge.app/verify`

### 12.3 SHA-256 Tamper Evidence

```typescript
// Backend generates report, computes hash before signing
const reportBuffer = await generatePdfBuffer(reportData);
const hash = createHash('sha256').update(reportBuffer).digest('hex');

// Store hash in DB with report metadata
await db.reports.create({ userId, hash, dateRange, generatedAt: new Date() });

// Embed hash in PDF footer (page 1 + every page)
// Verification endpoint: GET /api/reports/verify?hash=abc123
//   → returns: { valid: true, generatedAt, userId (masked), dateRange }
```

- PDF generation happens **server-side** (Vercel Edge Function) to ensure deterministic output
- `@react-pdf/renderer` renders React components to PDF buffer on server
- Client downloads via signed S3 URL (expires in 1 hour)
- User can verify authenticity at `fairbridge.app/verify` without login

### 12.4 PDF Generation Stack

```
Client: clicks "Generate"
  → POST /api/reports/generate { dateRange, sections }
  → Backend: fetch all data → renderToBuffer(<ReportDocument />) → sha256 → upload S3
  → Response: { reportId, downloadUrl, hash }
Client: download link + hash displayed
```

---

## 13. DV Safety Features

### 13.1 Global Safety Exit Button

Present on **every page** — fixed position, top-right corner.

```tsx
// components/SafetyExitButton.tsx
export function SafetyExitButton() {
  const handleExit = () => {
    // Replace current session history to prevent back-navigation
    window.location.replace('https://weather.com');
  };
  return (
    <button
      onClick={handleExit}
      className="fixed top-3 right-3 z-[10000] bg-red-600 text-white px-3 py-1.5 rounded text-sm font-semibold hover:bg-red-700"
      aria-label="Quick exit"
    >
      Exit
    </button>
  );
}
```

- Replaces history (no back-button return to FairBridge)
- Keyboard shortcut: `Escape` × 3 rapid presses
- Configurable destination URL in settings (default: weather.com)

### 13.2 Information Hiding

- Never show co-parent's email, phone, or address anywhere in UI
- Payment receipts show name only (no account details)
- Invite links use opaque tokens, not email in URL
- "Who sent this invite" on payee landing page: first name + last initial only
- No "last seen" indicators
- No co-parent location or device information exposed

### 13.3 Communication Design

- No in-app messaging (reduces conflict surface; OFW's message logging is a liability)
- All dispute resolution: structured decline reason + email notification only
- No read receipts

---

## 14. Settings

### 14.1 Settings Navigation
- Profile (name, email, notification preferences)
- Bank Account (view connected, update)
- Subscription (plan, billing)
- Co-Parent Connection (view status, resend invite, disconnect)
- Notifications (email, push toggles per event type)
- Safety (exit button destination URL, account deletion)
- Export (generate court reports)

### 14.2 Notification Preferences

| Event | Email | Push |
|---|---|---|
| Payment scheduled (3 days before) | ✓ | ✓ |
| Payment sent/received | ✓ | ✓ |
| Payment failed | ✓ | ✓ |
| Expense submitted by co-parent | ✓ | ✓ |
| Expense approved/declined | ✓ | ✓ |
| New invite accepted | ✓ | — |
| Monthly summary | ✓ | — |

---

## 15. API Contract Requirements (for backend-eng)

These are the API endpoints the frontend requires. Backend should treat these as the contract.

### Authentication
- `POST /api/auth/magic-link` — send magic link email
- `GET /api/auth/verify?token=` — verify token, issue session
- `POST /api/auth/google` — Google OAuth exchange
- `POST /api/auth/logout`

### Onboarding
- `POST /api/onboarding/invite` — create payee invite (returns token)
- `GET /api/onboarding/invite/:token` — get invite metadata (payer first name, amount, schedule)
- `POST /api/onboarding/accept/:token` — payee accepts invite

### Stripe
- `POST /api/stripe/financial-connections/session` — create FC session (returns clientSecret)
- `POST /api/stripe/connect/account` — create Connect Express account (returns onboarding URL)
- `POST /api/stripe/checkout/session` — create Checkout session for subscription
- `GET /api/stripe/subscription/status` — current plan + expiry

### Payments
- `GET /api/payments` — paginated payment history
- `POST /api/payments/manual` — initiate manual payment
- `POST /api/payments/:id/retry` — retry failed payment

### Expenses
- `GET /api/expenses` — list with filters
- `POST /api/expenses` — submit expense
- `GET /api/expenses/:id`
- `POST /api/expenses/:id/approve`
- `POST /api/expenses/:id/decline` `{ reason: string }`

### Calendar
- `GET /api/schedule` — custody schedule config (pattern, start date, overrides)
- `PUT /api/schedule/override` — add day override
- `GET /api/events` — payments + expenses as calendar events for date range

### Reports
- `POST /api/reports/generate` — async; returns `{ reportId }`
- `GET /api/reports/:id/status` — polling for async generation
- `GET /api/reports/:id/download` — signed S3 URL
- `GET /api/reports/verify?hash=` — public hash verification (no auth)

---

## 16. Error Handling & Empty States

### 16.1 Error Boundaries

- Global error boundary at `AppProviders` level: catches unexpected crashes → "Something went wrong" page with reload button
- Route-level error boundaries for page-specific failures
- API errors: React Query `onError` handlers → toast notifications for transient errors; inline error states for form submissions

### 16.2 Empty States

| Page | Empty State |
|---|---|
| Dashboard | "Waiting for co-parent to accept invite" with resend option |
| Payments | "No payments yet — your first payment is on [date]" |
| Expenses | "No expenses. Tap + to log a shared expense." |
| Calendar | Calendar renders with custody colors even with no events |

---

## 17. Responsive Design

- **Breakpoints**: mobile (<768px), tablet (768-1024px), desktop (>1024px)
- **Mobile-first**: all components designed for mobile, enhanced for desktop
- **Calendar**: month view on mobile (week view default on desktop, toggle available)
- **Expense form**: full-page on mobile, modal on desktop
- **Navigation**: bottom tab bar on mobile (`/dashboard`, `/calendar`, `/expenses`, `/payments`), left sidebar on desktop

---

## 18. Accessibility

- WCAG 2.1 AA compliance target
- All interactive elements keyboard-accessible
- `aria-label` on icon-only buttons
- Color is never the only indicator (custody: color + pattern/label)
- Focus trap in modals (Stripe, expense form, export)
- Screen reader: `aria-live="polite"` for payment status updates

---

## 19. Performance Targets

| Metric | Target |
|---|---|
| LCP (invite landing page) | < 1.0s |
| LCP (dashboard) | < 2.5s |
| TTI | < 3.5s |
| Bundle size (initial) | < 200KB gzipped |
| API response time (p95) | < 500ms |

Code splitting: lazy-load calendar, PDF export, and Stripe modules — they're heavy and not needed on initial render.

```typescript
const CalendarPage = lazy(() => import('./pages/calendar/CalendarPage'));
const ExportPage = lazy(() => import('./pages/export/ExportPage'));
```

---

## 20. Security Considerations

- **CSP headers**: restrict script-src to self + Stripe domains only
- **CORS**: restrict to `fairbridge.app` origin
- **CSRF**: SameSite=Strict cookies + Origin header validation
- **File uploads**: validate MIME type + magic bytes server-side; max 10MB enforced at CDN level
- **Input sanitization**: DOMPurify for any user-generated content rendered as HTML
- **Stripe.js only from `js.stripe.com`**: never self-host; include integrity check
- **Report download URLs**: signed S3 presigned URLs, expire in 1 hour

---

## 21. Open Questions for Team

**For backend-eng (backend-eng)**:
1. WebSocket or SSE for real-time payment status updates? (prefer SSE for simplicity)
2. Async report generation: polling vs. webhook push to frontend?
3. Rate limiting on expense submission? (suggest: 20/day per user)
4. Invite token expiry: 7 days acceptable?

**For ux-engineer (ux-engineer)**:
1. Payee invite landing page: show payment amount before signup? (conversion vs. privacy tradeoff)
2. Two-parent confirmation: should declining an expense require a reason or allow anonymous decline?
3. Calendar: should both parents see the same view, or can each customize custody colors?
4. Safety exit: bottom-right vs. top-right? Any brand conflict?

**For frontend-tester**:
1. Critical paths to cover in E2E: (a) payer onboarding, (b) payee invite accept, (c) expense submit + approve, (d) payment failure + retry
2. Stripe Financial Connections: use `stripe-js` test mode; no real bank needed in CI
3. PDF export: snapshot test the React PDF component in isolation; hash verification tested via API mock

---

*End of Web Frontend Specification v1*
