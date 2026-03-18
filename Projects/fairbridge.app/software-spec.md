# FairBridge.app — MVP Software Specification

## Executive Summary

FairBridge is a co-parenting financial platform built on three pillars: ACH payments via Stripe Connect, append-only expense tracking with cryptographic integrity, and a shared custody calendar. The platform prioritizes domestic violence safety defaults, regulatory compliance (no MTL required via Stripe Connect), and a conversion-optimized payee onboarding funnel. This specification defines the complete MVP across backend, web, iOS, Android, and QA.

### Pricing Model

| Role | Price | Channel |
|------|-------|---------|
| Payer | $7/mo or $70/yr | Web-only (NOT Apple IAP) |
| Payee | Free forever | N/A |
| Transaction fee | 0.8% Stripe pass-through | No platform markup V1 |

### Key Success Metrics

| Metric | Target |
|--------|--------|
| Payee activation rate | >50% within 60 days |
| First ACH payment | <10 days from payer signup |
| Nacha unauthorized return rate | <0.5% |

### Pre-Launch Legal Cost

~$4-7K total: ACH authorization language, Reg E notice, AML policy, ToS addendum. Stripe is Nacha TPS; FairBridge is Originator. No MTL needed — launch all 50 states day one.

### Reg E Dispute Obligation

FairBridge must provide provisional credit within 10 business days. Losses absorbed from $5-10K reserve fund.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Backend Specification](#2-backend-specification)
   - 2.1 Database Schema (PostgreSQL)
   - 2.2 Append-Only Hash Chain and Merkle Root Anchoring
   - 2.3 REST API Endpoints
   - 2.4 Stripe Connect Integration
   - 2.5 ACH Payment Flow
   - 2.6 Webhook Handlers and Idempotency
   - 2.7 Notification Dispatch Pipeline
   - 2.8 Fraud Controls and Velocity Monitoring
   - 2.9 Co-Parent Verification (Asymmetric)
   - 2.10 Reg E Dispute Intake
   - 2.11 DV Safety Implementation (Backend)
3. [Web Frontend Specification](#3-web-frontend-specification)
   - 3.1 Web App Architecture (React)
   - 3.2 Subscription Management (Web-Only Purchase)
   - 3.3 Onboarding Flows (Payer and Payee)
   - 3.4 Expense Submission and Two-Party Confirmation UI
   - 3.5 Calendar View Components
   - 3.6 PDF Court Export with Hash Verification
   - 3.7 Stripe Connect Express Onboarding Modal
   - 3.8 Stripe Financial Connections Integration
   - 3.9 DV Safety Features (Web)
4. [UX Flows](#4-ux-flows)
   - 4.1 Payer Onboarding Journey
   - 4.2 Payee "Money Waiting" Invite and Conversion Funnel
   - 4.3 Expense Lifecycle: Submit, Confirm, Settle
   - 4.4 External Payment Logging (Venmo/Zelle/Check/Cash)
   - 4.5 Calendar Setup and Custody Pattern Selection
   - 4.6 Dispute Workflow (Expense Dispute + Evidence)
   - 4.7 DV Safety Flows
   - 4.8 Notification Permission Gates (iOS vs Android)
   - 4.9 Error States and Recovery Flows
5. [iOS Specification](#5-ios-specification)
   - 5.1 APNs Push Notification Configuration
   - 5.2 Notification Permission Gate UX
   - 5.3 Photo Picker and Camera (PHPicker + VisionCamera)
   - 5.4 Calendar Export (EventKit)
   - 5.5 Keychain Storage and Biometric Protection
   - 5.6 Screen Content Masking (App Switcher)
   - 5.7 App Store Submission Strategy
   - 5.8 Info.plist Permissions
6. [Android Specification](#6-android-specification)
   - 6.1 FCM High-Priority Configuration
   - 6.2 Battery Optimization Exemption
   - 6.3 Notification Channels and Collapse Keys
   - 6.4 Google Play Financial Services Declaration
   - 6.5 Android Keystore (EncryptedSharedPreferences)
   - 6.6 FLAG_SECURE on Financial Screens
   - 6.7 Camera and Calendar Integration
   - 6.8 WorkManager Background Sync
   - 6.9 ProGuard/R8 Obfuscation Rules
7. [Backend Test Plan](#7-backend-test-plan)
   - 7.1 Hash Chain Integrity Tests
   - 7.2 Stripe Webhook Handler Tests
   - 7.3 Webhook Idempotency and Dead-Letter Queue Tests
   - 7.4 ACH Payment E2E Tests
   - 7.5 Fraud Control Tests
   - 7.6 Co-Parent Verification Tests
   - 7.7 Notification Pipeline Tests
   - 7.8 Append-Only Constraint Verification
   - 7.9 Merkle Root Anchor Tests
   - 7.10 Load Testing Thresholds
   - 7.11 DV Safety Tests
8. [Web Frontend Test Plan](#8-web-frontend-test-plan)
   - 8.1 Component Unit Tests
   - 8.2 Onboarding Flow Integration Tests
   - 8.3 Expense Workflow E2E Tests
   - 8.4 Calendar Rendering Tests
   - 8.5 PDF Export Verification Tests
   - 8.6 Stripe Integration Tests
   - 8.7 Accessibility and DV Safety Tests
9. [iOS Test Plan](#9-ios-test-plan)
   - 9.1 APNs Delivery Tests
   - 9.2 Permission Flow Tests
   - 9.3 Photo/Camera Tests
   - 9.4 Keychain and Biometric Tests
   - 9.5 Screen Masking Tests
   - 9.6 Platform-Specific Edge Cases
10. [Android Test Plan](#10-android-test-plan)
    - 10.1 FCM Delivery Tests
    - 10.2 Battery Optimization Tests
    - 10.3 Notification Channel Tests
    - 10.4 Keystore Tests
    - 10.5 FLAG_SECURE Tests
    - 10.6 WorkManager Tests
    - 10.7 Platform-Specific Edge Cases
11. [Cross-Cutting Concerns](#11-cross-cutting-concerns)
    - 11.1 Authentication and Authorization
    - 11.2 DV Safety Defaults (System-Wide)
    - 11.3 Data Export and Deletion
    - 11.4 Regulatory Compliance Summary
    - 11.5 Deployment and Infrastructure
    - 11.6 Monitoring and Observability

---

## Technical Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Fastify (Node.js) |
| Database | PostgreSQL (append-only tables) |
| Queue | Redis + BullMQ |
| Object Storage | Cloudflare R2 |
| Email | Resend |
| SMS | Twilio |
| Payments | Stripe Connect Express + Financial Connections |
| Mobile | React Native (Expo) |
| Web | React |
| Auth | TBD (specify in Section 11.1) |
| CI/CD | TBD (specify in Section 11.5) |

---

## Section Ownership

| Section | Owner | Status |
|---------|-------|--------|
| 2. Backend Specification | backend-eng | Pending |
| 3. Web Frontend Specification | web-dev | Pending |
| 4. UX Flows | ux-engineer | Pending |
| 5. iOS Specification | ios-dev | Pending |
| 6. Android Specification | android-dev | Pending |
| 7. Backend Test Plan | backend-tester | Pending |
| 8. Web Frontend Test Plan | frontend-tester | Pending |
| 9. iOS Test Plan | ios-tester | Pending |
| 10. Android Test Plan | android-tester | Pending |
| 11. Cross-Cutting Concerns | security-eng | Pending |

---

## Key Design Constraints (All Sections Must Respect)

1. **Append-Only Data Model**: No UPDATE or DELETE on financial records. Every record includes SHA-256 hash of previous record. Daily Merkle root anchor.
2. **DV Safety Defaults**: No activity timestamps exposed to co-parent. Silent deactivation. Data export/delete. These are V1 non-negotiable.
3. **Stripe as TPS**: FairBridge is the Originator, Stripe is the Nacha Third-Party Sender. No independent TPS registration. No Money Transmitter Licenses needed.
4. **Web-Only Subscription Purchase**: Mobile apps do NOT sell subscriptions (avoids Apple 30% IAP cut). Subscription management is web-only.
5. **Payee Conversion is #1 Product Risk**: The "money waiting" invite flow must minimize steps. Target >50% conversion.
6. **Asymmetric Verification**: Co-parents independently enter child name + DOB. System matches without exposing one parent's data to the other.

---

<!-- SPEC SECTIONS BEGIN — Each teammate fills their section below -->

## 1. System Architecture Overview

*To be composed by program-manager after all sections are received.*

---

## 2. Backend Specification

*Owner: backend-eng — awaiting submission*

---

## 3. Web Frontend Specification

*Owner: web-dev — awaiting submission*

---

## 4. UX Flows

*Owner: ux-engineer — awaiting submission*

---

## 5. iOS Specification

**Platform**: iOS 16.0+ | **Framework**: React Native (Expo bare workflow) | **Owner**: ios-dev

> Expo bare workflow is mandatory — managed workflow cannot expose Keychain biometric, APNs time-sensitive entitlement, EventKit write-only (iOS 17+), or app-switcher content masking.

### 5.1 APNs Push Notification Configuration

FairBridge requires push notifications for expense confirmation, payment status, and calendar alerts. Notifications must arrive when backgrounded or terminated.

**Entitlements** (`FairBridge.entitlements`):
- `aps-environment`: production
- `com.apple.developer.usernotifications.time-sensitive`: true

**Time-sensitive notifications** (bypass Focus/DND):
- Expense pending co-parent confirmation (>24h deadline)
- ACH payment failed (action required)
- Dispute filed by co-parent (response deadline)

**Standard notifications**:
- Payment succeeded (informational)
- Calendar reminders (non-urgent)

**APNs payload format**: JSON with `interruption-level: "time-sensitive"` for urgent, `"active"` for standard. Custom keys: `fairbridge_type`, entity ID.

### 5.2 Notification Permission Gate UX

Notification permission **blocks pairing** — both parents must be reachable for the two-party confirmation model.

**Flow**:
1. After email verification, before "Invite co-parent" step: full-screen pre-prompt
2. Pre-prompt explains why notifications are required
3. CTA calls `UNUserNotificationCenter.requestAuthorization(options: [.alert, .sound, .badge, .timeSensitive])`
4. If denied: inline warning, pairing blocked. Secondary "Continue without notifications" shown only after one denial
5. If permanently denied: deep link to iOS Settings

**Token registration**: `expo-notifications` → `getDevicePushTokenAsync()` → `POST /api/devices` with `{ token, platform: 'ios' }`.

### 5.3 Photo Picker and Camera (PHPicker + VisionCamera)

**Receipt photo selection**: `expo-image-picker` wraps `PHPickerViewController` (iOS 14+). No `NSPhotoLibraryUsageDescription` needed — sandboxed picker returns only selected image.

**Camera capture**: `react-native-vision-camera` v4 (bare workflow). Requires `NSCameraUsageDescription`. Permission requested only on "Take Photo" tap. Falls back to PHPicker on denial.

**Upload**: local URI → `expo-file-system` → multipart POST `/api/expenses/:id/receipt` → Cloudflare R2 → CDN URL stored in DB.

### 5.4 Calendar Export (EventKit)

**Dual approach**:
1. **Direct EventKit write** (primary): iOS 17+ `EKAuthorizationStatus.writeOnly` via `expo-calendar`. Writes events to a dedicated "FairBridge" calendar.
2. **.ics share sheet** (fallback, no permission): Generates RFC 5545 `.ics` file, shared via `expo-sharing`.

**Info.plist keys**:
- `NSCalendarsWriteOnlyAccessUsageDescription` (iOS 17+)
- `NSCalendarsUsageDescription` (iOS 16 fallback)

### 5.5 Keychain Storage and Biometric Protection

| Item | Key | Access class |
|------|-----|-------------|
| Access JWT | `fb_access_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| Refresh token | `fb_refresh_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| Biometric PIN | `fb_biometric_pin` | `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` + `biometryAny` |

`ThisDeviceOnly` prevents iCloud Keychain sync. Tokens lost on restore from backup (re-auth required). Implementation via `expo-secure-store`.

**DV safety**: Silent deactivation clears all Keychain items without confirmation dialog.

**Biometric app lock (Face ID unlock)**: Deferred to V2. V1 uses Keychain biometric for token access only.

### 5.6 Screen Content Masking (App Switcher)

BlurView overlay (via `expo-blur`) activated on `AppState 'inactive'` — fires before iOS takes the app switcher screenshot. Shows FairBridge logo over blurred content.

- Mounted at root `<App />` level above all navigation
- ON by default, user-configurable in Settings > Privacy
- `'inactive'` triggers before screenshot on iOS

### 5.7 App Store Submission Strategy

**Category**: Finance (primary), Lifestyle (secondary). Age rating: 4+.

**IAP exemption**: ACH payments are P2P transfers — exempt under Guideline 3.1.3(b). No IAP for payment transactions.

**Subscription**: Sold exclusively on web (`app.fairbridge.com/subscribe`). In-app paywall shows "Subscribe at fairbridge.com" — no purchase button. Permitted under current guidelines (post-2022 antitrust update).

**App Review notes**:
- P2P financial transfers per Guideline 3.1.3(b)
- Web-only subscription per Guideline 3.1.1
- Stripe test keys in review build with demo co-parent pair

**Privacy Manifest** (`PrivacyInfo.xcprivacy`): Name, email, financial info, photos, device ID, crash data collected. Linked to user. No tracking. No third-party ad SDKs.

**Export compliance**: HTTPS/TLS only — qualifies for standard exemption.

### 5.8 Info.plist Permissions

| Key | Purpose |
|-----|---------|
| `NSCameraUsageDescription` | Receipt photo capture |
| `NSCalendarsWriteOnlyAccessUsageDescription` | Calendar export (iOS 17+) |
| `NSCalendarsUsageDescription` | Calendar export (iOS 16 fallback) |
| `NSFaceIDUsageDescription` | Biometric data protection |
| `UIBackgroundModes` | `remote-notification`, `background-fetch`, `processing` |

Not needed: `NSPhotoLibraryUsageDescription` (PHPicker), `NSMicrophoneUsageDescription`, `NSLocationWhenInUseUsageDescription`.

**Native dependencies**: expo ~51.0.0, expo-notifications, expo-image-picker, expo-calendar, expo-secure-store, expo-blur, expo-file-system, expo-sharing, react-native-vision-camera ^4.0.0.

**Security**: Certificate pinning via `react-native-ssl-pinning`. Jailbreak detection (warning only, not blocking — DV users may need jailbroken devices). Token refresh: 15min access, 30-day refresh.

**Cross-platform parity table**: See full iOS spec at `/Users/ychen2/Obsidian/Projects/fairbridge.app/iOS-Spec.md` Section 11 for Android equivalents.

---

## 6. Android Specification

*Owner: android-dev — awaiting submission*

---

## 7. Backend Test Plan

*Owner: backend-tester — awaiting submission*

---

## 8. Web Frontend Test Plan

*Owner: frontend-tester — awaiting submission*

---

## 9. iOS Test Plan

*Owner: ios-tester — awaiting submission*

---

## 10. Android Test Plan

*Owner: android-tester — awaiting submission*

---

## 11. Cross-Cutting Concerns

*Owner: program-manager — to be composed after integration*

---

## Appendix

- A. Stripe Webhook Event Reference
- B. API Endpoint Catalog
- C. Database Schema Diagram
- D. DV Safety Checklist
- E. Regulatory Compliance Matrix
