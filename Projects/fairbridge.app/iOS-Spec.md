# FairBridge iOS Implementation Specification

**Platform**: iOS 16.0+
**Framework**: React Native (Expo) with bare workflow (required for native module access)
**Author**: ios-dev agent
**Date**: 2026-03-17

---

## 1. Executive Summary

FairBridge's iOS implementation sits inside a React Native (Expo) bare workflow. The bare workflow is mandatory — managed workflow cannot expose the native modules required for APNs time-sensitive notifications, PHPickerViewController, EventKit write-only access, Keychain biometric protection, or app-switcher content masking. This document specifies every iOS-specific surface, permission, entitlement, and App Store submission strategy needed to ship the FairBridge MVP.

---

## 2. Minimum Deployment Target

| Setting | Value |
|---------|-------|
| Minimum iOS version | **16.0** |
| Xcode minimum | 15.0 |
| Swift version | 5.9 |
| Expo SDK | 51+ (bare workflow) |

**Rationale**: iOS 16.0 covers ~95%+ of active iPhones as of 2026. It provides:
- `UNNotificationInterruptionLevel.timeSensitive` (iOS 15+)
- PHPickerViewController stable API (iOS 14+)
- `NSCalendarsWriteOnlyAccessUsageDescription` (iOS 17+ key, but write-only permission backfilled to iOS 16 via `EKAuthorizationStatus`)
- Background task scheduling improvements

---

## 3. Push Notifications (APNs)

### 3.1 APNs Setup

FairBridge requires push notifications for expense confirmation requests, payment status updates, and calendar change alerts. Notifications must arrive even when the app is backgrounded or terminated.

**Entitlements** (`FairBridge.entitlements`):
```xml
<key>aps-environment</key>
<string>production</string>
<key>com.apple.developer.usernotifications.time-sensitive</key>
<true/>
```

**Expo config** (`app.json`):
```json
{
  "expo": {
    "ios": {
      "entitlements": {
        "aps-environment": "production",
        "com.apple.developer.usernotifications.time-sensitive": true
      }
    }
  }
}
```

### 3.2 Time-Sensitive Notifications

Expense confirmation requests and payment failures are classified as **time-sensitive** (`UNNotificationInterruptionLevel.timeSensitive`). This bypasses Focus modes (Do Not Disturb) for a brief window and shows a yellow indicator in the notification.

**When to use time-sensitive**:
- Expense pending co-parent confirmation (>24h deadline)
- ACH payment failed (action required)
- Dispute filed by co-parent (response deadline)

**When NOT to use time-sensitive**:
- Payment succeeded (informational)
- Calendar reminder (non-urgent)
- App marketing / re-engagement

**DV safety constraint on payloads**: Push notification bodies are visible on the lock screen without authentication. No amounts, co-parent names, or child names may appear in `alert.title` or `alert.body`. Use generic language only — sensitive details are shown only after the user unlocks and opens the app.

**Backend payload** (APNs JSON — time-sensitive):
```json
{
  "aps": {
    "alert": {
      "title": "Expense needs your approval",
      "body": "An expense is waiting for your review in FairBridge."
    },
    "sound": "default",
    "interruption-level": "time-sensitive",
    "relevance-score": 0.9,
    "badge": 1
  },
  "fairbridge_type": "expense_confirmation",
  "expense_id": "exp_abc123"
}
```

**Standard (non-time-sensitive) payload**:
```json
{
  "aps": {
    "alert": { "title": "Payment update", "body": "A payment has been processed. Tap to view details." },
    "sound": "default",
    "interruption-level": "active"
  },
  "fairbridge_type": "payment_succeeded"
}
```

**Payload rules** (enforced by backend, verified by iOS test plan):
- No dollar amounts in `alert.body` or `alert.title`
- No co-parent names or child names in any visible push field
- `fairbridge_type` and `expense_id` travel as data-only fields outside `aps.alert` — not shown on lock screen
- Violation of these rules is a DV safety defect, not a UX issue — treat as P0

### 3.4 Notification Collapse (apns-collapse-id)

To prevent expense notification flooding when multiple updates arrive for the same expense, the backend must set the `apns-collapse-id` HTTP/2 header on the APNs request. This replaces a pending notification rather than stacking a new one.

**Collapse key format** (must match FCM collapse key format for backend consistency):
```
expense_update_{user_id}
```

**Backend responsibility** (APNs HTTP/2 request headers):
```
apns-collapse-id: expense_update_usr_abc123
apns-priority: 10
apns-push-type: alert
```

The collapse key is scoped to `user_id`, not `expense_id` — if a user has multiple pending expense confirmations, they receive a single "You have N expenses awaiting approval" notification (updated in place) rather than N separate notifications. The backend notification dispatch layer must maintain a pending-count and update the notification body accordingly when collapsing.

### 3.3 Notification Permission Gate UX

Notification permission **must be requested before pairing is allowed**. This is non-negotiable because:
1. Both parents must be reachable for the expense confirmation loop to function
2. A parent who denies notifications cannot participate in the two-party confirmation model

**Critical iOS constraint**: iOS grants each app exactly **one** system permission dialog for notifications per app lifetime. If the user dismisses it, the dialog can never be shown again (only Settings can re-enable). This means the timing and framing of the pre-prompt is critical.

**Permission gate flow** (aligned with UX Screen 8.1):
1. After email verification, **before** "Invite your co-parent" — show a full-screen pre-prompt rationale screen (our UI, not the system dialog)
2. Pre-prompt explains why notifications are required: "FairBridge needs notifications to alert you when expenses need approval."
3. Two options on pre-prompt screen:
   - "Enable Notifications" (primary) → immediately triggers the iOS system dialog → on grant, register token
   - "Not now" (secondary) → do NOT trigger the system dialog. Save the one-shot opportunity. Show inline banner on pairing screen instead.
4. **If "Not now" tapped**: record `notif_deferred = true` in local state. Show pairing screen with a soft banner. On any subsequent app open where `notif_deferred = true`, re-show the pre-prompt (but never the system dialog unless the pre-prompt primary CTA is tapped)
5. **If system dialog denied** (`.denied`): show one-time banner with deep link to `UIApplication.openSettingsURLString` — `UIApplication.shared.open(URL(string: UIApplication.openSettingsURLString)!)`
6. **If permanently denied** (checked via `getPermissionsAsync()` returning `.denied` without ever having shown dialog): treat same as step 5

```typescript
import * as Notifications from 'expo-notifications';
import { Linking } from 'react-native';

async function handleNotificationPrePromptCTA(): Promise<'granted' | 'denied' | 'deferred'> {
  const { status: existing } = await Notifications.getPermissionsAsync();
  if (existing === 'granted') return 'granted';

  // Only call requestPermissionsAsync when user explicitly taps the primary CTA
  // — never call speculatively, as this consumes the one-shot system dialog
  const { status } = await Notifications.requestPermissionsAsync({
    ios: {
      allowAlert: true,
      allowSound: true,
      allowBadge: true,
      allowCriticalAlerts: false,
      provideAppNotificationSettings: true,
    },
  });

  if (status === 'granted') {
    await registerAPNsToken();
    return 'granted';
  }
  return 'denied';
}

async function openNotificationSettings() {
  await Linking.openSettings(); // opens UIApplication.openSettingsURLString
}
```

**APNs device token registration** (UX Screen 8.2 — POST to `/user/push-token`):
```typescript
async function registerAPNsToken(): Promise<void> {
  const token = await Notifications.getDevicePushTokenAsync({
    projectId: Constants.expoConfig?.extra?.eas?.projectId,
  });
  // UX spec: POST /user/push-token (user_id from auth JWT)
  await api.post('/user/push-token', { token: token.data, platform: 'ios' });
}
```

---

## 4. Receipt Photo — PHPickerViewController

### 4.1 Why PHPickerViewController (Not UIImagePickerController)

iOS 14+ introduced `PHPickerViewController` as the privacy-safe replacement for `UIImagePickerController`. It requires **no photo library permission** (`NSPhotoLibraryUsageDescription`) — the system presents a sandboxed picker and returns only the selected image. This is the correct approach for FairBridge: we need one receipt photo, not access to the user's library.

**Info.plist**: No `NSPhotoLibraryUsageDescription` needed for read-only picker usage.

### 4.2 React Native Integration

Use `expo-image-picker` with `mediaTypes: ImagePicker.MediaTypeOptions.Images` — under the hood, Expo uses `PHPickerViewController` on iOS 14+, falling back to `UIImagePickerController` on older OS (irrelevant given our iOS 16 minimum).

```typescript
import * as ImagePicker from 'expo-image-picker';

async function pickReceiptPhoto(): Promise<string | null> {
  // No permission request needed for PHPicker on iOS 14+
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
    allowsEditing: true,
    aspect: [4, 3],
    quality: 0.8,
    allowsMultipleSelection: false,
  });

  if (!result.canceled && result.assets.length > 0) {
    return result.assets[0].uri; // local file:// URI
  }
  return null;
}
```

**Upload flow**: local URI → `expo-file-system` reads bytes → multipart POST to `/api/expenses/:id/receipt` → stored in Cloudflare R2 → returns CDN URL stored in DB.

### 4.3 Camera Capture (react-native-vision-camera)

For users who want to photograph a receipt in-app rather than selecting from library:

**Info.plist** (required):
```xml
<key>NSCameraUsageDescription</key>
<string>FairBridge uses your camera to photograph receipts for expense documentation.</string>
```

**Dependency**: `react-native-vision-camera` v4 (bare workflow, Expo plugin available)

```typescript
import { Camera, useCameraPermission } from 'react-native-vision-camera';

function ReceiptCameraScreen() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const camera = useRef<Camera>(null);

  async function captureReceipt() {
    const photo = await camera.current?.takePhoto({
      qualityPrioritization: 'balanced',
      flash: 'auto',
      enableAutoStabilization: true,
    });
    if (photo) {
      // photo.path is a file:// URI
      await uploadReceipt(photo.path);
    }
  }
  // ...
}
```

**Permission gate**: Camera permission requested only when user taps "Take Photo" — not at app launch. If denied, gracefully fall back to PHPickerViewController.

---

## 5. Calendar Export — EventKit

### 5.1 Overview

FairBridge generates `.ics` files representing custody schedule events. On iOS, these can be offered as:
1. **Share sheet** (no permission needed) — generates `.ics` file, user opens in Calendar.app manually
2. **Direct EventKit write** — writes events directly to the user's Calendar (requires `NSCalendarsWriteOnlyAccessUsageDescription` on iOS 17+)

MVP ships **both options**: share sheet as primary, direct write as secondary.

### 5.2 Info.plist Permissions

```xml
<!-- Required for direct EventKit write (iOS 17+) -->
<key>NSCalendarsWriteOnlyAccessUsageDescription</key>
<string>FairBridge can add custody schedule events directly to your calendar.</string>

<!-- Legacy key required for iOS 16 compatibility -->
<key>NSCalendarsUsageDescription</key>
<string>FairBridge adds custody schedule events to your calendar.</string>
```

### 5.3 Permission Flow

On iOS 17+, `EKAuthorizationStatus` has a new `.writeOnly` case. Request write-only access (not full read/write):

```typescript
import * as Calendar from 'expo-calendar';

async function requestCalendarWriteAccess(): Promise<boolean> {
  const { status } = await Calendar.requestCalendarPermissionsAsync();
  // expo-calendar maps to EKEventStore.requestWriteOnlyAccessToEvents on iOS 17+
  return status === 'granted';
}

async function addCustodyEventsToCalendar(events: CustodyEvent[]) {
  const hasPermission = await requestCalendarWriteAccess();
  if (!hasPermission) {
    // Fall back to share sheet .ics export
    await shareICSFile(events);
    return;
  }

  const calendarId = await getOrCreateFairBridgeCalendar();
  for (const event of events) {
    await Calendar.createEventAsync(calendarId, {
      title: event.title,
      startDate: event.start,
      endDate: event.end,
      notes: event.notes,
      alarms: [{ relativeOffset: -60 }], // 1h before
    });
  }
}
```

### 5.4 .ics Share Sheet (No Permission Required)

```typescript
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

async function shareICSFile(events: CustodyEvent[]) {
  const icsContent = generateICS(events); // standard RFC 5545 format
  const path = `${FileSystem.cacheDirectory}fairbridge-schedule.ics`;
  await FileSystem.writeAsStringAsync(path, icsContent, { encoding: 'utf8' });
  await Sharing.shareAsync(path, {
    mimeType: 'text/calendar',
    UTI: 'com.apple.ical.ics',
    dialogTitle: 'Export to Calendar',
  });
}
```

---

## 6. Keychain Storage

### 6.1 What Gets Stored in Keychain

| Item | Keychain key | Access class |
|------|-------------|--------------|
| Auth JWT (access token) | `fb_access_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| Refresh token | `fb_refresh_token` | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| Biometric-protected PIN | `fb_biometric_pin` | `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` + `biometryAny` |

**`ThisDeviceOnly`** prevents iCloud Keychain sync — auth tokens must not migrate to other devices. This also means tokens are lost on device restore from backup (acceptable — user re-authenticates).

### 6.2 React Native Implementation

Use `expo-secure-store` which wraps iOS Keychain:

```typescript
import * as SecureStore from 'expo-secure-store';

const TOKEN_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainService: 'com.fairbridge.app',
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  // Note: expo-secure-store does not yet expose biometryAny directly
  // For biometric gate, use requireAuthentication: true
};

async function saveAuthToken(token: string): Promise<void> {
  await SecureStore.setItemAsync('fb_access_token', token, TOKEN_OPTIONS);
}

async function getAuthToken(): Promise<string | null> {
  return SecureStore.getItemAsync('fb_access_token', TOKEN_OPTIONS);
}

async function deleteAuthToken(): Promise<void> {
  await SecureStore.deleteItemAsync('fb_access_token', TOKEN_OPTIONS);
}
```

**Biometric protection** for app unlock (optional, user-configurable):
```typescript
const BIOMETRIC_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainService: 'com.fairbridge.app.biometric',
  keychainAccessible: SecureStore.WHEN_PASSCODE_SET_THIS_DEVICE_ONLY,
  requireAuthentication: true, // triggers Face ID / Touch ID prompt
  authenticationPrompt: 'Authenticate to access FairBridge',
};
```

### 6.3 DV Safety Consideration

For DV safety mode ("silent deactivation"), call `deleteAuthToken()` and `clearAllKeychainItems()` when the user triggers silent wipe. This clears all local credentials without showing any confirmation dialog or indication to an observer.

---

## 7. App Switcher Content Masking

When the user presses the home button or swipes up, iOS takes a screenshot for the app switcher. Financial data (expense amounts, co-parent names, bank info) must not be visible in that screenshot.

### 7.1 Implementation

Use a React Native `AppState` listener to overlay a blur/mask view when the app goes to background:

```typescript
import { AppState, AppStateStatus } from 'react-native';
import { BlurView } from 'expo-blur';

function AppSwitcherMask() {
  const [isBackground, setIsBackground] = useState(false);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state: AppStateStatus) => {
      setIsBackground(state === 'inactive' || state === 'background');
    });
    return () => subscription.remove();
  }, []);

  if (!isBackground) return null;

  return (
    <BlurView
      intensity={100}
      tint="dark"
      style={StyleSheet.absoluteFillObject}
    >
      {/* FairBridge logo centered */}
      <Image source={require('./assets/logo-mask.png')} style={styles.maskLogo} />
    </BlurView>
  );
}
```

**Mount point**: At the root `<App />` level, above all navigation stacks. `'inactive'` state fires *before* the screenshot is taken on iOS, so the blur appears in the switcher.

**User setting**: Masking is ON by default. Users can disable it in Settings → Privacy → App Switcher Masking (off for low-risk users who don't share devices).

#### Screen Recording Detection (UIScreen.isCaptured)

Android's `FLAG_SECURE` blocks screenshots and screen recording on all financial screens. iOS has no equivalent system flag — the app-switcher BlurView covers the thumbnail but does not prevent screenshots or active screen recording. To achieve parity:

```typescript
import { NativeModules, NativeEventEmitter } from 'react-native';

// Custom native module wrapping UIScreen.isCaptured + UIScreenCapturedDidChangeNotification
// (requires bare workflow — add to ios/FairBridge/ScreenProtection.swift)
function useScreenRecordingProtection() {
  const [isCaptured, setIsCaptured] = useState(
    NativeModules.ScreenProtection?.isCaptured ?? false
  );

  useEffect(() => {
    const emitter = new NativeEventEmitter(NativeModules.ScreenProtection);
    const sub = emitter.addListener('screenCaptureChanged', ({ captured }) => {
      setIsCaptured(captured);
    });
    return () => sub.remove();
  }, []);

  return isCaptured;
}

// In root App component:
function AppRecordingMask() {
  const isCaptured = useScreenRecordingProtection();
  if (!isCaptured) return null;
  return (
    <BlurView intensity={100} tint="dark" style={StyleSheet.absoluteFillObject}>
      <Image source={require('./assets/logo-mask.png')} style={styles.maskLogo} />
    </BlurView>
  );
}
```

**Swift native module** (`ios/FairBridge/ScreenProtection.swift`):
```swift
@objc(ScreenProtection)
class ScreenProtection: RCTEventEmitter {
  override func startObserving() {
    NotificationCenter.default.addObserver(self,
      selector: #selector(captureDidChange),
      name: UIScreen.capturedDidChangeNotification,
      object: nil)
    // Fire initial state synchronously — handles the case where recording
    // was already active before the JS bridge initialized and registered
    // its listener. Without this, a cold-launch race (recording started
    // before root component mounts) drops the notification entirely.
    if UIScreen.main.isCaptured {
      sendEvent(withName: "screenCaptureChanged", body: ["captured": true])
    }
  }

  override func stopObserving() {
    NotificationCenter.default.removeObserver(self)
  }

  @objc func captureDidChange() {
    sendEvent(withName: "screenCaptureChanged",
      body: ["captured": UIScreen.main.isCaptured])
  }

  @objc func isCaptured(_ resolve: RCTPromiseResolveBlock, reject: RCTPromiseRejectBlock) {
    resolve(UIScreen.main.isCaptured)
  }

  override func supportedEvents() -> [String] {
    return ["screenCaptureChanged"]
  }
}
```

**Cold-launch timing note**: The `NotificationCenter` observer is registered when `startObserving()` fires (when the first JS listener attaches). This happens ~1–3 seconds into cold launch after the JS bridge initializes. The synchronous `isCaptured` check in `startObserving()` + the `NativeModules.ScreenProtection?.isCaptured` initial `useState` value together close this gap for practical cases. A narrow race remains if recording starts in the first ~100ms of cold launch before `startObserving()` runs — documented as a known V1 limitation (P2 test scenario).

**Limitation vs Android**: iOS cannot prevent screenshots via the system API — `UIScreen.isCaptured` detects recording but not static screenshots. This is a platform constraint, not a spec gap. DV safety documentation should note this difference.

---

## 7a. DV Safety — Settings Screen Requirements

The iOS Settings screen must include a **Safety Resources** section containing:
- Link to the National Domestic Violence Hotline (thehotline.org / 1-800-799-7233)
- "Delete my account and all data" destructive action (silent, no confirmation dialog that could be observed)
- "Deactivate silently" option — logs out and clears all local data without any visible completion screen

**Critical implementation detail — Safety Resources link**:
The DV hotline link must open in `SFSafariViewController` (in-app browser), NOT via `Linking.openURL()` which launches Safari. Reason: Safari maintains browser history. A co-parent inspecting the device's Safari history could discover the user sought DV resources. `SFSafariViewController` does not write to Safari history.

```typescript
import { WebBrowser } from 'expo-web-browser';

async function openSafetyResources() {
  await WebBrowser.openBrowserAsync('https://www.thehotline.org', {
    presentationStyle: WebBrowser.WebBrowserPresentationStyle.FORM_SHEET,
    createTask: false, // prevents adding to recent apps / history on Android
  });
}
```

**Silent deactivation** (see also Section 5 Keychain):
1. Clear all Keychain items (no dialog)
2. Clear AsyncStorage / MMKV local cache
3. Navigate to a blank/logo screen (no "Account deleted" toast)
4. After 2 seconds, reset navigation stack to the login screen
5. No analytics event fired for silent deactivation — no server-side log that could be subpoenaed by an abuser's attorney

---

## 8. Info.plist — Complete Permission Keys

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
  <!-- Camera: receipt photos -->
  <key>NSCameraUsageDescription</key>
  <string>FairBridge uses your camera to photograph receipts for expense documentation.</string>

  <!-- Calendar write (iOS 17+) -->
  <key>NSCalendarsWriteOnlyAccessUsageDescription</key>
  <string>FairBridge can add your custody schedule events directly to your calendar.</string>

  <!-- Calendar fallback key (iOS 16) -->
  <key>NSCalendarsUsageDescription</key>
  <string>FairBridge adds custody schedule events to your calendar.</string>

  <!-- Background processing for sync -->
  <key>UIBackgroundModes</key>
  <array>
    <string>remote-notification</string>
    <string>background-fetch</string>
    <string>processing</string>
  </array>

  <!-- No NSPhotoLibraryUsageDescription needed (PHPicker, no library access) -->
  <!-- No NSMicrophoneUsageDescription needed -->
  <!-- No NSLocationWhenInUseUsageDescription needed -->

  <!-- Face ID (for biometric unlock) -->
  <key>NSFaceIDUsageDescription</key>
  <string>FairBridge uses Face ID to protect your financial data.</string>
</dict>
</plist>
```

---

## 9. App Store Submission Strategy

### 9.1 Category & Rating

| Field | Value |
|-------|-------|
| Primary category | Finance |
| Secondary category | Lifestyle |
| Age rating | 4+ |
| Content rights | No third-party content |

### 9.2 Financial Services — IAP Exemption

Apple's App Store guidelines require IAP for digital goods sold within apps, with Apple taking 30%. However, **Guideline 3.1.3(b) — Person-to-Person Experiences** explicitly exempts peer-to-peer services:

> "Apps that allow a user to give a monetary gift to another individual, or to an individual performing a task or service as permitted by local law, are not required to use in-app purchase."

FairBridge's ACH payments are P2P transfers between co-parents — this is explicitly covered by 3.1.3(b). **No IAP required for payment transactions.**

**FairBridge subscription** (premium features: unlimited expenses, PDF export) must NOT be sold via IAP to avoid the 30% cut. Strategy:
- Subscription sold exclusively on web (`app.fairbridge.com/subscribe`) via Stripe
- In-app: show a paywall screen with text "Subscribe at fairbridge.com" — no in-app purchase button
- iOS 14+ allows explaining that subscription is available on the web (Apple updated rules in 2022 after antitrust pressure)
- No "Buy" or "Subscribe" button in the app — link is fine per current guidelines

**App Review notes to include**:
- "This app facilitates P2P financial transfers between co-parents per Guideline 3.1.3(b)"
- "Subscription is managed on our website per Guideline 3.1.1 — no in-app purchase is offered"

### 9.3 Stripe Connect Express — Review Considerations

App Review may flag the Stripe Connect Express onboarding (which opens a webview). Include a test account in App Review notes:
- Demo mode: show pre-configured mock co-parent pair with $0 test transactions
- Stripe test keys in the demo build submitted for review (NOT production keys)
- Explain in notes: "Bank linking uses Stripe Financial Connections (embedded webview) — users see Stripe's UI, not third-party banking credentials"

### 9.4 Privacy Nutrition Label (Privacy Manifest)

Required from iOS 17 / Xcode 15 (`PrivacyInfo.xcprivacy`):

| Data type | Collected | Linked to user | Used for tracking |
|-----------|-----------|---------------|------------------|
| Name | Yes | Yes | No |
| Email address | Yes | Yes | No |
| Financial info (bank account) | Yes | Yes | No |
| Photos/videos | Yes | Yes | No |
| Device ID | Yes | Yes | No |
| Crash data | Yes | No | No |

**No advertising data, no third-party tracking SDKs** (no Facebook SDK, no Amplitude, no Mixpanel in MVP).

### 9.5 Export Compliance

FairBridge uses HTTPS (TLS) only — standard encryption. Select "Yes, our app uses encryption" and "Yes, it qualifies for the exemption" (standard HTTPS). No export compliance documentation needed.

---

## 10. Expo Bare Workflow — Native Module Configuration

### 10.1 Required Native Dependencies

```json
{
  "dependencies": {
    "expo": "~51.0.0",
    "expo-notifications": "~0.28.0",
    "expo-image-picker": "~15.0.0",
    "expo-calendar": "~13.0.0",
    "expo-secure-store": "~13.0.0",
    "expo-blur": "~13.0.0",
    "expo-file-system": "~17.0.0",
    "expo-sharing": "~12.0.0",
    "react-native-vision-camera": "^4.0.0"
  }
}
```

### 10.2 Expo Plugins (app.json)

```json
{
  "expo": {
    "plugins": [
      ["expo-notifications", {
        "icon": "./assets/notification-icon.png",
        "color": "#2563EB",
        "sounds": [],
        "mode": "production"
      }],
      ["expo-image-picker", {
        "photosPermission": "FairBridge accesses your photos to attach receipts to expenses."
      }],
      ["expo-calendar", {
        "calendarPermission": "FairBridge adds custody schedule events to your calendar."
      }],
      "react-native-vision-camera"
    ]
  }
}
```

### 10.3 EAS Build Configuration

```json
{
  "build": {
    "production": {
      "ios": {
        "buildConfiguration": "Release",
        "credentialsSource": "remote",
        "autoIncrement": "buildNumber"
      }
    },
    "preview": {
      "ios": {
        "simulator": false,
        "buildConfiguration": "Release",
        "credentialsSource": "remote"
      }
    }
  }
}
```

---

## 11. Cross-Platform Parity Notes (for android-dev)

The following features require Android equivalents — coordinate with android-dev:

| iOS feature | Android equivalent |
|-------------|-------------------|
| APNs push | FCM (Firebase Cloud Messaging) |
| Time-sensitive notifications | High-priority FCM + `PRIORITY_HIGH` notification channel |
| PHPickerViewController | `ActivityResultContracts.PickVisualMedia` (Photo Picker API, Android 13+) |
| react-native-vision-camera | Same library (cross-platform) |
| EventKit write | `ContentResolver` calendar insert via `CalendarContract` |
| Keychain `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | Android Keystore `setUserAuthenticationRequired(true)` |
| App switcher masking (`AppState 'inactive'`) | `FLAG_SECURE` on Activity window |
| App Store IAP exemption | Google Play Billing exempt for P2P money transfers (same exemption exists) |
| `NSCalendarsWriteOnlyAccessUsageDescription` | `android.permission.WRITE_CALENDAR` (no read needed) |

**Notification channel/category IDs** (standardized with Android — use these exact IDs in backend FCM/APNs dispatch):

| ID | iOS interruption level | Android channel importance | Use cases |
|----|----------------------|--------------------------|-----------|
| `fairbridge_expenses` | `time-sensitive` | `IMPORTANCE_HIGH` | Expense pending co-parent approval (24h deadline), dispute filed |
| `fairbridge_payments` | `active` / `time-sensitive` | `IMPORTANCE_HIGH` | Payment succeeded (active), payment failed (time-sensitive) |
| `fairbridge_calendar` | `passive` | `IMPORTANCE_LOW` | Calendar reminders, custody schedule changes |

**Android note on payment importance granularity**: Android channel importance is set at channel creation and applies to all notifications on that channel — per-notification importance is not supported. Both payment success and payment failure land on `fairbridge_payments` (`IMPORTANCE_HIGH`). The urgency distinction (failure = time-sensitive, success = informational) is conveyed via notification body and action buttons rather than channel importance. iOS retains the full `interruption-level` split.

**iOS category registration** (map channel IDs to `UNNotificationCategory`):
```typescript
await Notifications.setNotificationCategoryAsync('fairbridge_expenses', [
  { identifier: 'APPROVE', buttonTitle: 'Approve', options: { opensAppToForeground: true } },
  { identifier: 'VIEW', buttonTitle: 'View', options: { opensAppToForeground: true } },
]);
await Notifications.setNotificationCategoryAsync('fairbridge_payments', []);
await Notifications.setNotificationCategoryAsync('fairbridge_calendar', []);
```

The backend sets `"fairbridge_channel": "fairbridge_expenses"` (or `fairbridge_payments`/`fairbridge_calendar`) in the data payload. iOS reads this to apply the correct category; Android uses it to route to the correct notification channel.

---

## 12. Security Considerations

1. **Certificate pinning** (**V2 — not V1**): `react-native-ssl-pinning` supports both iOS and Android (Android equivalent: `network_security_config.xml` with cert hash). Deferred to V2 because pinning requires an operational cert rotation process — a pinned cert that expires without a coordinated app update bricks the app for all users. V1 relies on TLS 1.3 + OS certificate validation, which is sufficient for MVP. Android-dev confirmed their V1 `network_security_config.xml` only disables cleartext; no pinning yet.
2. **Jailbreak detection**: Use `react-native-device-info` `isEmulator()` + basic jailbreak heuristics (e.g., check for `/Applications/Cydia.app`, `cydia://` URL scheme). Show a **warning only** — do not block app access. DV users may rely on jailbroken devices for safety apps; blocking would strand vulnerable users.
3. **Screenshot prevention**: iOS app-switcher masking via `AppState 'inactive'` + BlurView (Section 7) covers the thumbnail. `UIScreen.isCaptured` detects active screen recording (Section 7, recording detection). Static screenshot prevention is not possible on iOS at the OS level — documented platform gap vs Android `FLAG_SECURE`.
4. **Token refresh**: Access tokens expire in 15 minutes. Refresh tokens in 30 days. On Keychain read failure (device restarted without unlock), prompt re-auth gracefully — do not crash.
5. **Keychain mapping to Android Keystore** (aligned with android-dev):
   - Session tokens: `WHEN_UNLOCKED_THIS_DEVICE_ONLY` (iOS) ↔ `KeyGenParameterSpec` without `setUserAuthenticationRequired` + device-unlock dependency (Android). Accessible when phone is unlocked, no biometric prompt.
   - Biometric PIN (V2): `WHEN_PASSCODE_SET_THIS_DEVICE_ONLY` + `requireAuthentication: true` (iOS) ↔ `setUserAuthenticationRequired(true)` + `setInvalidatedByBiometricEnrollment(true)` (Android).

---

## 13. Stripe Web Flows — SFSafariViewController

Both Stripe flows (UX Screens 1.6 and 2.5) **must** use `SFSafariViewController`, not `WKWebView`.

**Why SFSafariViewController is required**:
- Shares the Safari cookie jar — users already logged into their bank don't re-enter credentials
- `WKWebView` has an isolated cookie store; bank OAuth redirects fail or require re-login
- Stripe's own iOS SDK wraps `SFSafariViewController` for this reason

**Screen 1.6 — Payer bank linking (Stripe Connect Express)**:
```typescript
import { useStripe } from '@stripe/stripe-react-native';

// Stripe React Native SDK opens SFSafariViewController internally
// for the Connect Express onboarding URL — no manual WebBrowser call needed
const { presentConnectSheet } = useStripe();

async function openStripeConnectOnboarding(accountLinkUrl: string) {
  // Stripe SDK handles SFSafariViewController presentation
  await Linking.openURL(accountLinkUrl);
  // Or use expo-web-browser which also uses SFSafariViewController:
  await WebBrowser.openAuthSessionAsync(accountLinkUrl, 'fairbridge://stripe-return');
}
```

**Screen 2.5 — Payee bank linking (Stripe Financial Connections)**:
```typescript
import { collectBankAccountForSetup } from '@stripe/stripe-react-native';

// Stripe Financial Connections uses a native sheet on iOS (not a webview)
// — it presents its own UIViewController sheet using ASWebAuthenticationSession
// which also shares Safari cookies
async function linkPayeeBankAccount(clientSecret: string) {
  const { paymentMethod, error } = await collectBankAccountForSetup({
    clientSecret,
    params: {
      paymentMethodType: 'us_bank_account',
      paymentMethodData: { billingDetails: { name: userName } },
    },
  });
}
```

**Do NOT use**: `WebBrowser.openBrowserAsync()` (opens full Safari, leaves history) or `WKWebView` component (isolated cookies, bank OAuth fails).

---

## 14. Universal Links

The payee invite link (`https://fairbridge.app/claim/[token]`) must open directly in the installed app. This requires Universal Links configuration (Apple's equivalent of Android App Links).

### 14.1 Apple App Site Association (AASA) File

The backend must serve this file at `https://fairbridge.app/.well-known/apple-app-site-association` with `Content-Type: application/json` (no `.json` extension):

```json
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "TEAMID.com.fairbridge.app",
        "paths": ["/claim/*", "/invite/*"]
      }
    ]
  }
}
```

### 14.2 Entitlements

```xml
<!-- FairBridge.entitlements -->
<key>com.apple.developer.associated-domains</key>
<array>
  <string>applinks:fairbridge.app</string>
</array>
```

### 14.3 React Native Handler

```typescript
import { Linking } from 'react-native';
import { useEffect } from 'react';

function useUniversalLinks() {
  useEffect(() => {
    // Handle cold-start Universal Link
    Linking.getInitialURL().then(url => {
      if (url) handleIncomingLink(url);
    });

    // Handle foreground Universal Link
    const sub = Linking.addEventListener('url', ({ url }) => handleIncomingLink(url));
    return () => sub.remove();
  }, []);
}

function handleIncomingLink(url: string) {
  const match = url.match(/\/claim\/([a-zA-Z0-9_-]+)/);
  if (match) {
    const token = match[1];
    // Navigate to payee onboarding with pre-filled invite token
    navigation.navigate('PayeeOnboarding', { inviteToken: token });
  }
}
```

### 14.4 Web Fallback

If the app is not installed, `fairbridge.app/claim/[token]` must serve a web page with:
- "Money is waiting for you" landing page (UX Screen 2.0)
- App Store download button
- After 1.5 seconds with no app response, show the web onboarding flow directly
- Store the invite token in a cookie/sessionStorage so it survives the App Store install → first launch flow via `SKAdNetwork` / deferred deep link (use Branch.io or Expo's built-in deferred linking)

---

## 15. Sign in with Apple

**App Store requirement**: "Sign in with Apple" must appear as the **first** social login option when any third-party social login is offered (App Store Guideline 4.8).

### 15.1 Button Ordering (UX Screens 1.3 / 2.2)

```
[ Sign in with Apple ]   ← MUST be first
[ Sign in with Google ]  ← secondary
[ Continue with email ]  ← tertiary
```

Violating this ordering is grounds for App Review rejection.

### 15.2 Implementation

```typescript
import * as AppleAuthentication from 'expo-apple-authentication';

async function signInWithApple() {
  const credential = await AppleAuthentication.signInAsync({
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
  });
  // credential.identityToken → send to backend for verification
  // NOTE: Apple only sends name/email on FIRST sign-in.
  // Store them immediately — subsequent sign-ins return null for name.
  await api.post('/auth/apple', {
    identityToken: credential.identityToken,
    fullName: credential.fullName,
    email: credential.email,
  });
}
```

**Critical Apple behavior**: `credential.fullName` and `credential.email` are only provided on the first authentication. If the backend fails to persist them on first call, they are lost permanently (user must revoke and re-authorize in their Apple ID settings). The backend must save these immediately.

### 15.3 Entitlement

```xml
<key>com.apple.developer.applesignin</key>
<array>
  <string>Default</string>
</array>
```

---

## 16. Accessibility (iOS-Specific Requirements)

All interactive elements must meet iOS accessibility standards — required for App Store review and non-negotiable per UX spec.

### 16.1 Touch Target Minimum

All tappable elements must be ≥ **44×44pt** (Apple HIG requirement). Use `minHeight: 44, minWidth: 44` in StyleSheet. For small visual elements (icons, badges), expand the hit area with `hitSlop`:

```typescript
<TouchableOpacity hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
  <Icon name="close" size={20} />
</TouchableOpacity>
```

### 16.2 Currency Amount Accessibility Labels

Screen readers read "$42.50" as "dollar sign forty-two point fifty". All currency display components must override the accessibility label:

```typescript
function CurrencyAmount({ cents }: { cents: number }) {
  const dollars = Math.floor(cents / 100);
  const centsRemainder = cents % 100;
  const displayText = `$${dollars}.${String(centsRemainder).padStart(2, '0')}`;
  const accessibilityLabel = `${dollars} dollar${dollars !== 1 ? 's' : ''} and ${centsRemainder} cent${centsRemainder !== 1 ? 's' : ''}`;

  return (
    <Text
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="text"
    >
      {displayText}
    </Text>
  );
}
```

### 16.3 Dynamic Type

All `Text` components must support Dynamic Type — use `allowFontScaling={true}` (default in RN) and never hardcode font sizes without a maximum scale cap on layout-critical elements:

```typescript
// Layout-critical elements (e.g., nav bar title) — cap at accessibility large
<Text maxFontSizeMultiplier={1.5} style={{ fontSize: 17 }}>
  FairBridge
</Text>

// Content text — allow full scaling
<Text style={{ fontSize: 16 }}>
  Expense description
</Text>
```

### 16.4 VoiceOver Semantic Roles

```typescript
// Expense list items
<TouchableOpacity
  accessibilityRole="button"
  accessibilityLabel={`Expense: ${description}, ${amountLabel}, pending approval`}
  accessibilityHint="Double tap to review this expense"
>

// Status badges
<View
  accessibilityRole="text"
  accessibilityLabel={`Status: ${statusText}`}
>
```

---

## 13. Open Questions for Team (updated)

~~1. UX-engineer: notification permission gate screen count~~ — resolved by UX spec (Screen 8.1: full-screen pre-prompt, "Not now" defers system dialog)
~~3. Program-manager: biometric app lock V1 or V2~~ — resolved: V2
~~4. Android-dev: vision-camera version~~ — resolved: v4 on both platforms

**Remaining open:**
1. **Backend-eng**: Confirm `/user/push-token` endpoint upserts on `(user_id, platform)` — reinstall generates new token, old must be replaced not accumulated.
2. **Backend-eng**: AASA file hosting — must be served at `https://fairbridge.app/.well-known/apple-app-site-association` with correct Content-Type before app ships. Confirm infra ownership.
3. **UX-engineer**: Deferred deep link on App Store install (invite token survives install) — do we use Branch.io or Expo's built-in deferred linking? This affects the Universal Links fallback web page implementation.
