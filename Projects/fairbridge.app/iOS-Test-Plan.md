# FairBridge iOS Test Plan

**Version**: 1.1
**Author**: iOS QA
**Date**: 2026-03-17 (updated 2026-03-18)
**Stack**: React Native (Expo) · iOS 16.0 minimum · APNs · Stripe Connect/Financial Connections

---

## Overview

This test plan covers all iOS-specific behaviors for the FairBridge MVP: ACH co-parent payments, append-only expense tracking, and custody calendar. Tests are organized by functional area. Each test case specifies device, iOS version, preconditions, steps, and expected result.

---

## 1. Device and OS Matrix

All test suites must be executed across the following matrix. Mark each cell pass/fail.

| Device | Form Factor | iOS 16 | iOS 17 | iOS 18 |
|---|---|---|---|---|
| iPhone SE (3rd gen) | 4.7" compact | ✓ | ✓ | ✓ |
| iPhone 12 | 6.1" notch | ✓ | ✓ | ✓ |
| iPhone 13 | 6.1" notch | ✓ | ✓ | ✓ |
| iPhone 14 | 6.1" notch | ✓ | ✓ | ✓ |
| iPhone 15 | 6.1" Dynamic Island | ✓ | ✓ | ✓ |

**Simulator coverage**: All matrix cells may use Xcode Simulator for functional tests. Physical device required for: APNs delivery, Keychain biometric, camera capture, NFC-less Stripe OAuth redirect.

**Regression priority**: iPhone 15 / iOS 18 (latest), iPhone SE 3rd / iOS 16 (oldest supported).

---

## 2. APNs Push Notification Delivery

### 2.1 Normal Mode — Payment Notification

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-001 |
| **Priority** | P0 |
| **Device** | iPhone 14, iOS 17 (physical) |

**Preconditions**: App installed, notification permission granted, user authenticated, co-parent has submitted an expense awaiting confirmation.

**Steps**:
1. Place device in normal mode (no Focus active).
2. Lock device screen.
3. Trigger payment notification from backend test harness (send `payment_intent.succeeded` event).
4. Observe lock screen.
5. Tap notification banner.

**Expected**:
- Banner appears within 5 seconds of APNs delivery receipt.
- Notification title: "Payment Received" (or equivalent per copy spec).
- Tapping notification deep-links to the expense detail screen, not app home.
- Sound plays (default APNs sound).

---

### 2.2 Focus Mode — Do Not Disturb

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-002 |
| **Priority** | P1 |

**Preconditions**: Focus mode set to "Do Not Disturb". App NOT in DND allowlist.

**Steps**:
1. Enable Do Not Disturb via Control Center.
2. Send payment notification from test harness.
3. Observe lock screen — no banner expected.
4. Open Notification Center (swipe down).
5. Disable DND.
6. Observe whether notification surfaces.

**Expected**:
- No banner during DND (correct suppression).
- Notification appears in Notification Center while DND is active.
- After DND disabled, notification remains accessible in Notification Center.

---

### 2.3 Focus Mode — Sleep

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-003 |
| **Priority** | P1 |

**Preconditions**: Sleep Focus active (configured via Health app sleep schedule).

**Steps**:
1. Activate Sleep Focus.
2. Send payment notification.
3. Send expense-confirmation notification (time-sensitive category — see 2.6).

**Expected**:
- Standard payment notification suppressed (no banner).
- Time-sensitive expense notification **breaks through** Sleep Focus and displays banner.
- Both notifications appear in Notification Center.

---

### 2.4 Focus Mode — Work

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-004 |
| **Priority** | P2 |

**Steps**: Enable Work Focus (no app allowlist configured). Send all three notification types: payment, expense-confirmation, calendar-reminder.

**Expected**: All suppressed. No banners. All appear in Notification Center.

---

### 2.5 Focus Mode — Personal

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-005 |
| **Priority** | P2 |

**Steps**: Enable Personal Focus. Send all notification types.

**Expected**: All suppressed. No banners. All in Notification Center.

---

### 2.6 Time-Sensitive Notification Behavior

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-006 |
| **Priority** | P0 |

**Preconditions**: Backend marks payment-due-today and expense-confirmation-pending as `interruption-level: time-sensitive` in APNs payload.

**Build requirement**: TestFlight or production build ONLY. `com.apple.developer.usernotifications.time-sensitive` entitlement is present in `FairBridge.entitlements` but is NOT active in debug/simulator builds — `aps-environment: production` is required. Do NOT run this test case against a debug build or Xcode simulator; it will always fail.

**Steps**:
1. Enable any Focus mode (Sleep or DND).
2. Send a notification with `interruption-level: time-sensitive` payload.
3. Observe device.

**Expected**:
- Banner appears even under Focus mode.
- Yellow clock icon visible in notification banner (iOS 15+ time-sensitive indicator).
- Notification listed as "Time Sensitive" in Notification Center grouping.
- User can disable time-sensitive per-app in Settings → Notifications → FairBridge → Time Sensitive (verify toggle is present and functional).

---

### 2.7 Notification Permission Denied — In-App Inbox Fallback

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-007 |
| **Priority** | P0 |

**Preconditions**: App installed with notification permission explicitly denied (Settings → Notifications → FairBridge → Allow Notifications = OFF).

**Steps**:
1. Log in to app.
2. Trigger payment event from test harness.
3. Navigate to in-app inbox (bell icon or dedicated tab).
4. Verify inbox badge count and message content.
5. Tap inbox item.

**Expected**:
- No system notification delivered (correct — permission denied).
- In-app inbox badge increments by 1.
- Inbox shows: sender name, amount, expense description, timestamp.
- Tapping inbox item navigates to expense detail.
- No crash or empty state error.

**Also verify**:
- App does NOT re-prompt for notification permission after denial (must not call `requestAuthorization` again within same session).
- App shows a non-intrusive in-app prompt to re-enable notifications (Settings deeplink) once per install.

---

### 2.8 DV Safety — No Sensitive Data in Push Payload (Lock Screen Privacy)

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-008 |
| **Priority** | P0 — Non-negotiable V1 requirement |
| **Device** | iPhone 14, iOS 17 (physical, locked screen) |

**Context**: DV safety requires that push notification payloads never expose amounts, names, or transaction details on the lock screen — an abuser with physical access to the device must not be able to read financial activity at a glance.

**Steps**:
1. Lock device.
2. Trigger each notification type from test harness: payment received, expense submitted, expense confirmation required, payment failed, dispute opened.
3. Observe lock screen banner for each notification.

**Expected**:
- Notification body contains NO dollar amounts (e.g., must NOT show "$450.00 payment received").
- Notification body contains NO co-parent name.
- Notification body is generic (e.g., "You have a new payment update" or "An expense needs your attention").
- Full details are revealed only after device unlock + app authentication.
- APNs `content-available: 1` (silent push) may be used to trigger in-app badge without lock screen exposure.

**Verify via**: Inspect raw APNs payload in backend test harness. Confirm `alert.body` contains no PII, amounts, or transaction identifiers.

---

### 2.9 DV Safety — SMS Escalation for High-Stakes Events

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-009 |
| **Priority** | P0 |

**Context**: SMS (Twilio) is sent for highest-stakes events only — payment failure and dispute deadline — where missing the notification has financial or legal consequences.

**Steps**:
1. Trigger `payment_intent.payment_failed` event from test harness.
2. Observe: (a) push notification received, (b) after 15 min — email fallback, (c) SMS delivered to registered phone.
3. Trigger dispute deadline approaching (T-24h) event.
4. Observe SMS delivery.

**Expected (payment failure)**:
- SMS received within 60 seconds of event (not after the 15-min email delay — SMS is parallel or immediate for failures).
- SMS body is generic per DV safety: no amounts, no co-parent name. Example: "A payment on FairBridge needs your attention. Open the app for details."
- SMS contains no deeplink that exposes transaction ID in URL (use opaque token if deeplink needed).

**Expected (dispute deadline)**:
- SMS received when dispute deadline is T-24 hours.
- Same DV-safe body constraints apply.

**Expected (routine events)**:
- Expense submitted (non-urgent): NO SMS. Push + email fallback only.
- Calendar reminder: NO SMS.

---

### 2.10 Notification Delivery Cascade — End-to-End Verification

| Field | Value |
|---|---|
| **ID** | IOS-NOTIF-010 |
| **Priority** | P1 |

**Context**: Full cascade: Push → 15-min email fallback → in-app inbox guaranteed. Verify the complete chain on iOS.

**Steps**:
1. Disable push notifications for FairBridge (Settings).
2. Trigger payment event.
3. Wait 15 minutes.
4. Check email (registered address).
5. Open app and check in-app inbox.

**Expected**:
- No push delivered (permission denied).
- Email received within 16 minutes of event (15-min window + delivery latency).
- In-app inbox has notification regardless of push/email status (guaranteed delivery).
- All three contain no sensitive data in subject/body visible without authentication.

---

## 3. Receipt Photo — PHPickerViewController and Camera

### 3.1 PHPickerViewController — Library Selection

| Field | Value |
|---|---|
| **ID** | IOS-PHOTO-001 |
| **Priority** | P0 |
| **iOS versions** | 14, 15, 16, 17, 18 |

**Preconditions**: iOS 14+. App does NOT request full photo library access (uses PHPickerViewController which requires zero permissions).

**Steps**:
1. Open expense submission form.
2. Tap "Add Receipt".
3. Observe permission dialog — **none should appear**.
4. PHPicker sheet slides up.
5. Select a receipt photo from library.
6. Confirm selection.

**Expected**:
- No `NSPhotoLibraryUsageDescription` permission prompt appears (PHPicker is permission-free).
- Selected image is displayed in form as thumbnail.
- Image is compressed to ≤ 2MB before upload (verify via network inspector or log output).
- EXIF GPS metadata stripped before upload (privacy requirement — verify via exiftool on uploaded file).

---

### 3.2 Camera Capture — Quality and Blur Detection

| Field | Value |
|---|---|
| **ID** | IOS-PHOTO-002 |
| **Priority** | P1 |
| **Device** | Physical device only (camera unavailable in Simulator) |

**Preconditions**: `NSCameraUsageDescription` in Info.plist. Camera permission granted.

**Steps**:
1. Tap "Add Receipt" → "Take Photo".
2. Observe `NSCameraUsageDescription` permission prompt on first launch (must appear).
3. Grant camera access.
4. Capture a clear, in-focus receipt photo.
5. Capture a deliberately blurry photo (shake device during capture).

**Expected (clear photo)**:
- Photo accepted, thumbnail shown in form.
- Upload proceeds without error.

**Expected (blurry photo)**:
- App detects blur (using Vision framework `VNDetectImageRequest` or equivalent blur metric).
- User sees inline warning: "Photo appears blurry. Retake for better results?" with Retake / Keep options.
- User can choose to keep blurry photo (not hard-blocked).

**Expected (permission flow)**:
- First-time prompt uses `NSCameraUsageDescription` string from Info.plist.
- If denied, app shows: "Camera access required to capture receipts. Enable in Settings." with Settings deeplink.
- App does NOT crash when camera permission is denied.

---

### 3.3 Photo Upload — File Size and Format Validation

| Field | Value |
|---|---|
| **ID** | IOS-PHOTO-003 |
| **Priority** | P1 |

**Steps**: Select a HEIC image (default iPhone format). Select a PNG. Select a file > 10MB (if possible via Files picker).

**Expected**:
- HEIC converted to JPEG before upload (backend accepts JPEG/PNG only).
- PNG accepted as-is.
- Files > 10MB rejected with clear error message before upload attempt.

---

## 4. Calendar Export — .ics Generation and Apple Calendar Import

### 4.1 .ics File Generation

| Field | Value |
|---|---|
| **ID** | IOS-CAL-001 |
| **Priority** | P1 |
| **iOS versions** | 16, 17, 18 |

**Preconditions**: Custody calendar configured with at least one custody period. `NSCalendarsWriteOnlyAccessUsageDescription` in Info.plist (iOS 17+ write-only access).

**Steps**:
1. Navigate to Calendar tab.
2. Tap "Export to Apple Calendar" (or equivalent).
3. On iOS 17+: observe permission prompt using `NSCalendarsWriteOnlyAccessUsageDescription` string.
4. Grant calendar write-only access.
5. Observe export confirmation.

**Expected**:
- On iOS 17+: permission prompt uses write-only string (not full access string).
- On iOS 16: standard `NSCalendarsUsageDescription` prompt.
- Export succeeds with success toast.
- Calendar events created in Apple Calendar (verify by opening Calendar app).

---

### 4.2 Apple Calendar — Event Content Verification

| Field | Value |
|---|---|
| **ID** | IOS-CAL-002 |
| **Priority** | P1 |

**Steps**: After export (IOS-CAL-001), open Apple Calendar app. Navigate to custody period dates.

**Expected**:
- Events appear in a "FairBridge" calendar (separate calendar, not merged with personal).
- Event title: correct parent name (e.g., "Dad's Time" / "Mom's Time").
- Event spans correct custody dates (all-day events).
- Holiday overlays (if any configured) appear as separate events.
- No duplicate events if export is run twice (idempotent — use event UID matching).

---

### 4.3 Calendar Permission Denied

| Field | Value |
|---|---|
| **ID** | IOS-CAL-003 |
| **Priority** | P1 |

**Steps**: Deny calendar permission when prompted. Attempt calendar export.

**Expected**:
- Export button is disabled or shows permission-required state.
- App shows: "Calendar access required. Enable in Settings." with Settings deeplink.
- App does NOT crash.

---

## 5. Keychain — Token Storage Security

### 5.1 Token Stored with Correct Access Flags

| Field | Value |
|---|---|
| **ID** | IOS-KEYCHAIN-001 |
| **Priority** | P0 |

**Preconditions**: User completes login. Access token and refresh token stored in Keychain.

**Verification method**: Use Xcode → Devices and Simulators → device logs + `security` CLI tool OR use a Keychain inspection tool in debug build.

**Expected access flags**:
- `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` — token accessible only when device is unlocked, NOT migrated to new device via iCloud Keychain backup.
- `kSecAttrAccessControl` with biometric protection on sensitive operations (see 5.2).

**Steps**:
1. Log in with valid credentials.
2. Inspect Keychain entries for FairBridge app bundle ID.
3. Verify `kSecAttrAccessible` = `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`.
4. Verify item does NOT sync to iCloud (no `kSecAttrSynchronizable = true`).

**Expected**: Flags match specification. No iCloud sync. Token absent on fresh device restore from backup.

---

### 5.2 Biometric-Protected Access

| Field | Value |
|---|---|
| **ID** | IOS-KEYCHAIN-002 |
| **Priority** | P1 |
| **Device** | Physical device with Face ID or Touch ID |

**Steps**:
1. Enable biometric authentication in app settings.
2. Force-quit app, reopen.
3. Observe biometric prompt before showing financial data.
4. Authenticate with Face ID / Touch ID.
5. Verify access granted and financial data displayed.
6. Cancel biometric prompt.

**Expected**:
- Biometric prompt appears before first access to payment or expense data.
- Successful authentication grants access.
- Canceling biometric prompt shows password fallback (not raw data).
- Failed biometric (wrong face/finger) locks out after system-defined attempts.
- Keychain entry uses `LAContext` for biometric evaluation.

---

### 5.3 Keychain Persistence After App Reinstall

| Field | Value |
|---|---|
| **ID** | IOS-KEYCHAIN-003 |
| **Priority** | P1 |

**Steps**:
1. Log in. Confirm token in Keychain.
2. Delete app from device.
3. Reinstall app from TestFlight / Xcode.
4. Open app.

**Expected**:
- On iOS 16+: Keychain items may persist after app delete (OS behavior). App must handle stale/expired token gracefully.
- App detects expired token, prompts re-login (not crash or silent failure).
- Fresh login overwrites old Keychain entry correctly.

---

## 6. App Switcher — Screen Content Masking

### 6.1 Financial Data Not Visible in Multitasking View

| Field | Value |
|---|---|
| **ID** | IOS-PRIVACY-001 |
| **Priority** | P0 |
| **All devices and iOS versions** | Required |

**Preconditions**: User is authenticated and viewing a screen with financial data (expense list, payment amount, bank account info).

**Steps**:
1. Navigate to expense list screen showing dollar amounts.
2. Press Home button (or swipe up on Face ID devices) to enter app switcher.
3. Observe the app preview card in the multitasking view.

**Expected**:
- App preview shows a blurred/masked overlay OR a branded splash screen (e.g., FairBridge logo on white background).
- No dollar amounts, names, account numbers, or transaction details visible in app switcher preview.
- App switcher preview is NOT a live view of the financial screen.

**Implementation to verify**: `UIApplication.ignoreSnapshotOnNextApplicationLaunch()` or `UIView.isHidden` overlay applied in `applicationWillResignActive`.

---

### 6.2 Masking Applied on All Financial Screens

| Field | Value |
|---|---|
| **ID** | IOS-PRIVACY-002 |
| **Priority** | P1 |

**Screens to verify**:
- Expense list
- Payment confirmation screen
- Bank account linking screen
- Balance/payment history screen
- Co-parent profile with payment splits

**Steps**: Navigate to each screen, enter app switcher, verify masking.

**Expected**: Masking applied consistently on all screens listed. Non-financial screens (e.g., calendar overview without amounts) may optionally show preview — but default to masked if in doubt.

---

## 7. Offline Behavior

### 7.1 Expense Submission Queued While Offline

| Field | Value |
|---|---|
| **ID** | IOS-OFFLINE-001 |
| **Priority** | P0 |

**Preconditions**: Device has no network connectivity (Airplane Mode ON or Wi-Fi + Cellular disabled).

**Steps**:
1. Enable Airplane Mode.
2. Open app (already authenticated from previous session).
3. Submit a new expense (fill in amount, description, category).
4. Tap Submit.
5. Observe UI feedback.
6. Re-enable network.
7. Observe background sync.

**Expected**:
- Expense is accepted by the app UI with a "Queued" or "Pending sync" status indicator.
- Expense record is created locally with `client_created_at` timestamp (device time, UTC).
- No network error crash or data loss.
- When network restored, expense syncs to backend automatically (no manual retry required).
- Synced expense retains original `client_created_at` timestamp (server must preserve this, not overwrite with server receipt time).
- Backend must use `client_created_at` for expense ordering in the audit log.

---

### 7.2 Payment Blocked While Offline — Clear Error

| Field | Value |
|---|---|
| **ID** | IOS-OFFLINE-002 |
| **Priority** | P0 |

**Preconditions**: Device offline (Airplane Mode). User attempts to initiate ACH payment.

**Steps**:
1. Enable Airplane Mode.
2. Navigate to payment screen.
3. Tap "Send Payment" with valid amount.

**Expected**:
- Payment is NOT queued (ACH requires real-time Stripe API call — cannot be optimistically queued).
- Error message displayed: "Payment requires an internet connection. Please connect and try again."
- Error is dismissible. No retry loop.
- User is NOT charged (verify via Stripe dashboard — no payment intent created).
- App does NOT crash.

---

### 7.3 App Launch While Offline

| Field | Value |
|---|---|
| **ID** | IOS-OFFLINE-003 |
| **Priority** | P1 |

**Steps**: Fully kill app. Enable Airplane Mode. Launch app.

**Expected**:
- App launches successfully (no hang on loading spinner).
- Cached expense data displayed (last-fetched state).
- "Offline" banner or indicator shown.
- Calendar data displayed from local cache.
- Payments tab shows "Connect to internet to view payments" state (no cached payment initiation).

---

## 8. Stripe Financial Connections — Bank Linking OAuth Flow

### 8.1 Bank Linking via SFSafariViewController

| Field | Value |
|---|---|
| **ID** | IOS-STRIPE-001 |
| **Priority** | P0 |
| **Device** | Physical device (OAuth redirect requires real network) |

**Preconditions**: User is in Stripe Connect Express onboarding or bank linking step. Backend has created a `FinancialConnections.Session`.

**Steps**:
1. Tap "Link Bank Account".
2. Observe that Stripe Financial Connections sheet opens.
3. Select a test bank institution (use Stripe test credentials).
4. Complete OAuth authentication in SFSafariViewController (in-app browser — NOT leaving to Safari).
5. Observe redirect back to app.
6. Confirm bank account shown as linked.

**Expected**:
- SFSafariViewController opens (not external Safari — verify by the absence of Safari UI chrome and the presence of in-app done/back buttons).
- OAuth flow completes without redirect failure.
- App receives callback and dismisses SFSafariViewController.
- Bank account name and last 4 digits displayed in linked accounts section.
- No cookies or credentials leaked to Safari browser history (SFSafariViewController does not share cookies with Safari on iOS 11+).

---

### 8.2 Bank Linking — Failure and Retry

| Field | Value |
|---|---|
| **ID** | IOS-STRIPE-002 |
| **Priority** | P1 |

**Steps**: Use Stripe test credentials for a failing bank link (e.g., `test_wrong_credentials`). Attempt link. Observe error.

**Expected**:
- Stripe sheet shows institution-specific error.
- User can retry (sheet remains open for retry or closes and user can re-tap "Link Bank Account").
- No partial state left in backend (no orphaned Financial Connections session).
- App does NOT crash on failure.

---

### 8.3 Bank Linking — User Abandons Mid-Flow

| Field | Value |
|---|---|
| **ID** | IOS-STRIPE-003 |
| **Priority** | P1 |

**Steps**: Begin bank linking OAuth flow. Tap "Cancel" or swipe down to dismiss SFSafariViewController mid-flow.

**Expected**:
- SFSafariViewController dismisses cleanly.
- App returns to the bank linking screen with "No bank linked" state.
- User can retry by tapping "Link Bank Account" again.
- No crash or stuck loading state.

---

## 9. Stripe Connect Express — Onboarding in Web View

### 9.1 Express Account Onboarding

| Field | Value |
|---|---|
| **ID** | IOS-STRIPE-004 |
| **Priority** | P0 |

**Preconditions**: User is a payee (recipient). Backend has created a Stripe Connect Express account and generated an account link URL.

**Steps**:
1. Navigate to "Set Up Payments" / payee onboarding.
2. Observe Stripe Connect Express onboarding opens in web view (SFSafariViewController or WKWebView per implementation).
3. Complete onboarding with Stripe test identity data.
4. Observe redirect back to app.
5. Verify payee account status shown as "Active" or "Pending verification".

**Expected**:
- Web view opens within app (not external Safari).
- Onboarding form loads without blank screen or timeout.
- Stripe identity verification steps complete (or test-mode bypass works).
- App receives completion redirect and updates payee status.
- No data loss if user backgrounds app during onboarding and returns.

---

### 9.2 Express Onboarding — Interrupted and Resumed

| Field | Value |
|---|---|
| **ID** | IOS-STRIPE-005 |
| **Priority** | P1 |

**Steps**: Begin Express onboarding. Background the app (home button or swipe). Return to app after 5 minutes.

**Expected**:
- Web view session preserved (not reset to beginning).
- User can continue onboarding from where they left off.
- If session expired (Stripe account links expire after 24 hours): app detects expiry and generates a new account link automatically, re-presenting the onboarding sheet.

---

## 10. App Store Compliance

### 10.1 No IAP Prompt for Subscription

| Field | Value |
|---|---|
| **ID** | IOS-ASC-001 |
| **Priority** | P0 (App Store rejection risk) |

**Preconditions**: App installed. User has not subscribed. User navigates to subscription/pricing screen.

**Steps**:
1. Open app as unauthenticated user.
2. Navigate to subscription or pricing screen.
3. Observe any payment prompt.

**Expected**:
- App displays a message: "Subscribe at fairbridge.app" (or equivalent) with a web URL.
- App does NOT present an `SKProductsRequest` or StoreKit payment sheet.
- App does NOT show a price within the app that could be confused for an IAP.
- Tapping the web link opens Safari (not SFSafariViewController — App Store guidelines require external browser for subscription purchase to avoid 30% cut).

**Verification**: Run `strings` on the app binary and confirm no `SKPaymentQueue` symbols are referenced in the subscription flow. Review App Store submission notes template (see 10.3).

---

### 10.2 P2P Payment Exemption — No IAP Required

| Field | Value |
|---|---|
| **ID** | IOS-ASC-002 |
| **Priority** | P0 (App Store rejection risk) |

**Context**: Apple App Store guideline 3.1.1 exempts peer-to-peer payment apps from IAP requirements when payments flow between users (not to the developer). FairBridge qualifies as a P2P payment platform.

**Verification steps**:
1. Confirm App Store Review Notes include: "FairBridge facilitates peer-to-peer ACH payments between co-parents. Payments flow directly between users via Stripe Connect. FairBridge does not receive payment funds. This is a P2P payment app exempt from IAP requirements per App Store guideline 3.1.1."
2. Confirm the "Financial Services" category is selected in App Store Connect.
3. Confirm subscription purchase directs to external web URL (not in-app).
4. No digital goods or premium in-app features gated by IAP.

**Expected**: App Review notes document is prepared and accurate. No IAP code paths exist in the build.

---

### 10.3 App Store Review Notes Template

The following must be included in App Store Connect "Notes for App Review":

```
FairBridge is a co-parenting expense and payment coordination app.

Payment flow: ACH payments are peer-to-peer between co-parents via Stripe Connect Express. FairBridge does not hold or receive user funds. This app qualifies for the P2P payment exemption under App Store guideline 3.1.1.

Subscription: FairBridge subscription is purchased at fairbridge.app (web). No in-app purchases exist. The app displays a web URL directing users to the website to subscribe.

Test account credentials: [provide sandbox account email/password]

Permissions required:
- Camera: Required to photograph receipts for expense documentation.
- Calendar (Write-Only, iOS 17+): Required to export custody schedule to Apple Calendar.
- Notifications: Required for payment and expense confirmations; falls back to in-app inbox if denied.
```

---

### 10.4 Privacy Manifest and Required Reason APIs

| Field | Value |
|---|---|
| **ID** | IOS-ASC-003 |
| **Priority** | P0 (iOS 17+ App Store requirement) |

**Steps**: Verify `PrivacyInfo.xcprivacy` file exists in app bundle. Open and review.

**Expected**:
- `NSPrivacyAccessedAPITypes` includes entries for all "Required Reason" APIs used:
  - `NSFileTimestamp` (if file timestamps accessed): reason code documented.
  - `NSUserDefaults` (if used): reason code documented.
- `NSPrivacyCollectedDataTypes` accurately reflects: email, name, financial info, payment info.
- `NSPrivacyTrackingDomains` does NOT include analytics or ad network domains (app should not track).
- `NSPrivacyTracking` = `false`.

---

## 11. Info.plist Permissions Verification

| Permission Key | Required | Description | Test |
|---|---|---|---|
| `NSCameraUsageDescription` | Yes | "FairBridge uses the camera to photograph receipts for expense documentation." | IOS-PHOTO-002 |
| `NSCalendarsWriteOnlyAccessUsageDescription` | Yes (iOS 17+) | "FairBridge exports your custody schedule to Apple Calendar." | IOS-CAL-001 |
| `NSCalendarsUsageDescription` | Yes (iOS 16) | "FairBridge exports your custody schedule to Apple Calendar." | IOS-CAL-001 |
| `NSFaceIDUsageDescription` | Yes | "FairBridge uses Face ID to protect your financial data." | IOS-KEYCHAIN-002 |
| `NSPhotoLibraryUsageDescription` | No — must NOT be present | PHPickerViewController requires no permission | IOS-PHOTO-001 |
| `NSPhotoLibraryAddUsageDescription` | No — must NOT be present | App does not save to library | — |
| `NSLocationWhenInUseUsageDescription` | No — must NOT be present | App does not use location | — |

**Verification**: Run `plutil -p Info.plist` and confirm prohibited keys are absent.

---

## 12. DV Safety — iOS-Specific Verification

These tests are non-negotiable V1 requirements. All must pass before any TestFlight distribution to real users.

### 12.1 No Activity Timestamps Exposed Cross-Parent

| Field | Value |
|---|---|
| **ID** | IOS-DV-001 |
| **Priority** | P0 |

**Steps**:
1. As Parent A, submit an expense at a specific time (e.g., 11:47 PM).
2. Log in as Parent B on a separate device.
3. Inspect all screens where the expense appears: expense list, detail view, notification, in-app inbox.

**Expected**:
- Parent B sees the expense date (e.g., "March 18") but NOT the exact submission time (no "11:47 PM").
- No `created_at` timestamp with time precision exposed in any UI element.
- Network response inspection (via proxy): API must not return time-precision timestamps in any field visible to the other parent.

---

### 12.2 Silent Account Deactivation

| Field | Value |
|---|---|
| **ID** | IOS-DV-002 |
| **Priority** | P0 |

**Context**: A user in a DV situation must be able to deactivate their account without the other parent being notified.

**Steps**:
1. As Parent A, navigate to Settings → Account → Deactivate Account.
2. Complete deactivation flow.
3. Log in as Parent B.

**Expected**:
- Parent B receives NO notification, email, or SMS about Parent A's deactivation.
- Parent B sees a neutral message if they try to interact with Parent A's account (e.g., "This user is unavailable" — no indication of deactivation).
- Parent A's data is not deleted immediately (export window preserved per data deletion policy).

---

### 12.3 Data Export and Deletion

| Field | Value |
|---|---|
| **ID** | IOS-DV-003 |
| **Priority** | P0 |

**Steps**:
1. Navigate to Settings → Privacy → Export My Data.
2. Request data export.
3. Verify export delivered (email with download link or in-app download).
4. Navigate to Settings → Privacy → Delete My Account.
5. Complete deletion flow.

**Expected**:
- Export contains: all expenses submitted, payments sent/received, calendar data, account info.
- Export delivered within 24 hours (or immediately if generated client-side).
- After deletion: login with same credentials fails.
- No residual PII retrievable via API after deletion confirmation.
- Backend soft-deletes financial records (append-only constraint) but scrubs PII fields.

---

### 12.4 Safety Resources Link Accessible

| Field | Value |
|---|---|
| **ID** | IOS-DV-004 |
| **Priority** | P0 |

**Steps**:
1. Navigate to Settings.
2. Locate "Safety Resources" or "Help & Safety" link.
3. Tap link.

**Expected**:
- Link present and tappable without authentication required (accessible even on lock screen if applicable).
- Opens DV hotline resource (e.g., National DV Hotline: 1-800-799-7233) in external Safari.
- Link does NOT open in SFSafariViewController (must be external browser — user may need to share URL safely).
- No co-parent activity triggered by tapping this link.

---

### 12.5 Push Notification Lock Screen Privacy (DV)

Cross-reference with IOS-NOTIF-008. Verify on physical locked device that no financial amount, co-parent name, or transaction detail is visible in lock screen notification banners without device unlock.

---

## 13. Regression and Smoke Test Checklist

Run this checklist on every TestFlight build before distribution:

- [ ] App launches without crash on iPhone SE 3 / iOS 16 (oldest supported)
- [ ] App launches without crash on iPhone 15 / iOS 18 (latest)
- [ ] Login and authentication flow completes
- [ ] Push notification delivered in normal mode (physical device)
- [ ] Push notification lock screen shows NO amounts or names (DV safety)
- [ ] In-app inbox receives notification when push permission denied
- [ ] Receipt photo selection via PHPicker (no permission prompt)
- [ ] Camera capture works with blur warning on blurry photo
- [ ] Calendar export creates events in Apple Calendar
- [ ] Keychain token survives app background and foreground
- [ ] App switcher shows masked screen (no financial data visible)
- [ ] Offline: expense submission queued, payment blocked with error
- [ ] Stripe bank linking OAuth completes in SFSafariViewController
- [ ] Stripe Connect Express onboarding loads and completes
- [ ] No IAP prompt visible anywhere in app
- [ ] Privacy manifest present in app bundle
- [ ] DV: silent deactivation sends no notification to other parent
- [ ] DV: safety resources link present in Settings

---

## 13. Known Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| APNs time-sensitive notifications rejected by Apple entitlement review | Medium | Submit `com.apple.developer.usernotifications.time-sensitive` entitlement justification in App Store Review Notes. Test with and without entitlement in staging. |
| PHPicker availability on iOS 14 (minimum) | Low | PHPicker available since iOS 14.0. No fallback needed for iOS 16+ minimum. |
| Calendar write-only access (iOS 17+) silently falls back to full access on iOS 16 | Low | Code must branch on iOS version and use appropriate `EKAuthorizationStatus` check. |
| Stripe Financial Connections redirects to external Safari instead of SFSafariViewController | Medium | Verify Stripe SDK version supports `SFSafariViewController` presentation. Test with latest Stripe iOS SDK on all devices. |
| App Store rejection for subscription pricing shown in-app | High | Do not display any price in-app. Use "Subscribe at fairbridge.app" text only. |
| Screen masking not applied on all financial screens | Medium | Automated UI test: enumerate all tab/screen routes, enter app switcher after each, verify masked state. |
| DV safety: sensitive data leaks into push payload on lock screen | High | Backend must strip amounts/names from APNs `alert.body`. QA must verify on physical locked device for every notification type before beta. |
| DV safety: silent deactivation accidentally notifies other parent | Medium | Backend-tester to verify no webhook/email fires on deactivation. iOS-tester verifies no local push triggered on deactivation event received. |
| SMS body exposes financial details violating DV safety | Medium | Twilio message templates reviewed by security-eng before launch. Generic body required for all SMS. |

---

*End of iOS Test Plan v1.1 — updated 2026-03-18 with DV safety, SMS escalation, and notification cascade tests*
