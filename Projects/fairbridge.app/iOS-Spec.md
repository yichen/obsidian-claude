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

**Permission gate flow**:
1. After email verification but **before** the "Invite your co-parent" step, show a full-screen permission pre-prompt screen
2. Pre-prompt explains: "FairBridge needs notifications to alert you when expenses need approval. Without this, you may miss time-sensitive requests."
3. Primary CTA: "Enable Notifications" → calls `UNUserNotificationCenter.requestAuthorization(options: [.alert, .sound, .badge, .timeSensitive])`
4. If denied: show inline warning banner on the pairing screen. Pairing is **blocked** until the user either grants permission or explicitly acknowledges the limitation (secondary "Continue without notifications" button, shown only after one denial)
5. If permanently denied (`.denied` status): show deep link to Settings → FairBridge → Notifications

**React Native implementation**:
```typescript
import * as Notifications from 'expo-notifications';

async function requestNotificationPermission(): Promise<boolean> {
  const { status: existing } = await Notifications.getPermissionsAsync();
  if (existing === 'granted') return true;

  const { status } = await Notifications.requestPermissionsAsync({
    ios: {
      allowAlert: true,
      allowSound: true,
      allowBadge: true,
      allowCriticalAlerts: false, // don't request critical — App Review rejects unless medical/safety
      provideAppNotificationSettings: true,
    },
  });
  return status === 'granted';
}
```

**APNs device token registration**:
```typescript
// Register for remote notifications after permission granted
const token = await Notifications.getDevicePushTokenAsync({
  projectId: Constants.expoConfig?.extra?.eas?.projectId,
});
// Send token.data to backend: POST /api/devices/register
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
  }

  @objc func captureDidChange() {
    sendEvent(withName: "screenCaptureChanged",
      body: ["captured": UIScreen.main.isCaptured])
  }

  @objc func isCaptured(_ resolve: RCTPromiseResolveBlock, reject: RCTPromiseRejectBlock) {
    resolve(UIScreen.main.isCaptured)
  }
}
```

**Limitation vs Android**: iOS cannot prevent screenshots via the system API — `UIScreen.isCaptured` detects recording but not static screenshots. This is a platform constraint, not a spec gap. DV safety documentation should note this difference.

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

**Notification channels** (Android requires explicit channels; iOS uses categories):
- `EXPENSE_CONFIRMATION` — time-sensitive, sound on, vibrate
- `PAYMENT_STATUS` — default priority
- `CALENDAR_REMINDER` — low priority, no sound

---

## 12. Security Considerations

1. **Certificate pinning**: Use `react-native-ssl-pinning` or Expo's network security config to pin the FairBridge API certificate. Prevents MITM on financial data.
2. **Jailbreak detection**: Use `react-native-device-info` `isEmulator()` + basic jailbreak heuristics. Show warning (not block) if jailbreak detected — DV users may need jailbroken devices for safety apps.
3. **Screenshot prevention**: Consider `FLAG_SECURE` equivalent on sensitive screens (expense list, bank linking). iOS does not have a direct equivalent — the app switcher mask (section 7) is the primary protection.
4. **Token refresh**: Access tokens expire in 15 minutes. Refresh tokens in 30 days. On Keychain read failure (device restarted without unlock), handle gracefully — prompt re-auth instead of crash.

---

## 13. Open Questions for Team

1. **UX-engineer**: What is the exact screen count in the notification permission gate? Should the pre-prompt be a modal sheet or full-screen? (Coordinate with ux-engineer)
2. **Backend-eng**: APNs device token registration endpoint — is it `POST /api/devices/register` with `{ token, platform: 'ios', user_id }`? Confirm payload schema.
3. **Program-manager**: Should biometric app lock (Face ID) be V1 or V2? It's a significant UX and security win but adds complexity.
4. **Android-dev**: Confirm `react-native-vision-camera` v4 is used on Android too (same version) to avoid dependency divergence.
