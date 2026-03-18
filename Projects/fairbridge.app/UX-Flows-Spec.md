# FairBridge UX Flows Specification

**Document type**: UX Flow Specification
**Author**: UX Engineer
**Date**: 2026-03-17
**Status**: Draft v1.0

---

## Executive Summary

FairBridge is a co-parenting expense tracking and ACH payment app targeting cooperative, non-court-ordered separated parents. The product has three pillars: ACH payments (via Stripe Connect), append-only expense tracking, and a custody calendar. The app ships as React Native (Expo) on iOS and Android, with a React web app for subscription management.

The single highest-risk user journey is the payee onboarding funnel. The payee (typically the parent who is owed money) must accept an invite, create an account, link a bank account, and receive a first deposit — all without the payer standing over their shoulder. Every unnecessary screen kills conversion. The design target is >50% completion from invite open to first payment received.

This specification covers every user-facing flow, specifying screens, actions, transitions, error states, and platform differences (web vs. iOS vs. Android).

---

## Platform Overview and Constraints

| Platform | Primary Use | Key Constraints |
|----------|-------------|-----------------|
| iOS (React Native / Expo) | Core daily use | App Store IAP rules — no subscription purchase in-app; Notification permission must be requested at an appropriate moment; No background location |
| Android (React Native / Expo) | Core daily use | Battery optimization may kill FCM; No uniform permission dialog timing; Sideloading edge cases |
| Web (React) | Subscription management, onboarding landing pages, court PDF export | Full-screen Stripe Connect modal; Deeplink handoff to mobile app |

All three platforms share the same backend API. Platform-specific divergences are called out inline with **[iOS]**, **[Android]**, and **[Web]** tags.

---

## Flow 1: Payer Onboarding → Invite Payee → First Expense → First Payment

This is the primary acquisition flow. The payer is the parent who initiates the app, adds expenses, and initiates payment. They are typically more motivated and technically comfortable.

### Screen 1.1 — Welcome / Value Prop

**Trigger**: First app launch (no session token)

**Layout**:
- Single screen, no scroll
- Headline: "Split kids' expenses. Send money. Keep records."
- Subheadline: "Track shared costs and pay your co-parent by bank transfer — with a permanent record both of you can export."
- CTA: "Get started" (primary button)
- Secondary link: "Already have an account? Sign in"

**Actions**:
- Tap "Get started" → Screen 1.2
- Tap "Sign in" → Screen 1.7 (Sign In)

**Error states**: None — this screen is fully local.

**Platform differences**:
- **[iOS/Android]**: Native app — full-bleed illustration, haptic on CTA tap
- **[Web]**: Same layout, no haptic; "Get started" opens inline next step

---

### Screen 1.2 — Role Selection

**Layout**:
- Headline: "Which describes you?"
- Two cards, equal size:
  - Card A: "I pay expenses" — icon of outgoing payment — subtext: "You'll invite your co-parent to receive transfers"
  - Card B: "I receive payments" — icon of incoming payment — subtext: "Your co-parent sent you a link to get started"
- No "Other" option — keep binary for MVP

**Why this matters**: Payer and payee onboarding diverge significantly after this. Payee may arrive via invite link (Flow 2), in which case they skip this screen entirely.

**Actions**:
- Tap "I pay expenses" → Screen 1.3 (Payer account creation)
- Tap "I receive payments" → Flow 2, Screen 2.1

**Error states**: None.

**Platform differences**: None — identical across platforms.

---

### Screen 1.3 — Account Creation (Payer)

**Layout**:
- Headline: "Create your account"
- Fields: Full name, Email, Password (show/hide toggle)
- CTA: "Continue"
- Fine print: "By continuing you agree to our Terms and Privacy Policy" (tappable links)
- Alternative: "Continue with Apple" **[iOS]**, "Continue with Google" **[iOS/Android/Web]**

**Validation**:
- Email: real-time format check; show inline error "Enter a valid email"
- Password: minimum 8 chars; show strength indicator (weak / ok / strong) — do NOT show character-class requirements (reduces anxiety)
- Name: non-empty; trim whitespace

**Actions**:
- Tap "Continue" with valid inputs → POST /auth/register → Screen 1.4 (Email verification)
- Tap "Continue" with invalid inputs → inline field errors, no navigation
- Tap social login → OAuth flow → if new user, Screen 1.4 (skip email verification); if existing user, go to home

**Error states**:
- Email already registered: "That email is already in use. [Sign in instead?]" — "Sign in instead?" is a tappable inline link
- Network error: bottom sheet "No connection. Check your internet and try again." with "Retry" button
- Server error: same sheet, "Something went wrong. Try again in a moment."

**Platform differences**:
- **[iOS]**: "Sign in with Apple" must appear as first social option (App Store requirement)
- **[Android/Web]**: Google sign-in only

---

### Screen 1.4 — Email Verification

**Layout**:
- Headline: "Check your email"
- Body: "We sent a 6-digit code to [email]. Enter it below."
- 6-box OTP input (auto-advance on each digit, auto-submit on 6th)
- "Resend code" link — disabled for 60 seconds, shows countdown ("Resend in 0:43")
- "Wrong email? Go back" link

**Actions**:
- Enter 6 correct digits → auto-submit → if payer: Screen 1.5 (Phone verification)
- "Resend code" → POST /auth/resend-otp → shows "Code sent" toast
- "Wrong email?" → navigate back to Screen 1.3, preserve name field

**Error states**:
- Wrong code: shake animation on input boxes, "Incorrect code. Try again." — do NOT clear the input
- Expired code (10 min): "Code expired. Request a new one." — "Resend code" link re-enabled immediately
- Max attempts (5): lock screen for 10 minutes, show countdown, disable all input

**Platform differences**:
- **[iOS/Android]**: SMS autofill for OTP if user entered phone (not applicable here — email OTP); still, iOS will attempt to read code from email app via AutoFill Credential Provider if user has Mail configured
- **[Web]**: Standard OTP input; no autofill

---

### Screen 1.5 — Phone Number (Optional, Payer)

**Layout**:
- Headline: "Add your phone number"
- Subtext: "For payment alerts and account recovery. You can skip this."
- Field: Country code picker + phone number
- CTA: "Continue"
- Skip link: "Skip for now"

**Rationale**: Phone is optional at signup but required for SMS payment notifications. Collecting it here is lower friction than re-prompting later.

**Actions**:
- Enter phone + "Continue" → POST /user/phone → send SMS OTP → Screen 1.5a (SMS OTP)
- "Skip for now" → Screen 1.6 (Stripe Connect)

**Error states**:
- Invalid phone format: "Enter a valid phone number"
- Number already registered to another account: "That number is in use on another account. [Contact support]"

---

### Screen 1.5a — SMS OTP

Same layout as Screen 1.4 but for SMS. Resend delay 60 seconds. On success → Screen 1.6.

---

### Screen 1.6 — Stripe Connect Express Onboarding (Payer)

**Context**: The payer must complete Stripe Connect onboarding to send ACH payments. This is a Stripe-hosted flow.

**Layout**:
- Headline: "Connect your bank account"
- Body: "To send payments, we need to verify your identity and link your bank. This is handled securely by Stripe."
- Trust signals: Stripe logo, "Bank-level security", "Your data is never stored on FairBridge servers"
- CTA: "Connect bank"
- Skip link: "Do this later" (payer can explore the app but cannot send payments)

**Actions**:
- Tap "Connect bank" → open Stripe Connect Express flow:
  - **[iOS]**: `SFSafariViewController` (in-app browser, shares cookies with Safari)
  - **[Android]**: Chrome Custom Tab
  - **[Web]**: Full-screen modal iframe or redirect
- Stripe flow completes → deeplink back to app → Screen 1.6a (Bank linked confirmation)
- "Do this later" → Screen 1.7a (Home — payments locked state)

**Error states**:
- Stripe KYC rejected: Stripe handles the error screen; user returns to app with status "verification_failed"; show bottom sheet "We couldn't verify your identity. Contact Stripe support." with link
- User closes browser mid-flow: app receives no callback; show bottom sheet "Bank connection incomplete. Try again?" with "Continue" and "Later" options
- Network error opening browser: "Couldn't open bank setup. Check your connection."

**Platform differences**:
- **[iOS]**: `SFSafariViewController` — cookies shared with Safari, so users signed into their bank via Safari don't need to re-enter credentials
- **[Android]**: Chrome Custom Tab — similar cookie sharing, but only if Chrome is default browser; fall back to `openURL` if Chrome not installed
- **[Web]**: Stripe Connect modal embedded in page; no browser context switching

---

### Screen 1.6a — Bank Linked Confirmation

**Layout**:
- Success illustration (checkmark animation)
- Headline: "Bank connected"
- Body: "You're ready to send payments. Now let's invite your co-parent."
- CTA: "Invite co-parent"

**Actions**:
- Tap "Invite co-parent" → Screen 1.8 (Co-parent invite)

---

### Screen 1.7a — Home (Payments Locked State)

For payers who skipped bank linking. Home screen shows expenses and calendar but payment button is locked with a banner: "Connect your bank to send payments." Tap banner → Screen 1.6.

---

### Screen 1.8 — Co-Parent Invite

**Layout**:
- Headline: "Invite your co-parent"
- Body: "Enter their name and email. We'll send them a link to claim any payments you send."
- Fields: Co-parent's first name, Co-parent's email
- CTA: "Send invite"
- Alternative: "Share invite link" (copies a URL to clipboard or opens share sheet)

**Privacy note**: The invite email subject line and preview do NOT contain the sender's name or "co-parent" language — it reads "You have money waiting" to avoid alerting anyone who might be monitoring the recipient's email. Full DV safety rationale in Flow 7.

**Asymmetric verification** (runs silently in background, does not block UX):
- After invite is sent, payer is prompted on Screen 1.9 to enter the children's names and dates of birth
- Payee is prompted for the same data on their onboarding (Flow 2, Screen 2.6)
- Backend matches these independently — if they don't match within 72 hours, a soft warning is shown to payer only (not payee)

**Actions**:
- Tap "Send invite" → POST /invites → success → Screen 1.9 (Child verification)
- Tap "Share invite link" → GET /invites/link → system share sheet / clipboard
- Skip ("Do this later" link) → Home

**Error states**:
- Invalid email: inline error
- Email already has a FairBridge account: "That email already has an account. We've sent them a connection request instead." — flow continues identically
- Network error: retry sheet

---

### Screen 1.9 — Child Verification (Payer Side)

**Layout**:
- Headline: "Tell us about your children"
- Body: "This helps us verify the connection with your co-parent. We never share this with them."
- Fields: Child 1 first name, Child 1 date of birth (date picker)
- "Add another child" link (for multiple children)
- CTA: "Save"
- Skip link: "Skip for now"

**Actions**:
- "Save" → POST /family/children → Home (onboarding complete for payer)
- "Skip" → Home (verification deferred; soft reminder shown after 72h if payee completes theirs)

---

### Screen 1.10 — First Expense Entry

Accessible from Home via the "+" FAB (floating action button).

**Layout**:
- Bottom sheet slides up (modal)
- Headline: "Add expense"
- Fields:
  - Amount (numeric keypad, auto-shows on focus)
  - Category (segmented control or dropdown): Medical, Education, Activities, Childcare, Clothing, Food, Other
  - Description (optional text field, 140 char limit)
  - Date (defaults to today; date picker on tap)
  - Receipt (optional photo attach): "Add receipt" button → camera or photo library
  - Split ratio (defaults to 50/50; adjustable via slider or "Custom" field showing "You pay X% / Co-parent pays Y%")
- CTA: "Add expense"
- Cancel (top left)

**Actions**:
- Tap "Add expense" → POST /expenses → expense appears in list → offer to "Request payment now" or "Add another expense"
- Receipt photo → compress to JPEG ≤1MB → upload to Cloudflare R2 → attach URL to expense
- Cancel → dismiss sheet (no data saved)

**Error states**:
- Amount = 0 or empty: "Enter an amount"
- Network error on save: local draft saved to device; banner "Saved offline — will sync when connected"
- Receipt upload fails: "Receipt upload failed. Expense saved without receipt. Retry?" — "Retry" re-attempts upload only

**Platform differences**:
- **[iOS]**: Bottom sheet with native `UIImagePickerController` for photo; supports Live Photo (converted to JPEG)
- **[Android]**: Bottom sheet; `ImagePicker` from Expo; some devices show camera app instead of inline picker
- **[Web]**: Modal dialog; `<input type="file" accept="image/*">` for receipt

---

### Screen 1.11 — Payment Request / Settlement

After expenses accumulate, payer initiates a payment.

**Layout**:
- "Outstanding balance" card on Home: "You owe [co-parent name] $[X]" based on 50/50 split of logged expenses
- CTA: "Pay now"
- Secondary: "View breakdown"

**Tap "Pay now"**:
- Bottom sheet with payment summary:
  - List of included expenses (scrollable)
  - Total amount
  - "Payment to: [Co-parent name] ****[last 4 of bank]"
  - Estimated arrival: "2–3 business days via ACH"
  - CTA: "Confirm payment"
  - Cancel

**Actions**:
- "Confirm payment" → POST /payments → payment_intent created → Screen 1.12 (Payment sent)
- Cancel → dismiss

**Error states**:
- Payer bank not linked: redirect to Screen 1.6
- Payee bank not linked: "Your co-parent hasn't set up their bank yet. We'll send them a reminder." — payment is queued, not sent
- Payment amount below Stripe minimum ($1): "Minimum payment is $1.00"
- ACH return (R01 insufficient funds, etc.): push notification "Payment returned — insufficient funds"; Screen shows "Payment failed" with retry option

---

### Screen 1.12 — Payment Sent Confirmation

**Layout**:
- Success animation
- Headline: "Payment sent"
- Body: "$[X] is on the way to [co-parent name]. It should arrive in 2–3 business days."
- Timeline visual: Today → Processing → Arrived (with animated progress)
- CTA: "Done"

---

## Flow 2: Payee "Money Waiting" Invite → Signup → Bank Linking → Receive First Payment

**This is the critical funnel. Every screen that can be eliminated must be eliminated. Design target: >50% completion rate from invite link open to first payment received.**

### Design Principles for This Flow

1. Lead with the money. The payee's primary motivator is receiving funds. Every screen must reinforce "your money is waiting."
2. No account required to understand value. The landing page shows the amount waiting without requiring login.
3. Bank linking is the hardest step — place it last, after identity investment (name, email) is already complete.
4. Minimize typing. Pre-fill everything possible from the invite token.
5. Never use the words "co-parent," "custody," or "divorce" in the payee funnel — these trigger anxiety and legal concern for some users.

---

### Screen 2.0 — "Money Waiting" Landing Page (Web, opens from invite link)

**Trigger**: Payee taps invite link in email/SMS. Link opens in mobile browser (not app — app may not be installed yet).

**URL**: `https://fairbridge.app/claim/[token]`

**Layout**:
- No nav bar, no marketing header
- Prominent dollar amount: "$[X] is waiting for you"
- Sent by: "[Payer first name]" (NOT last name, not "your co-parent")
- Brief explanation: "Accept this transfer and get paid directly to your bank."
- Single CTA: "Claim your money" (large, primary button — above the fold on all phone sizes)
- Tiny fine print below: "Free to use. No credit card required."

**The amount shown is real** — pulled from the payer's pending payment linked to this invite token. If no payment has been queued yet (payer sent an invite without queuing a payment), show: "Your co-parent has invited you to split expenses and receive payments." — fallback messaging without a specific dollar amount.

**Actions**:
- Tap "Claim your money" → if mobile app installed: deeplink to Screen 2.1 in app; if not installed: Screen 2.2 (in-browser signup)
- App install detection: use `intent://` on Android, Universal Link on iOS; fall back to in-browser after 1.5 second delay

**Error states**:
- Token expired (>30 days): "This invite has expired. Ask your co-parent to resend it."
- Token already claimed: "This invite has already been used. [Sign in to your account]"
- Network error: "Couldn't load your payment details. Check your connection." with Retry

---

### Screen 2.1 — App Download Prompt (if app not installed)

Only shown if the deeplink fails (app not installed) and user is on mobile.

**Layout**:
- Minimal screen: "Download FairBridge to receive your payment"
- App Store / Google Play badge
- Alternative: "Continue in browser instead" link — preserves the invite token in session storage

**Actions**:
- Tap store badge → opens App Store / Play Store
- "Continue in browser" → Screen 2.2 (in-browser signup — full web flow)
- When app opens after install: deeplink resumes at Screen 2.2 (in-app)

---

### Screen 2.2 — Quick Signup (Payee)

**Layout**:
- Headline: "$[X] is waiting — create an account to receive it"
- Fields (minimal):
  - Email (pre-filled from invite if available)
  - Password (show/hide)
- CTA: "Create account & claim"
- Social login: "Continue with Apple" **[iOS]**, "Continue with Google"
- Fine print: Terms + Privacy links

**No phone number required here.** Phone is collected post-bank-linking when the user is already invested.

**Actions**:
- "Create account & claim" → POST /auth/register (with invite_token in body) → Screen 2.3 (Email verification)
- Social login → OAuth → account created with invite_token linked → skip email verification → Screen 2.4 (Name collection)

**Error states**: Same as Screen 1.3.

---

### Screen 2.3 — Email Verification (Payee)

Same layout as Screen 1.4. On success → Screen 2.4.

**Shortcut**: If payee used social login (Apple/Google), skip this screen entirely — email already verified.

---

### Screen 2.4 — Name Collection (Payee)

**Layout**:
- Headline: "What's your name?"
- Single field: First name + Last name (single field, split on first space)
- CTA: "Continue"

**Why collected separately**: Reduces the perceived length of the signup form on Screen 2.2. Users who see only "email + password" have higher completion than those who see "email + password + name + phone."

**Actions**:
- "Continue" → PATCH /user/profile → Screen 2.5 (Bank linking)

---

### Screen 2.5 — Bank Linking (Payee) — THE CRITICAL SCREEN

**Layout**:
- Headline: "Where should we send your $[X]?"
- Body: "Link your bank account to receive the transfer. Takes about 2 minutes."
- Trust signals (above the fold):
  - Stripe logo + "Secured by Stripe"
  - "256-bit encryption"
  - "We never store your banking credentials"
- CTA: "Link my bank" (large, primary)
- Secondary: "How does this work?" (expandable FAQ inline — no navigation away from screen)

**FAQ answers (collapsed by default)**:
- "Is this safe?" → "Your bank credentials go directly to Stripe, a company that processes payments for Amazon, Google, and millions of other businesses. FairBridge never sees your login."
- "How long does it take?" → "2–3 business days for the first transfer. Subsequent transfers may be faster."
- "What bank accounts work?" → "Any US checking or savings account."
- "Is there a fee?" → "No fee for receiving payments."

**Actions**:
- Tap "Link my bank" → open Stripe Financial Connections (hosted by Stripe):
  - **[iOS]**: `SFSafariViewController` or Stripe native SDK sheet
  - **[Android]**: Chrome Custom Tab
  - **[Web]**: Stripe Financial Connections modal
- Stripe flow completes → deeplink/callback → Screen 2.6 (Child verification — optional)

**Error states**:
- Bank not found in Financial Connections: Stripe offers manual routing/account number entry as fallback — FairBridge passes `collection_options: { payment_method_types: ['us_bank_account'] }` to allow manual entry
- User closes Stripe mid-flow: bottom sheet "Your bank isn't linked yet. The payment can't be sent until you connect a bank." with "Try again" and "Do this later" options
- Bank linking failed (Stripe error): "We couldn't connect to [Bank Name]. Try a different account or [enter details manually]."

**If "Do this later"**: payment remains queued; push notification and email sent after 24 hours reminding payee to link bank.

---

### Screen 2.6 — Child Verification (Payee, Optional)

Same layout as Screen 1.9. Headline: "Tell us about your children — this takes 30 seconds."

This screen appears AFTER bank linking so it doesn't block the critical conversion path.

**Actions**:
- "Save" or "Skip" → Screen 2.7 (Payment on the way)

---

### Screen 2.7 — Payment Confirmation (Payee)

**Layout**:
- Success illustration
- Headline: "Payment on its way!"
- Body: "$[X] from [Payer first name] will arrive in 2–3 business days to [Bank name] ****[last 4]"
- Timeline visual: Sent → Processing → Arrives [date]
- CTA: "View my account"
- Secondary: "Set up notifications" — taps into Flow 8 (notification permission)

**This screen is the payee's first success moment. The app should feel rewarding here — not clinical.**

---

### Payee Funnel Step Count Summary

| Step | Screen | Skip possible? |
|------|--------|---------------|
| 1 | Landing page: "Money waiting" | — |
| 2 | Quick signup (email + password) | Social login shortcut |
| 3 | Email OTP verification | Skipped with social login |
| 4 | Name collection | — |
| 5 | Bank linking (Stripe) | "Later" available but delays payment |
| 6 | Child verification | Optional / skippable |
| 7 | Payment confirmation | — |

**Total required screens (no shortcuts)**: 6
**With social login**: 4
**Competitor baseline (OFW)**: 8+ screens before first action

---

## Flow 3: Expense Submission → Two-Party Confirmation → Payment Settlement

This flow handles the recurring lifecycle of expenses shared between co-parents after both are onboarded.

### Screen 3.1 — Expense Submission

Same as Screen 1.10, but both parties can submit expenses.

**Key addition for payee-submitted expenses**: When the payee submits an expense, the payer receives a notification: "[Payee name] added an expense: $[X] for [category]. Review it."

---

### Screen 3.2 — Two-Party Confirmation (Payer Reviews Payee-Submitted Expense)

**Layout**:
- Notification tap → opens expense detail screen
- Expense summary: amount, category, description, date, receipt thumbnail (if provided)
- Status badge: "Pending your review"
- Actions:
  - "Approve" (primary green button)
  - "Dispute" (secondary, outlined red button)

**Approve flow**:
- POST /expenses/[id]/approve → expense status = "approved"
- Toast: "Expense approved"
- If payment balance is >$0, smart nudge: "You have $[X] outstanding. Pay now?" with "Pay" and "Later" buttons

**Dispute flow** → Flow 6.

---

### Screen 3.3 — Expense List (Ledger View)

**Layout**:
- Chronological list with date groupings
- Each row: category icon, description, amount, status chip (Pending / Approved / Disputed / Settled)
- Filter bar: All | Pending | Settled
- Outstanding balance banner at top: "Balance: You owe $[X]" or "Co-parent owes you $[X]"

**Tap any expense** → Expense detail modal (shows full info + audit trail: submitted by, submitted at, approved by, approved at, receipt)

---

### Screen 3.4 — Settlement (Recurring)

Triggered from "Pay now" nudge or from the balance banner.

**Layout**: Same as Screen 1.11. After first payment, this is the standard recurring settlement screen.

**Recurring settlement**: Users can opt into a "Pay automatically on the 1st of each month" toggle. If enabled:
- BullMQ job runs on the 1st
- Initiates ACH payment for outstanding balance
- Sends push notification: "Automatic payment of $[X] initiated"
- User can cancel within 1 hour (cancel window) via notification action button

---

## Flow 4: External Payment Logging (Venmo / Zelle / Check / Cash)

For situations where the payer sends money through another channel and wants to log it in FairBridge for record-keeping.

### Screen 4.1 — Log External Payment

**Access**: Home → "+" FAB → "Log external payment" option (secondary, below "Add expense")

**Layout**:
- Headline: "Log a payment you already made"
- Fields:
  - Amount
  - Method (segmented control): Venmo | Zelle | Check | Cash | Other
  - Date (defaults to today)
  - Note (optional, 140 chars)
  - If Venmo/Zelle: "Transaction ID" optional field (for reference)
  - If Check: "Check number" optional field
- CTA: "Log payment"

**Actions**:
- "Log payment" → POST /payments/external → payment logged as "external" type with method tag
- Logged payment appears in ledger with a different icon (no ACH icon — uses method icon instead)
- Reduces outstanding balance

**Important**: External payments are NOT verified by FairBridge. Both parties see them in the ledger, but either party can dispute them (see Flow 6). The append-only hash chain records both the log entry and any dispute.

**Co-parent notification**: "[Payer name] logged a $[X] [method] payment. If this is incorrect, tap to dispute."

**Error states**:
- Amount = 0: "Enter an amount"
- Network error: local draft; same offline behavior as expense entry

---

## Flow 5: Calendar Setup → Custody Pattern Selection → Co-Parent Confirmation

### Screen 5.1 — Calendar Introduction

**Trigger**: Home → "Calendar" tab → first visit

**Layout**:
- Brief illustration of a two-color calendar
- Headline: "Track your custody schedule"
- Body: "See who has the kids on any given day. Automatically calculates days for support calculations."
- CTA: "Set up calendar"
- Skip: "Not now"

---

### Screen 5.2 — Custody Pattern Selection

**Layout**:
- Headline: "What's your custody schedule?"
- Options (tappable cards with visual preview thumbnails):
  - "2-2-5-5" — alternating weeks with midweek exchanges
  - "Week on / Week off" — simple alternating full weeks
  - "Every other weekend" — primary with limited secondary
  - "60/40" — weighted schedule
  - "Custom" — manual entry
- CTA: "Choose this schedule" on each card (or tap card to select, then "Continue")

**Tap "Custom"** → Screen 5.3 (Manual entry)
**Tap any preset** → Screen 5.4 (Start date and assignment)

---

### Screen 5.3 — Custom Schedule Builder

**Layout**:
- 2-week grid (Mon–Sun × 2 rows)
- Each day cell is tappable — cycles through: You | Co-parent | Split
- Color coding: blue = user, orange = co-parent, striped = split day
- CTA: "This repeats every [X] weeks" — stepper to set cycle length (2, 3, or 4 weeks)
- "Save pattern"

---

### Screen 5.4 — Schedule Start Date and Assignment

**Layout**:
- Headline: "When does this schedule start?"
- Date picker (defaults to next Monday)
- "Who has the kids first?" toggle: "Me" or "[Co-parent name]"
- CTA: "Continue"

---

### Screen 5.5 — Send Calendar for Co-Parent Confirmation

**Layout**:
- Calendar preview (read-only, showing the configured pattern)
- Headline: "Share with your co-parent to confirm"
- Body: "We'll ask [co-parent name] to confirm this schedule. You can start using the calendar while you wait."
- CTA: "Send for confirmation"
- Skip: "Skip confirmation"

**Actions**:
- "Send for confirmation" → POST /calendar/share → notification sent to co-parent → Screen 5.6 (Pending confirmation state)
- "Skip confirmation" → calendar goes live for payer only (co-parent cannot see it until they confirm or are not invited)

---

### Screen 5.6 — Calendar Pending Confirmation

Calendar is visible to user with a banner: "[Co-parent name] hasn't confirmed yet. Reminders sent." Tap banner → option to resend reminder.

---

### Screen 5.7 — Co-Parent Calendar Confirmation (Payee Side)

**Trigger**: Payee receives push notification "Review your custody calendar"

**Layout**:
- Full calendar view with the proposed schedule
- "Does this look right?" prompt
- Action buttons: "Yes, confirm" | "No, suggest changes"

**"Yes, confirm"** → POST /calendar/confirm → both parties see confirmed calendar
**"No, suggest changes"** → text field ("What needs to change?") → sends message to payer via in-app message thread; calendar remains unconfirmed

---

## Flow 6: Dispute Workflow

Disputes can be raised on: expenses (any type), external payment logs, or ACH payments (Reg E financial disputes).

### Screen 6.1 — Initiate Dispute (Expense)

**Trigger**: On expense detail screen, tap "Dispute"

**Layout**:
- Bottom sheet
- Headline: "What's wrong with this expense?"
- Radio options:
  - "I didn't agree to this expense"
  - "The amount is wrong"
  - "This was already paid another way"
  - "Other"
- If "Other": text field (required, 20–500 chars)
- CTA: "Submit dispute"
- Cancel

**Actions**:
- "Submit dispute" → POST /disputes → expense status = "disputed" → notification sent to other party → Screen 6.2

**Important note for ACH payment disputes (Reg E)**: If the dispute is on an ACH transfer (not just an expense), a Reg E intake form is shown instead (Screen 6.1b). The dispute is also flagged to the backend for manual review within 24 hours per Reg E requirements.

---

### Screen 6.1b — Reg E Dispute Intake (ACH Payments Only)

**Layout**:
- Headline: "Report a payment problem"
- Body: "Federal law (Regulation E) protects you for unauthorized or incorrect bank transfers."
- Fields:
  - "What happened?" (radio): Unauthorized transfer | Wrong amount | Transfer never received | Other
  - "When did you first notice?" (date picker)
  - Description (required, min 20 chars)
- Notice: "We'll review this within 1 business day. You may be asked to provide additional documentation."
- CTA: "Submit report"

---

### Screen 6.2 — Dispute Submitted (Initiator View)

**Layout**:
- Status: "Dispute submitted" with timestamp
- Expense/payment details
- Timeline: Dispute submitted → Awaiting response → Resolved
- "Add more information" button (upload photo or add note)
- Notification that the other party has 7 days to respond

---

### Screen 6.3 — Dispute Received (Respondent View)

**Trigger**: Push notification "[Name] has disputed an expense"

**Layout**:
- Dispute details: reason given by disputing party
- Expense detail (amount, category, description, receipt if any)
- Response options:
  - "Accept the dispute" (expense is voided or amount corrected)
  - "Provide counter-evidence" (upload receipt, add explanation)
  - "Request a call" (opens device phone app with co-parent's number if shared — optional feature)

---

### Screen 6.4 — Counter-Evidence Submission

**Layout**:
- Text field: "Explain your position" (required, 20–500 chars)
- Photo upload: "Attach receipt or documentation" (max 3 photos)
- CTA: "Submit response"

**Actions**:
- "Submit response" → POST /disputes/[id]/respond → photos uploaded to R2 → disputing party notified → dispute status = "under review"

---

### Screen 6.5 — Dispute Resolution

If both parties reach agreement → one party marks "Resolved" → expense status updated, hash chain appended.

If no resolution after 14 days → dispute is marked "Unresolved" → both parties see: "This dispute is unresolved. Export your records for mediation." with one-tap PDF export link.

**No FairBridge arbitration in V1** — the app is a record-keeper, not a court. Unresolved disputes stay in the ledger as "disputed" and do not block other functionality.

---

## Flow 7: DV Safety Flows

**Non-negotiable for V1.** Domestic violence safety features must be present at launch. They must be discoverable but not prominent — users should not feel they are being categorized as victims.

### Design Principle: "Safety by Default, Invisible Until Needed"

DV safety features are present but not highlighted. A user who doesn't need them will never encounter them. A user who does need them can find them within 3 taps from Settings.

---

### Screen 7.1 — Silent Deactivation

**Access**: Settings → Privacy & Safety → "Deactivate account silently"

**Layout**:
- Headline: "Deactivate without alerting anyone"
- Body: "Your account will be deactivated. Your co-parent will not be notified. They will see expenses as 'undeliverable' and payments as 'pending.'"
- "What happens to my data?" expandable: "Your data is retained for 90 days, then permanently deleted. You can request immediate deletion below."
- CTA: "Deactivate silently" (red, requires confirmation)
- Confirmation: "Type DEACTIVATE to confirm" text field + "Confirm" button

**What "silent" means**:
- No email sent to any party
- No notification sent to co-parent
- Account moves to "suspended" state server-side
- Co-parent's app shows expenses as "undeliverable" (generic error — does NOT say "account deactivated")
- No FairBridge employee proactively contacts either party
- User can reactivate by logging back in within 90 days

---

### Screen 7.2 — Data Export

**Access**: Settings → Privacy & Safety → "Export my data"

**Layout**:
- "What's included": expense records, payment history, calendar, receipts, messages
- Format: PDF (court-formatted) + CSV (raw data)
- CTA: "Generate export"
- Note: "Export is encrypted and sent to [email on file]. It does not notify your co-parent."

**Actions**:
- "Generate export" → POST /user/export → background job generates ZIP (PDF + CSVs) → email delivered to user's email address only
- ZIP contains: SHA-256 hash of each record for tamper-evident verification

---

### Screen 7.3 — Data Deletion

**Access**: Settings → Privacy & Safety → "Delete my account and all data"

**Layout**:
- Warning: "This is permanent. All your records, expenses, and payment history will be deleted. Your co-parent will lose access to shared records."
- Alternative: "Download your data first" link (→ Screen 7.2)
- CTA: "Delete everything" (red)
- Confirmation: "Type DELETE to confirm" + Confirm button

**What happens**:
- All user records, expenses, payments, calendar events purged
- Shared records (with co-parent) become "submitted by deleted user" — co-parent retains their copy
- Stripe Connect account deauthorized
- Confirmation email sent to user's email only (not co-parent)

---

### Screen 7.4 — Safety Resources

**Access**: Settings → Privacy & Safety → "Safety resources" OR via panic trigger (see below)

**Layout**:
- National Domestic Violence Hotline: 1-800-799-7233
- Text line: Text START to 88788
- Chat: thehotline.org (opens in browser)
- "Safety planning" link (external resource — opens browser)
- "Quick exit" button (prominent, red) → immediately closes app, clears recent history in app switcher **[iOS]**, clears recents **[Android]**

**Panic trigger (hidden)**:
- Tapping the FairBridge logo in Settings header 5 times rapidly → goes directly to Screen 7.4
- No visual indication this gesture exists — discoverable only if user is told about it
- **[iOS]**: Also clears app from recent apps if possible via `UIApplication.shared.perform(#selector(URLSessionTask.suspend))` workaround
- **[Android]**: `moveTaskToBack(true)` + clear recents if API 21+

---

### Invisible Safety Defaults (No User Action Required)

These are architectural defaults, not UI flows, but they affect every screen:

1. **No activity timestamps exposed to co-parent**: "Last seen" or "last active" data is never shown to the other party.
2. **Invite email subject**: "You have money waiting" — no "co-parent" or sender name in preview
3. **Push notification preview**: Payment and expense notifications show amounts only, not sender name (to avoid exposing relationship to device bystanders)
4. **Screenshot protection** **[iOS]**: `isProtectedDataAvailable` check; app blurs on App Switcher preview
5. **Screenshot protection** **[Android]**: `FLAG_SECURE` on all screens containing financial data

---

## Flow 8: Notification Permission Gates

Notifications are critical for the two-party confirmation model — if the payee doesn't get notified about payments, the app fails. But requesting permissions too early kills grant rates.

### Permission Request Timing

**Rule**: Never request notification permission on first launch or during account creation. Request at a moment of clear value.

| Trigger | When to ask | Expected grant rate |
|---------|-------------|-------------------|
| After payer sends first payment | "Get notified when your payment arrives" | ~70% (high motivation) |
| After payee bank is linked | "Get notified when the transfer arrives" | ~75% |
| After expense is added | "Get notified when your co-parent reviews it" | ~55% |

---

### Screen 8.1 — Pre-Permission Rationale Screen (iOS)

**[iOS only]** — iOS allows only ONE system permission prompt per app lifetime. A pre-permission rationale screen is shown first to filter out users who would deny.

**Layout**:
- Illustration: phone with notification badge
- Headline: "Stay on top of payments"
- Body: "We'll let you know when you're paid, when expenses are added, and when your co-parent responds. You can change this anytime in Settings."
- CTA: "Turn on notifications" → triggers iOS system dialog
- Secondary: "Not now" → skips; no system dialog shown (preserving the one-shot iOS prompt for a better moment)

**If user taps "Not now"**: tracked; shown again after second meaningful action (e.g., second payment sent).

---

### Screen 8.2 — iOS System Notification Prompt

**[iOS only]** — standard system dialog triggered after Screen 8.1. FairBridge has no control over this UI.

**On grant**: POST /user/push-token with APNs device token.
**On deny**: soft fallback — "You can enable notifications anytime in iPhone Settings > FairBridge." Banner shown once.

---

### Screen 8.3 — Android Notification Permission (API 33+)

**[Android API 33+ only]** — Android 13+ requires explicit `POST_NOTIFICATIONS` permission. On older Android, notifications are granted by default.

Same two-step approach as iOS:
1. Pre-permission rationale screen (same design as Screen 8.1)
2. System dialog: `ActivityCompat.requestPermissions(POST_NOTIFICATIONS)`

On deny:
- Android allows re-requesting (up to 2 times before "Don't ask again" is shown)
- After first deny: "You can enable notifications in Android Settings." — inline banner, not blocking
- After "Don't ask again": same message; "Open Settings" button links directly to app notification settings

---

### Screen 8.4 — In-App Notification Preferences

**Access**: Settings → Notifications

**Layout**:
- Toggle list:
  - Payments (required — cannot disable if using payments feature)
  - Expenses (on by default)
  - Calendar (on by default)
  - Reminders (on by default)
  - Disputes (on by default)
- Each toggle has a brief description of what it controls
- "Manage in phone Settings" link for OS-level control

**[iOS/Android]**: If OS-level permission is denied, all toggles are greyed out with message: "Notifications are disabled in your device settings. [Open Settings]"

---

## Flow 9: Android Battery Optimization Exemption

**[Android only]** — Android's battery optimization (Doze mode) kills background processes and delays FCM push notifications. On some manufacturers (Huawei, Xiaomi, Samsung with aggressive battery management), critical payment notifications may be delayed hours or not delivered at all.

### Screen 9.1 — Battery Optimization Prompt

**Trigger**: Shown once, after notification permissions are granted on Android, before leaving the onboarding flow.

**Layout**:
- Headline: "Ensure you never miss a payment notification"
- Body: "Some Android phones delay or block notifications to save battery. Allow FairBridge to run reliably in the background."
- CTA: "Allow background activity" → triggers OS dialog for battery optimization exemption
- Secondary: "Skip" — user can skip; shown again after first missed notification (detected via delivery receipt)

**OS dialog trigger**:
```
Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
intent.setData(Uri.parse("package:" + getPackageName()));
startActivity(intent);
```

**Manufacturer-specific handling**:
- **Samsung**: Additional AutoStart permission required; if Samsung device detected, add step: "On Samsung, also enable AutoStart in Settings > Apps > FairBridge > Battery > Allow background activity"
- **Huawei/Honor**: Similar AutoStart prompt
- **Other OEMs**: Generic prompt; link to dontkillmyapp.com for device-specific instructions

---

### Screen 9.2 — Battery Exemption Confirmation

After OS dialog:
- Granted: Toast "Background notifications enabled" — continue to home
- Denied: "Payment notifications may be delayed. You can change this in Android Settings." — no blocking; continue to home

---

## Flow 10: Error States

### 10.1 — Offline / No Connection

**Detection**: Network status monitor (NetInfo in Expo); show persistent banner when offline.

**Banner** (top of screen, non-dismissible while offline):
- "No internet connection — working offline"
- When reconnected: banner changes to "Back online" for 2 seconds, then disappears

**Offline-capable actions** (local draft saved):
- Add expense
- View expense list (cached)
- View calendar (cached)

**Not offline-capable** (show inline error on attempt):
- Send payment: "Payment requires a connection. Try again when online."
- Log in / sign up
- Link bank

---

### 10.2 — Payment Failed

**Trigger**: Stripe webhook `payment_intent.payment_failed` or ACH return code received.

**User-facing notification** (push + in-app):
- Title: "Payment didn't go through"
- Body: "Your $[X] payment to [co-parent] failed. Tap to retry."

**Screen — Payment Failed Detail**:
- Amount, date, recipient
- Failure reason (user-friendly, NOT Stripe's raw error):
  - R01 (insufficient funds): "Your bank account had insufficient funds."
  - R02 (account closed): "The destination account appears to be closed. Ask your co-parent to update their bank."
  - R03/R04 (no account): "We couldn't find that bank account. Ask your co-parent to re-link their bank."
  - Generic Stripe failure: "Payment declined. Contact your bank for details."
- CTA: "Retry payment" (re-initiates the same ACH amount)
- Secondary: "Contact support"

**Retry logic**: User-initiated only (no automatic retry on ACH returns — Nacha rules prohibit retrying R01 more than 2 times).

---

### 10.3 — Bank Linking Failed

**Trigger**: Stripe Financial Connections returns an error; user returns from Stripe flow with error callback.

**Screen**:
- Headline: "Bank connection failed"
- Error-specific messaging:
  - Bank not supported: "Your bank isn't supported yet. Try linking a different account, or enter your routing and account number manually."
  - Login failed: "We couldn't log in to [Bank name]. Make sure your online banking credentials are correct."
  - Timeout: "The connection timed out. Try again."
- CTA: "Try again" (re-opens Financial Connections)
- Secondary: "Enter account details manually" → Stripe manual bank entry (routing + account number)

---

### 10.4 — Notification Permission Denied (Permanent)

**[iOS]**: After denying on the system dialog, the app cannot re-request. Show once:
- Bottom sheet: "Notification permission denied. You can enable notifications in iPhone Settings > Notifications > FairBridge."
- "Open Settings" → `UIApplication.openSettingsURLString`
- Dismiss

**[Android]**: After "Don't ask again":
- Same message with "Open Settings" → `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`

**Fallback**: All notifications also sent as email. If notification permission is denied, email frequency increases (user notified of this change on the settings screen).

---

## Appendix A: Screen Inventory

| Screen ID | Name | Flow |
|-----------|------|------|
| 1.1 | Welcome / Value Prop | Payer onboarding |
| 1.2 | Role Selection | Payer onboarding |
| 1.3 | Account Creation | Payer onboarding |
| 1.4 | Email OTP Verification | Payer onboarding |
| 1.5 | Phone Number (Optional) | Payer onboarding |
| 1.5a | SMS OTP | Payer onboarding |
| 1.6 | Stripe Connect Express | Payer onboarding |
| 1.6a | Bank Linked Confirmation | Payer onboarding |
| 1.7a | Home (Payments Locked) | Payer onboarding |
| 1.8 | Co-Parent Invite | Payer onboarding |
| 1.9 | Child Verification | Payer onboarding |
| 1.10 | First Expense Entry | First expense |
| 1.11 | Payment Request | First payment |
| 1.12 | Payment Sent Confirmation | First payment |
| 2.0 | Money Waiting Landing (Web) | Payee onboarding |
| 2.1 | App Download Prompt | Payee onboarding |
| 2.2 | Quick Signup | Payee onboarding |
| 2.3 | Email OTP Verification | Payee onboarding |
| 2.4 | Name Collection | Payee onboarding |
| 2.5 | Bank Linking (Payee) | Payee onboarding |
| 2.6 | Child Verification (Payee) | Payee onboarding |
| 2.7 | Payment Confirmation | Payee onboarding |
| 3.1 | Expense Submission | Two-party confirmation |
| 3.2 | Two-Party Confirmation | Two-party confirmation |
| 3.3 | Expense List / Ledger | Two-party confirmation |
| 3.4 | Settlement (Recurring) | Payment settlement |
| 4.1 | Log External Payment | External payment |
| 5.1 | Calendar Introduction | Calendar setup |
| 5.2 | Custody Pattern Selection | Calendar setup |
| 5.3 | Custom Schedule Builder | Calendar setup |
| 5.4 | Schedule Start Date | Calendar setup |
| 5.5 | Send Calendar for Confirmation | Calendar setup |
| 5.6 | Calendar Pending Confirmation | Calendar setup |
| 5.7 | Co-Parent Calendar Confirmation | Calendar setup |
| 6.1 | Initiate Dispute (Expense) | Dispute |
| 6.1b | Reg E Dispute Intake | Dispute |
| 6.2 | Dispute Submitted | Dispute |
| 6.3 | Dispute Received | Dispute |
| 6.4 | Counter-Evidence Submission | Dispute |
| 6.5 | Dispute Resolution | Dispute |
| 7.1 | Silent Deactivation | DV Safety |
| 7.2 | Data Export | DV Safety |
| 7.3 | Data Deletion | DV Safety |
| 7.4 | Safety Resources | DV Safety |
| 8.1 | Pre-Permission Rationale | Notifications |
| 8.2 | iOS System Notification Prompt | Notifications |
| 8.3 | Android Permission (API 33+) | Notifications |
| 8.4 | In-App Notification Preferences | Notifications |
| 9.1 | Battery Optimization Prompt | Android battery |
| 9.2 | Battery Exemption Confirmation | Android battery |

---

## Appendix B: Key UX Design Decisions

| Decision | Rationale |
|----------|-----------|
| No "co-parent" language in payee invite | DV safety; reduces anxiety for conflicted relationships |
| Bank linking is step 5 of 6 in payee funnel (not step 1) | Identity investment before the hard step increases completion |
| Pre-permission rationale screen before iOS notification prompt | Preserve the one iOS prompt for a high-value moment |
| Automatic payment cancel window (1 hour) | Gives users recourse without adding friction to the confirmation step |
| No FairBridge arbitration for disputes | Keeps FairBridge as neutral record-keeper, not judge |
| Silent deactivation (no co-parent notification) | DV safety; prevents retaliation for app usage |
| "Quick exit" button in safety resources | Allows rapid exit if someone is watching user's screen |
| External payments logged but not verified | FairBridge is an evidence layer, not a payment enforcer |
| Phone number optional at signup (collected post-bank-link) | Reduces signup friction; phone is high-anxiety ask for some users |
| Social login skips email OTP | Reduces payee funnel to 4 required steps |

---

## Appendix C: Accessibility Minimums

All screens must meet WCAG 2.1 AA:
- Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- All interactive elements ≥ 44×44pt touch targets **[iOS]**, ≥ 48×48dp **[Android]**
- All amounts readable by VoiceOver **[iOS]** / TalkBack **[Android]** — use `accessibilityLabel` for formatted currency ("42 dollars and 50 cents" not "$42.50")
- No information conveyed by color alone (status chips use both color and text label)
- Dynamic Type support on all text **[iOS]**
- Font scaling support on all text **[Android]**
