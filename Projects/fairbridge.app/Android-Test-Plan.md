# FairBridge Android Test Plan

**Author**: android-tester
**Date**: 2026-03-17
**Version**: 1.1
**Status**: Updated with MVP context (2026-03-18) — sent to program-manager

---

## Executive Summary

This document specifies the complete Android quality assurance strategy for FairBridge, a co-parenting ACH payment and expense tracking application. Android presents unique testing challenges compared to iOS: OEM firmware fragmentation means a notification that works on a stock Pixel may silently die on a Xiaomi or Samsung device without battery optimization exemption. Financial data security requires hardware-backed keystore validation. The test plan covers eleven testing domains across a device matrix of four OEM families and four API levels, from Android 7.0 (API 24, still ~5% of global market) through Android 14 (API 34). Every test case is tied to a specific acceptance criterion — a test without a pass/fail gate is not a test.

---

## 1. Device Matrix

All functional test cases must pass on the full device matrix. Performance and battery tests may be scoped to the subset noted per section.

### 1.1 Primary Device Matrix

| Device | OEM Skin | API Level | RAM | Camera |
|--------|----------|-----------|-----|--------|
| Pixel 6 | Stock Android 12 | API 31 | 8 GB | 50 MP |
| Pixel 7 | Stock Android 13 | API 33 | 8 GB | 50 MP |
| Pixel 8 | Stock Android 14 | API 34 | 8 GB | 50 MP |
| Samsung Galaxy S22 | One UI 4.1 | API 31 | 8 GB | 50 MP |
| Samsung Galaxy S23 | One UI 5.1 | API 33 | 8 GB | 50 MP |
| Samsung Galaxy S24 | One UI 6.1 | API 34 | 12 GB | 200 MP |
| Xiaomi 13 | MIUI 14 | API 33 | 8 GB | 54 MP |
| Xiaomi 14 | HyperOS 1.0 | API 34 | 12 GB | 50 MP |
| OnePlus 11 | OxygenOS 13 | API 33 | 16 GB | 50 MP |
| OnePlus 12 | OxygenOS 14 | API 34 | 12 GB | 50 MP |

### 1.2 API Level Coverage Rationale

| API Level | Android Version | Significance |
|-----------|----------------|-------------|
| API 24 | Android 7.0 | Minimum supported; Doze mode introduced |
| API 28 | Android 9.0 | Background activity launch restrictions |
| API 31 | Android 12 | Notification permission not yet required; exact alarm restrictions |
| API 34 | Android 14 | POST_NOTIFICATIONS permission required; health connect |

### 1.3 Low-End Device (Camera Quality Testing Only)

| Device | Camera | API | Purpose |
|--------|--------|-----|---------|
| Motorola Moto G Power (2022) | 50 MP (low-quality sensor, f/1.8) | API 31 | Low-end camera simulation |
| Samsung Galaxy A14 | 50 MP (binned to 12 MP effective) | API 33 | Mid-range baseline |

---

## 2. FCM Notification Delivery

### 2.1 Background and Risk

FCM delivers high-priority messages that should wake the device and display notifications even when the app is backgrounded. OEM skins — particularly Samsung One UI, Xiaomi MIUI/HyperOS, and Oppo ColorOS — implement aggressive background process killing that can silently block FCM delivery regardless of priority setting. This is the highest-risk area for Android fragmentation failures.

### 2.2 Test Setup

Each notification test requires:
1. App in background (not recently foregrounded within 60 seconds)
2. Screen off, device idle for 5 minutes before test
3. Test FCM message sent via backend test endpoint with `priority: high` and correct `collapse_key`
4. Observation window: 60 seconds maximum

### 2.3 FCM Delivery Test Cases

**TC-FCM-001: Stock Android baseline delivery**
- Device: Pixel 6, 7, 8
- Preconditions: Battery optimization NOT exempted (default state), app background
- Action: Trigger payment_received FCM (high-priority channel)
- Expected: Notification appears within 15 seconds
- Pass criteria: 3/3 Pixel devices deliver within 15 seconds on first attempt
- Note: Stock Android without exemption should still deliver FCM high-priority reliably

**TC-FCM-002: Samsung One UI delivery without exemption**
- Device: Samsung S22, S23, S24
- Preconditions: Battery optimization NOT exempted, "Sleeping apps" not configured, app background 5 min
- Action: Trigger payment_received FCM
- Expected: Notification appears (may be delayed up to 60 seconds due to One UI power management)
- Pass criteria: Notification appears within 60 seconds on 2/3 Samsung devices
- Failure mode to document: If notification does not appear, record One UI version and power mode setting

**TC-FCM-003: Samsung One UI delivery WITH exemption**
- Device: Samsung S22, S23, S24
- Preconditions: Battery optimization exempted via REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, "Unrestricted" in One UI battery settings
- Action: Trigger payment_received FCM
- Expected: Notification appears within 15 seconds
- Pass criteria: 3/3 Samsung devices deliver within 15 seconds

**TC-FCM-004: Xiaomi MIUI/HyperOS delivery without exemption**
- Device: Xiaomi 13 (MIUI 14), Xiaomi 14 (HyperOS 1.0)
- Preconditions: Autostart NOT enabled, battery saver OFF, app in background 5 min
- Action: Trigger payment_received FCM
- Expected: Notification may not arrive (MIUI aggressively kills background processes)
- Pass criteria: DOCUMENT actual behavior — if notification never arrives without exemption, this is expected and confirms exemption prompt is mandatory for Xiaomi
- Note: Xiaomi MIUI requires BOTH battery optimization exemption AND Autostart permission for reliable FCM

**TC-FCM-005a: Xiaomi 13 (MIUI 14) delivery WITH full exemption**
- Device: Xiaomi 13 (MIUI 14)
- Preconditions: Battery optimization exempted AND Autostart enabled via MIUI Security app
- Action: Trigger payment_received FCM
- Expected: Notification appears within 30 seconds
- Pass criteria: Device delivers within 30 seconds
- Deep-link verification: `Intent("miui.intent.action.APP_PERM_EDITOR")` with extras `pkg_name = "app.fairbridge"` and `pkg_uid = <app UID>` opens MIUI Security app Autostart screen correctly

**TC-FCM-005b: Xiaomi 14 (HyperOS 1.0) delivery WITH full exemption**
- Device: Xiaomi 14 (HyperOS 1.0)
- Preconditions: Battery optimization exempted via standard `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` (Autostart moved to native Settings in HyperOS — no separate Security app step required)
- Action: Trigger payment_received FCM
- Expected: Notification appears within 30 seconds
- Pass criteria: Device delivers within 30 seconds
- Deep-link verification: Standard `android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` with package URI opens Settings > Apps > FairBridge > Battery > No restrictions correctly
- Note: HyperOS 1.0 does NOT use `miui.intent.action.APP_PERM_EDITOR` — using it will fail silently or open wrong screen

**TC-FCM-006: OnePlus OxygenOS delivery**
- Device: OnePlus 11, 12
- Preconditions: Battery optimization NOT exempted
- Action: Trigger payment_received FCM
- Expected: Notification appears within 30 seconds (OxygenOS is less aggressive than MIUI)
- Pass criteria: Both devices deliver within 30 seconds without exemption

**TC-FCM-007: FCM delivery during active call**
- Device: Pixel 8, Samsung S24
- Preconditions: Device in active phone call, app backgrounded
- Action: Trigger payment_received FCM
- Expected: Notification appears in notification shade (not full-screen interrupt)
- Pass criteria: Notification visible in shade, does not interrupt call UI

**TC-FCM-008: FCM delivery with notification permission denied (API 33+)**
- Device: Pixel 8, Samsung S24 (API 33+)
- Preconditions: POST_NOTIFICATIONS permission denied by user
- Action: Trigger payment_received FCM
- Expected: No system notification shown; in-app inbox updated on next foreground
- Pass criteria: (1) No system notification appears, (2) In-app inbox shows the event when app is opened

**TC-FCM-009: FCM delivery on API 24 (Doze mode)**
- Device: Emulator API 24 (no physical device in matrix)
- Preconditions: Device in Doze mode (simulate via `adb shell dumpsys deviceidle force-idle`)
- Action: Trigger payment_received FCM high-priority
- Expected: High-priority FCM should bypass Doze mode (FCM whitelist)
- Pass criteria: Notification arrives within 60 seconds even in forced Doze

---

## 3. Battery Optimization Exemption

### 3.1 Overview

Android's battery optimization (Doze + App Standby) can prevent background FCM delivery. FairBridge must prompt the user to grant battery optimization exemption via `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` intent. This section tests the prompt lifecycle and behavioral outcomes.

### 3.2 Exemption Prompt Test Cases

**TC-BATT-001: Exemption prompt appears at correct onboarding step**
- Trigger (API 33+): Fires immediately after notification permission dialog closes, regardless of grant/deny — sequence is: email verification → notification permission → **battery exemption prompt** → co-parent pairing
- Trigger (API 24–32): Fires after email verification, before co-parent pairing (no notification permission dialog exists on these API levels)
- Expected: System dialog appears: "Allow [FairBridge] to always run in the background?"
- Pass criteria: Dialog appears on all 10 devices in matrix at the correct sequence step; does NOT fire before email verification completes
- Note: Do NOT prompt before user understands why — must follow UX flow sequence

**TC-BATT-002: Exemption prompt — user grants**
- Action: User taps "Allow" on battery optimization dialog
- Expected: `PowerManager.isIgnoringBatteryOptimizations()` returns `true`
- Pass criteria: API call returns `true` immediately after grant; no app restart required

**TC-BATT-003: Exemption prompt — user denies**
- Action: User taps "Don't allow"
- Expected: App shows in-app explanation card: "Notifications may be delayed on your device. [Open settings] to fix."
- Pass criteria: (1) App does not crash, (2) explanation card visible on home screen, (3) "Open settings" deep-links to system battery settings for FairBridge

**TC-BATT-004: Exemption prompt — user dismisses (back button)**
- Action: User presses back button on system dialog
- Expected: Same as TC-BATT-003 — show explanation card
- Pass criteria: Explanation card appears; settings deep-link functional

**TC-BATT-005: Re-prompt after denial (next session)**
- Preconditions: User previously denied exemption
- Action: User opens app next day
- Expected: No re-prompt on every launch (would be annoying); re-prompt shown at most once per 7 days
- Pass criteria: Second prompt does NOT appear within 6 days of denial

**TC-BATT-006: Degraded-but-functional behavior WITHOUT exemption (Pixel)**
- Device: Pixel 6 (stock Android, no exemption)
- Preconditions: Battery optimization NOT exempted, Doze mode active
- Action: Backend sends payment_received notification; user does NOT open app for 30 minutes
- Expected: Notification arrives within 30 minutes (FCM high-priority may still wake device on stock Android)
- Pass criteria: Notification visible within 30 minutes; when user opens app, payment status is correct
- Failure note: If notification delayed beyond 30 min without exemption on Pixel, this is a regression

**TC-BATT-007: Degraded behavior WITHOUT exemption (Samsung S22)**
- Device: Samsung S22
- Preconditions: Battery optimization NOT exempted, "Sleeping apps" potentially applied by One UI
- Action: Backend sends payment_received; user does not open app for 60 minutes
- Expected: Notification may be delayed significantly; in-app inbox must be correct when app next opens
- Pass criteria: (1) In-app inbox shows payment event when app reopens, (2) App does not show stale data

**TC-BATT-008: Samsung One UI "Sleeping apps" interaction**
- Device: Samsung S22, S23
- Preconditions: FairBridge manually added to "Sleeping apps" list in One UI battery settings
- Action: Trigger payment_received FCM
- Expected: Notification does not arrive (sleeping app blocks FCM)
- Pass criteria: Test CONFIRMS that "Sleeping apps" = total FCM block; document for user-facing help content

---

## 4. Notification Channels

### 4.1 Channel Configuration Requirements

FairBridge must register three notification channels on first launch:

| Channel ID | Name | Importance | Sound | Vibration |
|------------|------|------------|-------|-----------|
| `fairbridge_payments` | Payments | IMPORTANCE_HIGH | Default ringtone | Yes |
| `fairbridge_expenses` | Expenses | IMPORTANCE_DEFAULT | Default | Yes |
| `fairbridge_calendar` | Calendar | IMPORTANCE_LOW | None | No |

### 4.2 Channel Test Cases

**TC-CHAN-001: Channels registered on first launch**
- Action: Fresh install, launch app
- Expected: Three channels visible in System Settings > Apps > FairBridge > Notifications
- Pass criteria: All three channels appear with correct names and importance levels immediately after first launch (before any FCM received)
- Verification: `adb shell dumpsys notification --noredact | grep fairbridge`

**TC-CHAN-002: Payment channel importance = HIGH**
- Verification method: `adb shell dumpsys notification --noredact | grep -A5 "fairbridge_payments"`
- Pass criteria: Output shows `importance=4` (IMPORTANCE_HIGH)

**TC-CHAN-003: Expense channel importance = DEFAULT**
- Verification: `adb shell dumpsys notification --noredact | grep -A5 "fairbridge_expenses"`
- Pass criteria: Output shows `importance=3` (IMPORTANCE_DEFAULT)

**TC-CHAN-004: Calendar channel importance = LOW**
- Verification: `adb shell dumpsys notification --noredact | grep -A5 "fairbridge_calendar"`
- Pass criteria: Output shows `importance=2` (IMPORTANCE_LOW)

**TC-CHAN-005: Channel importance survives app update**
- Preconditions: User has manually lowered payment channel to DEFAULT in system settings
- Action: App update installed (simulate via sideload of new APK)
- Expected: User's customized importance (DEFAULT) is preserved — app must NOT reset channel importance on update
- Pass criteria: Channel importance remains at user-set level after update
- Implementation note: `createNotificationChannel()` is idempotent for existing channels — importance only set on first creation

**TC-CHAN-006: Channel importance survives app reinstall**
- Preconditions: User has customized channel importance
- Action: Uninstall and reinstall app
- Expected: Channels reset to app defaults (IMPORTANT: user customizations are lost on reinstall — this is Android system behavior, not a bug)
- Pass criteria: After reinstall, channels revert to defaults; no crash

**TC-CHAN-007: Collapse key batching — 20 rapid expense notifications**
- Preconditions: App backgrounded; payment channel active
- Action: Backend sends 20 expense notifications in 10 seconds, all with `collapse_key: "expense_updates"`
- Expected: User sees 1 notification in shade (collapsed), not 20 separate notifications
- Pass criteria: Maximum 2 notifications visible in shade (may show latest + "2 more" grouping)
- Device coverage: Test on Pixel 8, Samsung S24, Xiaomi 14
- Verification: Count notification items in shade via UI Automator

**TC-CHAN-008: Collapse key — different collapse keys do NOT merge**
- Action: Send 5 expense notifications + 5 payment notifications simultaneously
- Expected: Two notification groups visible (expenses collapsed, payments collapsed); total ≤ 4 visible items
- Pass criteria: Expense and payment notifications remain in separate groups

---

## 5. FLAG_SECURE — Screen Security

### 5.1 Requirements

All financial screens must set `FLAG_SECURE` on the Android Window to prevent screenshots and recent apps thumbnails from showing financial data.

Financial screens include: payment initiation, payment history, expense detail view, bank account screen, and any screen displaying account balances or transaction amounts.

### 5.2 FLAG_SECURE Test Cases

**TC-SECURE-001: Screenshot blocked on payment screen**
- Action: Navigate to payment initiation screen; attempt screenshot via hardware buttons (Volume Down + Power)
- Expected: Toast message "Screenshot blocked" or similar; screenshot file NOT created in gallery
- Pass criteria: No screenshot file created; no financial data captured
- Device coverage: All 10 devices in matrix

**TC-SECURE-002: Screenshot blocked on expense detail screen**
- Action: Navigate to expense detail (showing amount, description, receipt photo); attempt screenshot
- Expected: Screenshot blocked
- Pass criteria: Same as TC-SECURE-001

**TC-SECURE-003: Recent apps thumbnail — no financial data visible**
- Action: While on payment screen, press Recent Apps button
- Expected: App thumbnail shows blank/app icon only, NOT the financial screen content
- Pass criteria: No dollar amounts, account numbers, or names visible in recent apps thumbnail
- Device coverage: All 10 devices (thumbnail rendering varies by OEM)

**TC-SECURE-004: Recent apps thumbnail on non-financial screen**
- Action: While on home dashboard (showing only notification count, not amounts), press Recent Apps
- Expected: Dashboard thumbnail IS visible (FLAG_SECURE not set on non-financial screens)
- Pass criteria: Dashboard preview renders normally in recent apps

**TC-SECURE-005: Screen recording blocked**
- Action: Start screen recording via Quick Settings tile; navigate to payment screen
- Expected: Payment screen appears black in recording
- Pass criteria: Recorded video shows black frame when on financial screen; non-financial screens visible normally
- Device coverage: Pixel 8, Samsung S24 (screen recording built-in)

**TC-SECURE-006: Samsung DeX / split-screen**
- Device: Samsung S22+
- Action: Enter split-screen mode with FairBridge payment screen on one side
- Expected: FLAG_SECURE prevents screen capture of FairBridge pane
- Pass criteria: Screenshot of split-screen shows FairBridge pane as black

---

## 6. Android Keystore — Token Storage

### 6.1 Requirements

Auth tokens must be stored using `react-native-keychain` backed by the Android Keystore system. For devices with hardware security module (API 28+), tokens must reside in hardware-backed storage. Biometric authentication must be required before token access on devices with enrolled biometrics.

### 6.2 Keystore Test Cases

**TC-KEY-001: Token stored in Android Keystore (not SharedPreferences)**
- Action: Log in; inspect storage
- Verification: `adb shell run-as com.fairbridge.app ls /data/data/com.fairbridge.app/shared_prefs/` — auth token must NOT appear in SharedPreferences XML files
- Pass criteria: No plaintext token in SharedPreferences; token retrievable only via Keystore API

**TC-KEY-002: Hardware-backed storage on API 28+ device**
- Device: Pixel 7 (API 33), Samsung S23 (API 33)
- Action: Log in; query key properties
- Verification: Use `react-native-keychain`'s `getSecurityLevel()` — must return `SECURE_HARDWARE` or `BIOMETRICS`
- Pass criteria: Security level is NOT `ANY` or `SOFTWARE` on supported devices

**TC-KEY-003: Biometric authentication required for token access**
- Preconditions: Fingerprint enrolled on device; app configured with biometric protection
- Action: Background app for 5 minutes; return to app
- Expected: Biometric prompt appears before app shows any financial data
- Pass criteria: Biometric prompt appears; canceling prompt does not reveal financial data; confirms via fingerprint shows data

**TC-KEY-004: Token inaccessible after failed biometric**
- Action: At biometric prompt, fail authentication 3 times (exceeds lockout threshold)
- Expected: App shows "Authentication failed — please try again later" or falls back to PIN/password
- Pass criteria: No financial data shown; app gracefully handles biometric lockout

**TC-KEY-005: Token cleared on app uninstall**
- Action: Log in; uninstall app; reinstall; attempt to access protected data
- Expected: Token is gone; user must log in again
- Pass criteria: After reinstall, user sees login screen (not automatically authenticated)

**TC-KEY-006: Keystore behavior on rooted device**
- Device: Rooted Pixel 6 (test environment only)
- Action: Attempt to extract token using Frida or root file access
- Expected: Hardware-backed Keystore keys are non-exportable; extraction fails
- Pass criteria: Frida-based extraction returns error; token not recoverable as plaintext
- Note: This is a security validation test, not a regression test

---

## 7. Receipt Photo Capture

### 7.1 Requirements

Receipt photos must be AI-processable: minimum 720p effective resolution, blur score below threshold, usable JPEG quality. FairBridge uses CameraX via `react-native-vision-camera`. Photos are uploaded to Cloudflare R2.

### 7.2 Device Tier Definitions

| Tier | Device Examples | Camera Spec | Expected Quality |
|------|----------------|-------------|-----------------|
| Low-end | Motorola Moto G Power 2022 | 2MP front / 50MP (low sensor quality) main | Must produce AI-usable image in good light |
| Mid-range | Samsung Galaxy A14 | 50MP (12MP effective) | Good quality in most conditions |
| Flagship | Pixel 8, Samsung S24 | 50MP+ computational | Excellent quality |

### 7.3 Receipt Photo Test Cases

**TC-PHOTO-001: Camera permission flow**
- Action: First time tapping "Add receipt photo"
- Expected: Android permission dialog for CAMERA appears (not requested pre-emptively)
- Pass criteria: Dialog appears; granting permission opens camera immediately; denying shows "Camera required for receipt photos" with settings link

**TC-PHOTO-002: Low-end device — good lighting**
- Device: Motorola Moto G Power 2022
- Action: Photograph a standard receipt (restaurant, 8.5" paper) under indoor fluorescent lighting at 30cm distance
- Expected: Photo uploaded; AI returns line items with >80% accuracy
- Pass criteria: AI extraction succeeds (returns at least vendor name + total amount); image not rejected for quality

**TC-PHOTO-003: Low-end device — poor lighting**
- Device: Motorola Moto G Power 2022
- Action: Photograph same receipt in dim lighting (equivalent to restaurant candlelight)
- Expected: App detects blur or low quality; shows warning "Photo may be hard to read — try better lighting"
- Pass criteria: Warning shown if blur score exceeds threshold; user can still submit photo (warning is advisory, not blocking)

**TC-PHOTO-004: Mid-range device — standard conditions**
- Device: Samsung Galaxy A14
- Action: Photograph receipt under standard indoor lighting
- Expected: Photo AI extraction succeeds; no quality warning
- Pass criteria: AI returns vendor + total; JPEG size between 200KB and 2MB (compressed for upload)

**TC-PHOTO-005: Flagship device — high resolution handling**
- Device: Samsung S24 (200MP sensor, binned to 12MP by default)
- Action: Photograph receipt; verify upload size
- Expected: App compresses to max 2MP for upload (not uploading raw 12MP JPEG)
- Pass criteria: Uploaded file ≤ 2MB; AI extraction succeeds

**TC-PHOTO-006: Photo from gallery (existing receipt)**
- Action: Tap "Add receipt photo" → select "Choose from gallery" → pick existing photo
- Expected: Photo selected and uploaded; same AI processing applied
- Pass criteria: Gallery picker opens (using `react-native-image-picker` with `launchImageLibrary`); selected image processed correctly

**TC-PHOTO-007: Camera capture — portrait and landscape orientation**
- Action: Capture receipt photo in portrait orientation; then landscape
- Expected: Both orientations produce correctly oriented image in review screen
- Pass criteria: No 90-degree rotation bug; EXIF orientation handled correctly

**TC-PHOTO-008: Upload failure — network unavailable**
- Action: Capture receipt photo; disable Wi-Fi and mobile data; attempt to submit expense
- Expected: Expense queued locally with photo reference; photo uploaded when connectivity restored
- Pass criteria: Expense appears in local queue with "(receipt pending upload)" indicator; auto-uploads when online

---

## 8. Calendar Export

### 8.1 Requirements

FairBridge exports custody schedule events to the device calendar via Android's `CalendarContract` API. Events must appear in Google Calendar and other CalendarContract-compatible apps (Samsung Calendar, etc.).

### 8.2 Calendar Export Test Cases

**TC-CAL-001: Calendar permission request**
- Action: First time tapping "Export to Calendar"
- Expected: System permission dialog for `WRITE_CALENDAR` (and `READ_CALENDAR` if needed)
- Pass criteria: Permission dialog appears with FairBridge name visible; granting continues export; denying shows explanation

**TC-CAL-002: Event appears in Google Calendar**
- Device: Pixel 8 (Google Calendar default)
- Action: Export 30-day custody schedule
- Expected: Events appear in Google Calendar with correct titles, dates, times, and FairBridge calendar color
- Pass criteria: All exported events visible in Google Calendar within 30 seconds; no duplicate events

**TC-CAL-003: Event appears in Samsung Calendar**
- Device: Samsung S23 (Samsung Calendar default)
- Action: Export 30-day custody schedule
- Expected: Events appear in Samsung Calendar
- Pass criteria: Events visible; Samsung Calendar syncs correctly with CalendarContract

**TC-CAL-004: Duplicate prevention on re-export**
- Action: Export custody schedule; wait; export same schedule again
- Expected: No duplicate events created
- Pass criteria: Calendar has exactly N events (not 2N) after second export
- Implementation note: FairBridge must write a `SYNC_DATA1` or `UID_2445` field to track exported event IDs and delete/update rather than insert new

**TC-CAL-005: Calendar selection — multiple calendars**
- Preconditions: Device has multiple Google accounts (work + personal)
- Action: Export custody schedule
- Expected: Calendar picker shown letting user choose which calendar account to write to
- Pass criteria: Picker appears; selected calendar receives events; other calendars unaffected

**TC-CAL-006: Export large date range (365 days)**
- Action: Export full-year custody schedule (365 events)
- Expected: All events written; no timeout or partial write
- Pass criteria: All 365 events appear in calendar within 60 seconds; no ANR dialog

**TC-CAL-007: CalendarContract not available (edge case)**
- Preconditions: Device has no calendar accounts configured
- Action: Attempt calendar export
- Expected: App shows "No calendar found. Please add a Google account or calendar app."
- Pass criteria: Graceful error; no crash

---

## 9. Offline Behavior

### 9.1 Requirements

FairBridge must handle network loss gracefully: expense submission queued locally with `client_created_at` timestamp, payment initiation blocked with clear error, data sync on reconnection.

### 9.2 Offline Test Cases

**TC-OFF-001: Expense submission queued when offline**
- Action: Disable all network connectivity; submit expense (amount, description, category)
- Expected: Expense saved locally with `client_created_at` timestamp; UI shows "Queued — will sync when online"
- Pass criteria: (1) Expense visible in local queue immediately, (2) `client_created_at` timestamp correct, (3) No error dialog or crash

**TC-OFF-002: Queued expense syncs on reconnection**
- Preconditions: One expense in local queue (from TC-OFF-001)
- Action: Re-enable network connectivity
- Expected: Queue auto-syncs within 30 seconds; expense appears on server with original `client_created_at`
- Pass criteria: (1) Expense appears in backend within 30 seconds, (2) Timestamp preserved (not overwritten by server time)

**TC-OFF-003: Multiple expenses queued offline**
- Action: Disable network; submit 5 expenses
- Expected: All 5 queued; queue count visible (e.g., "5 items pending sync")
- Pass criteria: All 5 sync in correct submission order on reconnection; no duplicates

**TC-OFF-004: Payment initiation blocked when offline**
- Action: Disable network; attempt to initiate ACH payment
- Expected: Clear error message: "Payment requires an internet connection. Please reconnect and try again."
- Pass criteria: Payment NOT submitted to backend; error message shown; user not confused about whether payment was sent

**TC-OFF-005: Offline → reconnect → WorkManager sync**
- Preconditions: WorkManager registered for connectivity-change sync job
- Action: Background app; disable network; re-enable network
- Expected: WorkManager fires sync job within 60 seconds of reconnection (even with app backgrounded)
- Pass criteria: Pending expenses sync automatically without user reopening the app

**TC-OFF-006: Offline indicator in UI**
- Action: Disable network while app is in foreground
- Expected: Offline banner appears ("You're offline — some features unavailable")
- Pass criteria: Banner appears within 5 seconds of network loss; disappears when connectivity restored

**TC-OFF-007: Stale data display when offline**
- Action: Load expense list while online; go offline; refresh expense list
- Expected: Cached data displayed with "Last updated [time]" indicator; no spinner that never resolves
- Pass criteria: Cached data visible; no infinite loading state; timestamp shown

---

## 10. Stripe Financial Connections (Bank Linking)

### 10.1 Requirements

Stripe Financial Connections opens a Chrome Custom Tab (CCT) for bank OAuth. Unlike iOS (SFSafariViewController), Android requires Chrome to be installed or a compatible CCT provider.

### 10.2 Bank Linking Test Cases

**TC-STRIPE-001: Chrome Custom Tab opens correctly**
- Device: Pixel 8 (Chrome default browser)
- Action: Tap "Link Bank Account"
- Expected: Chrome Custom Tab opens with Stripe Financial Connections URL; FairBridge toolbar color preserved
- Pass criteria: CCT opens within 3 seconds; Stripe UI rendered correctly; no fallback to external browser

**TC-STRIPE-002: Chrome not installed — fallback**
- Device: Emulator with Chrome removed (or use a device with Chrome disabled)
- Action: Tap "Link Bank Account"
- Expected: Graceful fallback — either use another CCT-compatible browser or show error "Please install Chrome to link your bank"
- Pass criteria: No crash; user informed of requirement

**TC-STRIPE-003: Successful bank link — result returned to app**
- Action: Complete Stripe Financial Connections OAuth flow (use Stripe test credentials)
- Expected: CCT closes; FairBridge receives success callback; bank account shown as linked
- Pass criteria: Bank account name displayed; "Account linked" confirmation shown within 5 seconds of CCT close

**TC-STRIPE-004: Bank link cancelled by user (back button)**
- Action: Open Stripe CCT; press Android back button
- Expected: CCT closes; FairBridge shows "Bank linking cancelled" message; user can retry
- Pass criteria: No crash; app state preserved; retry button functional

**TC-STRIPE-005: Bank link on Samsung with Samsung Internet browser**
- Device: Samsung S22 (Samsung Internet as CCT provider)
- Action: Tap "Link Bank Account"
- Expected: Samsung Internet CCT opens if Chrome not available/preferred; Stripe UI functions correctly
- Pass criteria: CCT opens; bank link flow completes; success callback received

**TC-STRIPE-006: Stripe Connect Express onboarding**
- Action: Payer taps "Set up payouts" → Stripe Connect Express onboarding
- Expected: CCT opens Stripe Connect Express onboarding; user completes identity verification; CCT closes with success
- Pass criteria: Connect Express onboarding completes; payer marked as onboarded in FairBridge; payment initiation enabled

---

## 11. Google Play Compliance

### 11.1 Financial Services Declaration

FairBridge must comply with Google Play's Financial Services policy. The app facilitates peer-to-peer ACH payments between co-parents and must declare this usage during app submission.

### 11.2 Compliance Test Cases

**TC-PLAY-001: Financial Services policy declaration**
- Verification: Review Google Play Console submission — Financial Services target audience declaration complete
- Required declarations: P2P payment facilitation, Stripe as payment processor, no lending/insurance/investment features
- Pass criteria: App approved by Google Play without Financial Services policy violation

**TC-PLAY-002: Play Protect warning — first install**
- Device: Pixel 8 (factory reset, Play Protect enabled)
- Action: Install FairBridge from Play Store
- Expected: No Play Protect warning (app must be signed by release keystore, not debug)
- Pass criteria: App installs without "App may be harmful" warning
- Failure mode: If Play Protect warning appears, document exact warning text and escalate to security review

**TC-PLAY-003: Play Protect warning — sideload APK (expected)**
- Action: Sideload debug APK (not from Play Store)
- Expected: Play Protect warning appears (expected behavior for sideloaded APK)
- Pass criteria: Warning appears; this is NOT a bug; document expected behavior for QA reference

**TC-PLAY-004: Target SDK version compliance**
- Verification: APK manifest declares `targetSdkVersion` = 34 (required for new Google Play submissions as of 2024)
- Pass criteria: `adb shell dumpsys package com.fairbridge.app | grep targetSdk` returns 34

**TC-PLAY-005: Permissions audit — no excess permissions**
- Verification: Review APK manifest permissions list
- Allowed permissions: INTERNET, POST_NOTIFICATIONS, CAMERA, READ_CALENDAR, WRITE_CALENDAR, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, USE_BIOMETRIC, USE_FINGERPRINT, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE
- Pass criteria: No undeclared sensitive permissions; no READ_CONTACTS, READ_CALL_LOG, ACCESS_FINE_LOCATION (these trigger additional Play Store review)

**TC-PLAY-006: Data Safety form accuracy**
- Verification: Google Play Data Safety form must accurately declare:
  - Financial info collected (payment method, bank account): YES, shared with Stripe
  - Personal info (name, email): YES, used for account management
  - No precise location data collected
  - No contacts data collected
- Pass criteria: Data Safety form approved; no post-submission correction required

---

## 12. Regression and Smoke Test Suite

### 12.1 Smoke Tests (Run on Every Build)

The following tests must pass before any build is promoted to QA:

| ID | Test | Device | Duration |
|----|------|--------|----------|
| TC-SMOKE-001 | App launches without crash | Pixel 8, Samsung S24 | <30s |
| TC-SMOKE-002 | Login succeeds | Pixel 8 | <60s |
| TC-SMOKE-003 | Expense submission (online) | Pixel 8 | <60s |
| TC-SMOKE-004 | Notification received (FCM) | Pixel 8 | <90s |
| TC-SMOKE-005 | FLAG_SECURE on payment screen | Pixel 8 | <30s |

### 12.2 Full Regression Suite

Full regression runs before each release candidate on all 10 devices in matrix. Estimated duration: 8 hours on physical device farm.

---

## 13. Known Limitations and Mitigations

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Xiaomi MIUI requires Autostart permission (not requestable via API) | FCM may never arrive on MIUI without user action | In-app guide: show Xiaomi-specific instructions with screenshot walkthrough; in-app notification health check screen |
| FLAG_SECURE prevents accessibility tools (e.g., screen readers for visually impaired users) | FLAG_SECURE + TalkBack conflicts on some OEM skins | Test TalkBack compatibility; document workaround if financial screen content inaccessible to screen readers |
| CalendarContract does not support recurring event rules (RRULE) on all OEM calendars | Samsung Calendar may show individual events instead of recurring series | Export as individual events for MVP; RRULE support as V2 enhancement |
| Chrome Custom Tabs require Chrome or compatible browser | Users without Chrome cannot link bank on Android | Show pre-prompt: "This step opens in Chrome. Please ensure Chrome is installed." |

---

## Appendix A: ADB Commands Reference

```bash
# Verify notification channels
adb shell dumpsys notification --noredact | grep -A10 "fairbridge"

# Simulate Doze mode
adb shell dumpsys deviceidle force-idle
adb shell dumpsys deviceidle unforce

# Check battery optimization status
adb shell dumpsys deviceidle whitelist | grep fairbridge

# Verify FLAG_SECURE (check window flags)
adb shell dumpsys window windows | grep -A5 "fairbridge"

# Check keystore security level
# (requires custom debug build with logging)
adb logcat -s FairBridgeKeychain

# Trigger FCM via test endpoint
curl -X POST https://api.fairbridge.app/test/send-fcm \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"type": "payment_received", "device_token": "$FCM_TOKEN"}'
```

## Appendix B: OEM Battery Optimization Settings Deep Links

| OEM | Setting Path | Intent Action |
|-----|-------------|--------------|
| Samsung One UI | Settings > Battery > App Power Management > Unrestricted | `android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` |
| Xiaomi MIUI | Security app > Permissions > Autostart | `miui.intent.action.APP_PERM_EDITOR` |
| Xiaomi HyperOS | Settings > Apps > FairBridge > Battery > No restrictions | `android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` |
| OnePlus OxygenOS | Settings > Battery > Battery Optimization > FairBridge | `android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` |
| Stock Android | Settings > Apps > FairBridge > Battery > Unrestricted | `android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` |

## Appendix C: Test Environment Setup

1. **Physical device farm**: BrowserStack App Automate — configured with all 10 devices in matrix
2. **FCM test endpoint**: Backend test endpoint at `/test/send-fcm` (gated by test API key, disabled in production)
3. **Stripe test mode**: All Stripe Financial Connections tests use Stripe test credentials; test bank: "Stripe Test Bank" (institution ID: `ins_109508`)
4. **CI integration**: Smoke tests (Section 12.1) run automatically on each PR; full regression run manually before release candidate

---

## 14. Addendum: MVP Context Updates (v1.1, 2026-03-18)

Additional test cases required from MVP context clarification.

### 14.1 DV Safety — Push Notification Payload Sanitization

**TC-DV-001: No sensitive content in FCM payload visible on lock screen**
- Action: Trigger payment_received FCM while device is locked (screen off)
- Expected: Lock screen notification shows generic text only (e.g., "You have a new update in FairBridge") — NO dollar amounts, NO co-parent names, NO transaction details
- Pass criteria: Lock screen preview contains no financial data; full details only visible after unlock and app open
- Device coverage: All 10 devices (lock screen rendering varies by OEM skin)

**TC-DV-002: No sensitive content in notification shade preview**
- Action: Pull down notification shade without unlocking device
- Expected: Notification body shows generic text; amount and party names NOT in notification body
- Pass criteria: No PII or financial figures visible in notification preview
- Note: This is a non-negotiable DV safety requirement — an abuser viewing a partner's phone must not learn payment amounts or co-parent activity from the lock screen

**TC-DV-003: No cross-parent activity timestamps in Android UI**
- Action: Navigate to expense list, payment history, and calendar views
- Expected: No "last seen" / "read at" / "viewed at" timestamps exposed for the other parent's activity
- Pass criteria: UI shows event dates (when expense was submitted) but never shows when the other parent viewed or acted on a record

**TC-DV-004: Safety resources link accessible in settings**
- Action: Navigate to Settings > Safety & Privacy (or equivalent)
- Expected: DV hotline link visible (e.g., National DV Hotline: 1-800-799-7233)
- Pass criteria: Link visible; tapping opens dialer or browser with correct resource; link present on all 10 devices

### 14.2 Payment Amount Validation — $5 Minimum

**TC-PAY-001: Payment blocked below $5 minimum**
- Action: Attempt to initiate ACH payment for $4.99
- Expected: Form validation error: "Minimum payment amount is $5.00"
- Pass criteria: Error shown inline (not after submission); payment NOT submitted to backend

**TC-PAY-002: Expense amount below $5 — warning vs block**
- Action: Submit expense for $3.00 (expenses can be logged below $5; only payments are blocked)
- Expected: Expense submits successfully; no $5 minimum error
- Pass criteria: Expense created; $5 minimum only applies to ACH payment initiation

### 14.3 Expense Rate Limiting — Soft Limit Behavior

**TC-RATE-001: Soft rate limit at 10-15 expenses/day**
- Action: Submit 15 expenses in a single day
- Expected: After 10th expense, app shows advisory warning: "You're submitting expenses quickly — your co-parent will need to review these"
- Pass criteria: Warning shown; expenses still accepted (soft limit, not hard block); backend applies server-side rate limiting above 15

**TC-RATE-002: Collapse key behavior with rate-limited expense burst**
- Action: Submit 12 expenses rapidly (within 60 seconds) — within soft limit
- Expected: FCM notifications batch via collapse key; co-parent receives ≤2 notifications (not 12)
- Pass criteria: Notification count in shade ≤ 2 after all 12 expenses submitted; existing TC-CHAN-007 pass criteria apply

### 14.4 Co-Parent Verification — Child Name + Birth Year

**TC-VERIFY-001: Asymmetric verification — matching child name + birth year**
- Action: Payer enters child name "Olivia" + birth year "2019"; payee independently enters "Olivia" + "2019"
- Expected: Verification passes; co-parenting link established
- Pass criteria: Pairing succeeds; no full DOB required (birth year only)

**TC-VERIFY-002: Verification fails — mismatched birth year**
- Action: Payer enters "2019"; payee enters "2018"
- Expected: Verification fails with generic error (no hint about which field is wrong — DV safety)
- Pass criteria: Error shown to payee; payer not notified of failed attempt (prevents enumeration)

**TC-VERIFY-003: Verification — Unicode and special character names**
- Action: Enter child name with accented characters (e.g., "José") or hyphen ("Mary-Jane")
- Expected: Verification matches correctly regardless of case and with standard Unicode normalization
- Pass criteria: "josé" matches "José"; "mary-jane" matches "Mary-Jane" (case-insensitive, NFC normalized)

**TC-VERIFY-004: Verification — name entered in wrong order**
- Action: Child's name is "Emma Rose"; payer enters "Emma Rose", payee enters "Rose Emma"
- Expected: Verification fails (name order matters — no fuzzy matching to prevent false positives)
- Pass criteria: Pairing does not succeed with reversed name order; error shown
