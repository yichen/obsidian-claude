# FairBridge Android Implementation Specification

**Platform**: Android (React Native / Expo)
**Minimum API Level**: 24 (Android 7.0 Nougat)
**Target API Level**: 35 (Android 15)
**Build System**: Gradle with R8/ProGuard
**Author**: android-dev

---

## 1. Project Configuration

### 1.1 Manifest Permissions

All required permissions must be declared in `AndroidManifest.xml`. Permissions are grouped by feature area to make Play Store declarations straightforward.

```xml
<!-- Notifications -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
<uses-permission android:name="android.permission.VIBRATE" />

<!-- Camera -->
<uses-permission android:name="android.permission.CAMERA" />

<!-- Calendar -->
<uses-permission android:name="android.permission.WRITE_CALENDAR" />
<uses-permission android:name="android.permission.READ_CALENDAR" />

<!-- Background work -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />

<!-- Battery optimization exemption (must be explicitly declared) -->
<uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />

<!-- Network state (for WorkManager retry logic) -->
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Biometrics (for Keystore-backed credential storage) -->
<uses-permission android:name="android.permission.USE_BIOMETRIC" />
<uses-permission android:name="android.permission.USE_FINGERPRINT" />

<!-- Hardware features (not required — graceful degradation) -->
<uses-feature android:name="android.hardware.camera" android:required="false" />
<uses-feature android:name="android.hardware.fingerprint" android:required="false" />
```

### 1.2 Application-Level Manifest Settings

```xml
<application
    android:name=".MainApplication"
    android:label="@string/app_name"
    android:icon="@mipmap/ic_launcher"
    android:roundIcon="@mipmap/ic_launcher_round"
    android:allowBackup="false"
    android:fullBackupContent="false"
    android:dataExtractionRules="@xml/data_extraction_rules"
    android:networkSecurityConfig="@xml/network_security_config"
    android:theme="@style/AppTheme">
```

`allowBackup="false"` and `fullBackupContent="false"` prevent Android Auto Backup from uploading financial data and credentials to Google Drive. This is a hard security requirement — no exceptions.

### 1.3 Minimum SDK and Build Configuration

`android/build.gradle`:
```groovy
android {
    compileSdk 35
    defaultConfig {
        minSdk 24
        targetSdk 35
        versionCode 1
        versionName "1.0.0"
    }
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

---

## 2. Push Notifications — Firebase Cloud Messaging (FCM)

### 2.1 FCM High-Priority Message Configuration

FairBridge requires high-priority FCM messages so that payment and expense notifications wake the device even when the app is in the background or the phone is in Doze mode.

Backend sends all FCM payloads with `priority: "high"` and `content_available: true`:

```json
{
  "message": {
    "token": "<device_fcm_token>",
    "android": {
      "priority": "HIGH",
      "notification": {
        "channel_id": "fairbridge_payments",
        "notification_priority": "PRIORITY_HIGH",
        "title": "Payment update",
        "body": "A payment has been completed. Tap to view details.",
        "default_sound": true,
        "default_vibrate_timings": true,
        "click_action": "FLUTTER_NOTIFICATION_CLICK"
      },
      "data": {
        "type": "payment_succeeded",
        "payment_id": "<uuid>",
        "amount_cents": "5000",
        "deeplink": "fairbridge://payments/<uuid>"
      }
    },
    "fcm_options": {
      "analytics_label": "payment_notification"
    }
  }
}
```

**Critical**: The `android.priority` field at the message level controls delivery priority (wake device). The `notification.notification_priority` field controls how the notification is displayed in the shade. Both must be set for correct behavior.

**Payment failure vs success**: Both route to the `fairbridge_payments` channel (IMPORTANCE_HIGH). Android does not support per-notification importance overrides within a channel — importance is fixed at channel creation. The distinction between payment failure urgency and payment success (informational) is communicated through notification body copy and action buttons, not channel importance. Users who find success notifications too prominent can downgrade the channel manually in system settings (this is preserved across app updates per Section 2.2 TC-CHAN-005). iOS handles this more granularly via `interruption-level: time-sensitive` (failure) vs `interruption-level: active` (success) — an inherent platform difference.

### 2.2 Notification Channels

Notification channels must be created before the first notification is displayed. FairBridge creates three channels at app startup in `MainApplication.onCreate()` via a native module.

| Channel ID | Display Name | Importance | Lock Screen | Use Case |
|---|---|---|---|---|
| `payments` | Payment Alerts | `IMPORTANCE_HIGH` | `VISIBILITY_PRIVATE` | Payment initiated, succeeded, failed, dispute |
| `expenses` | Expense Updates | `IMPORTANCE_HIGH` | `VISIBILITY_PRIVATE` | Expense confirmation requests (deadline-sensitive), batch updates |
| `calendar` | Schedule Reminders | `IMPORTANCE_LOW` | `VISIBILITY_PUBLIC` | Custody handoff reminders, calendar sync |

```kotlin
// android/app/src/main/java/com/fairbridge/NotificationChannelModule.kt
class NotificationChannelModule(private val context: Context) {

    fun createChannels() {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val paymentsChannel = NotificationChannel(
            "fairbridge_payments",
            "Payment Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Notifications for payment activity including transfers and disputes"
            enableLights(true)
            lightColor = Color.GREEN
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 250, 250, 250)
            lockscreenVisibility = Notification.VISIBILITY_PRIVATE
        }

        val expensesChannel = NotificationChannel(
            "fairbridge_expenses",
            "Expense Updates",
            NotificationManager.IMPORTANCE_HIGH  // HIGH: expense confirmation has a deadline (matches iOS time-sensitive)
        ).apply {
            description = "Notifications for co-parent expense submissions and confirmations"
            lockscreenVisibility = Notification.VISIBILITY_PRIVATE
        }

        val calendarChannel = NotificationChannel(
            "fairbridge_calendar",
            "Schedule Reminders",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Custody schedule reminders and calendar sync updates"
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        }

        notificationManager.createNotificationChannels(
            listOf(paymentsChannel, expensesChannel, calendarChannel)
        )
    }
}
```

**DV Safety**: `payments` and `expenses` channels use `VISIBILITY_PRIVATE` — the notification appears on lock screen but hides the content text, showing only "FairBridge" instead of payment amounts or expense details.

### 2.3 Collapse Keys for Expense Notification Batching

When a co-parent submits multiple expenses rapidly (e.g., uploading a batch of receipts), the backend uses FCM collapse keys to prevent notification flooding. Only the most recent notification for the same collapse key is shown; earlier ones are replaced.

Backend collapse key strategy:
- **Expense notifications**: `collapse_key = "expense_update_{other_parent_user_id}"` — one pending expense notification per co-parent pair
- **Payment notifications**: No collapse key — every payment event is distinct and must be delivered
- **Calendar notifications**: `collapse_key = "calendar_sync"` — one sync notification at a time

Backend payload for expense batching:
```json
{
  "message": {
    "token": "<device_token>",
    "android": {
      "collapse_key": "expense_update_user_abc123",
      "priority": "NORMAL",
      "notification": {
        "channel_id": "fairbridge_expenses",
        "title": "3 expenses pending review",
        "body": "Your co-parent submitted new expenses"
      },
      "data": {
        "type": "expense_batch",
        "pending_count": "3",
        "deeplink": "fairbridge://expenses/pending"
      }
    }
  }
}
```

### 2.4 Notification Permission Gate

On Android 13+ (API 33+), `POST_NOTIFICATIONS` is a runtime permission. FairBridge requests it during onboarding, before pairing.

```typescript
// In React Native (via expo-notifications)
import * as Notifications from 'expo-notifications';

async function requestNotificationPermission(): Promise<boolean> {
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  if (existingStatus === 'granted') return true;

  // On Android 12 and below, this always returns 'granted' without a prompt
  const { status } = await Notifications.requestPermissionsAsync({
    android: {
      allowAlert: true,
      allowBadge: true,
      allowSound: true,
    },
  });

  return status === 'granted';
}
```

If permission is denied, show an in-app banner explaining that payment alerts require notifications. Do not block onboarding — the user can enable notifications later from Settings.

---

## 3. Battery Optimization Exemption

### 3.1 Why This Is Required

Android's Doze mode and App Standby can delay or drop FCM messages for apps not on the battery optimization exemption list. For FairBridge, delayed payment notifications are a trust-destroying UX failure. The app must be exempted.

### 3.2 Implementation

Prompt for exemption during onboarding, after notification permission is granted. Use `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` which shows the system dialog (no Play Store policy violation for financial apps).

```kotlin
// android/app/src/main/java/com/fairbridge/BatteryOptimizationModule.kt
@ReactMethod
fun requestBatteryOptimizationExemption() {
    val packageName = reactApplicationContext.packageName
    val pm = reactApplicationContext.getSystemService(Context.POWER_SERVICE) as PowerManager

    if (!pm.isIgnoringBatteryOptimizations(packageName)) {
        val intent = Intent().apply {
            action = Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
            data = Uri.parse("package:$packageName")
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        reactApplicationContext.startActivity(intent)
    }
}

@ReactMethod
fun isExemptFromBatteryOptimization(promise: Promise) {
    val packageName = reactApplicationContext.packageName
    val pm = reactApplicationContext.getSystemService(Context.POWER_SERVICE) as PowerManager
    promise.resolve(pm.isIgnoringBatteryOptimizations(packageName))
}
```

```typescript
// React Native side
import { NativeModules } from 'react-native';
const { BatteryOptimizationModule } = NativeModules;

async function promptBatteryExemption() {
  const isExempt = await BatteryOptimizationModule.isExemptFromBatteryOptimization();
  if (!isExempt) {
    // Show in-app explanation screen first
    // "FairBridge needs to run in the background to deliver payment alerts reliably"
    // User taps "Allow" → system dialog appears
    BatteryOptimizationModule.requestBatteryOptimizationExemption();
  }
}
```

**Onboarding placement**: Show after notification permission, before co-parent pairing. Frame it as: "Allow FairBridge to run in the background so you never miss a payment alert."

**API-level timing**:
- API 33+: fire immediately after the notification permission dialog closes (regardless of grant or deny)
- API 24–32: no notification permission prompt exists; fire after email verification, before co-parent pairing

**Re-prompt suppression**: If the user denies the exemption, do not re-prompt on every launch. Re-prompt at most once every 7 days.

```kotlin
val prefs = context.getSharedPreferences("fairbridge_prefs", Context.MODE_PRIVATE)
val lastPromptMs = prefs.getLong("battery_opt_prompt_last_ms", 0L)
val sevenDaysMs = 7 * 24 * 60 * 60 * 1000L
if ((System.currentTimeMillis() - lastPromptMs) > sevenDaysMs) {
    prefs.edit().putLong("battery_opt_prompt_last_ms", System.currentTimeMillis()).apply()
    requestBatteryOptimizationExemption()
}
```

**OEM-specific Autostart (Xiaomi)**:

Xiaomi devices require BOTH battery optimization exemption AND Autostart permission for reliable FCM delivery. The Autostart setting location differs by firmware:

- **MIUI 14** (e.g., Xiaomi 13): Autostart lives in the MIUI Security app. Use this intent:
  ```kotlin
  Intent("miui.intent.action.APP_PERM_EDITOR").apply {
      setClassName("com.miui.securitycenter",
          "com.miui.permcenter.autostart.AutoStartManagementActivity")
      putExtra("pkg_name", packageName)
  }
  ```
- **HyperOS 1.0** (e.g., Xiaomi 14): Autostart moved to native Settings. Use the standard `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` intent — it routes to the correct screen on HyperOS.

Detect via presence of the MIUI Security app package (`com.miui.securitycenter`) to branch:
```kotlin
fun isMiuiWithSecurityApp(context: Context): Boolean {
    return try {
        context.packageManager.getPackageInfo("com.miui.securitycenter", 0)
        true
    } catch (e: PackageManager.NameNotFoundException) { false }
}
```

**Play Store compliance**: `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` is explicitly permitted for apps that need reliable background message delivery. FairBridge qualifies under the "financial transactions" exemption. No additional Play Store policy declaration needed for this specific permission (unlike some others).

---

## 4. Security

### 4.1 Android Keystore via react-native-keychain

All sensitive data (Stripe tokens, session tokens, biometric-protected data) is stored using Android Keystore-backed storage via `react-native-keychain`. On Android 6+, this uses hardware-backed key storage when available.

```typescript
import * as Keychain from 'react-native-keychain';

// Store a credential (e.g., session token)
async function storeSecureCredential(key: string, value: string): Promise<void> {
  await Keychain.setGenericPassword(key, value, {
    service: `com.fairbridge.${key}`,
    accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    securityLevel: Keychain.SECURITY_LEVEL.SECURE_HARDWARE, // Requires hardware-backed key
    storage: Keychain.STORAGE_TYPE.RSA, // Use RSA for Android Keystore
  });
}

// Retrieve with biometric authentication
async function getSecureCredential(key: string): Promise<string | null> {
  const result = await Keychain.getGenericPassword({
    service: `com.fairbridge.${key}`,
    authenticationPrompt: {
      title: 'Verify your identity',
      subtitle: 'Access your FairBridge account',
      cancel: 'Cancel',
    },
  });
  if (result === false) return null;
  return result.password;
}
```

**EncryptedSharedPreferences fallback**: On devices where hardware-backed Keystore is unavailable (API 24-27 without StrongBox), `react-native-keychain` falls back to `EncryptedSharedPreferences` with software-backed AES-256-GCM. This is acceptable for MVP.

**What is stored in Keystore**:
- Session/refresh tokens
- Stripe ephemeral keys (short-lived; store only if needed across app restarts)
- Device pairing secret (used for co-parent pairing verification)

**What is NOT stored** (use in-memory only):
- Payment amounts during active transaction
- Raw bank account numbers (Stripe Financial Connections never returns these to the app)

### 4.2 FLAG_SECURE on Financial Screens

`FLAG_SECURE` prevents screenshots, screen recording, and appearance in the recent apps (recents) thumbnail for financial screens. This is a mandatory Android security requirement for any screen displaying payment amounts, bank details, or expense history.

```kotlin
// android/app/src/main/java/com/fairbridge/SecureScreenModule.kt
class SecureScreenModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName() = "SecureScreenModule"

    @ReactMethod
    fun enableSecureScreen() {
        val activity = currentActivity ?: return
        activity.runOnUiThread {
            activity.window.setFlags(
                WindowManager.LayoutParams.FLAG_SECURE,
                WindowManager.LayoutParams.FLAG_SECURE
            )
        }
    }

    @ReactMethod
    fun disableSecureScreen() {
        val activity = currentActivity ?: return
        activity.runOnUiThread {
            activity.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }
}
```

```typescript
// React Native hook — apply to all financial screens
import { useEffect } from 'react';
import { NativeModules } from 'react-native';

const { SecureScreenModule } = NativeModules;

export function useSecureScreen() {
  useEffect(() => {
    SecureScreenModule?.enableSecureScreen();
    return () => {
      SecureScreenModule?.disableSecureScreen();
    };
  }, []);
}
```

**Screens requiring FLAG_SECURE**:
- Payment initiation and confirmation
- Payment history / transaction detail
- Bank account linking (Stripe Financial Connections)
- Expense list and detail with amounts
- Any screen showing full bank account numbers or routing numbers

**Screens exempt** (FLAG_SECURE disabled):
- Login / signup
- Custody calendar (no financial data)
- Settings (except payment settings sub-screen)
- Safety resources screen

### 4.3 Network Security Configuration

`android/app/src/main/res/xml/network_security_config.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.fairbridge.app</domain>
        <domain includeSubdomains="true">stripe.com</domain>
    </domain-config>
</network-security-config>
```

Cleartext (HTTP) is disabled globally. All traffic must use TLS 1.2+. This blocks MITM attacks in development environments that might accidentally be using HTTP.

### 4.4 Data Extraction Rules (Android 12+)

`android/app/src/main/res/xml/data_extraction_rules.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="sharedpref" path="." />
        <exclude domain="database" path="." />
        <exclude domain="file" path="." />
    </cloud-backup>
    <device-transfer>
        <exclude domain="sharedpref" path="." />
        <exclude domain="database" path="." />
    </device-transfer>
</data-extraction-rules>
```

This prevents any local data from being included in Google Drive backup or device-to-device transfer. Combined with `allowBackup="false"`, this is belt-and-suspenders protection for financial data.

---

## 5. Camera — CameraX via react-native-vision-camera

### 5.1 Package Configuration

```bash
npx expo install react-native-vision-camera
```

`app.json` Expo plugin config:
```json
{
  "expo": {
    "plugins": [
      [
        "react-native-vision-camera",
        {
          "cameraPermissionText": "FairBridge needs camera access to capture receipts for expense tracking",
          "enableMicrophonePermission": false
        }
      ]
    ]
  }
}
```

`enableMicrophonePermission: false` — FairBridge only captures still images, never video. This avoids requesting a microphone permission that Play Store reviewers would flag.

### 5.2 CameraX Configuration

react-native-vision-camera uses CameraX internally. The following configuration targets receipt capture quality:

```typescript
import { Camera, useCameraDevice, useCodeScanner } from 'react-native-vision-camera';

export function ReceiptCaptureScreen() {
  const device = useCameraDevice('back');

  // Request permission on mount
  useEffect(() => {
    Camera.requestCameraPermission();
  }, []);

  const photoConfig = {
    photo: true,
    video: false,
    audio: false,
  };

  return (
    <Camera
      style={StyleSheet.absoluteFill}
      device={device}
      isActive={true}
      photo={true}
      // Optimize for document/receipt capture
      photoQualityBalance="quality"
      // Torch for dark environments
      torch="off"
      // Disable zoom gestures on financial screens (accidental UX)
      enableZoomGesture={false}
    />
  );
}
```

### 5.3 Image Processing Pipeline

After capture, receipts are:
1. Compressed to JPEG at 80% quality (typically 200-500KB)
2. Resized to max 2048px on the longest dimension
3. Uploaded to Cloudflare R2 via a signed upload URL from the backend
4. The R2 object key is stored in the expense record

```typescript
async function captureAndUploadReceipt(cameraRef: Camera): Promise<string> {
  const photo = await cameraRef.takePhoto({
    qualityPrioritization: 'quality',
    flash: 'off',
    enableShutterSound: false,
  });

  // Compress before upload
  const compressed = await ImageResizer.resize(photo.path, 2048, 2048, 'JPEG', 80);

  // Get signed upload URL from backend
  const { uploadUrl, objectKey } = await api.getReceiptUploadUrl();

  // Upload directly to R2
  await fetch(uploadUrl, {
    method: 'PUT',
    body: await FileSystem.readAsStringAsync(compressed.uri, { encoding: 'base64' }),
    headers: { 'Content-Type': 'image/jpeg' },
  });

  return objectKey;
}
```

---

## 6. Calendar Export — CalendarContract

### 6.1 Custody Calendar Export Flow

The CalendarContract API writes custody handoff events directly to the user's device calendar. This is the Android-native approach (versus iOS EventKit).

```kotlin
// android/app/src/main/java/com/fairbridge/CalendarModule.kt
@ReactMethod
fun exportCustodyEvents(eventsJson: String, promise: Promise) {
    val activity = currentActivity
    if (activity == null) {
        promise.reject("NO_ACTIVITY", "No current activity")
        return
    }

    // Check permission first
    if (ContextCompat.checkSelfPermission(reactApplicationContext, Manifest.permission.WRITE_CALENDAR)
        != PackageManager.PERMISSION_GRANTED) {
        promise.reject("PERMISSION_DENIED", "Calendar write permission not granted")
        return
    }

    try {
        val events = JSONArray(eventsJson)
        val resolver = reactApplicationContext.contentResolver

        // Find or create FairBridge calendar
        val calendarId = getOrCreateFairBridgeCalendar(resolver)

        var insertedCount = 0
        for (i in 0 until events.length()) {
            val event = events.getJSONObject(i)
            insertCalendarEvent(resolver, calendarId, event)
            insertedCount++
        }

        promise.resolve(insertedCount)
    } catch (e: Exception) {
        promise.reject("EXPORT_ERROR", e.message)
    }
}

private fun getOrCreateFairBridgeCalendar(resolver: ContentResolver): Long {
    // Check for existing FairBridge calendar
    val projection = arrayOf(CalendarContract.Calendars._ID)
    val selection = "${CalendarContract.Calendars.ACCOUNT_NAME} = ? AND " +
                    "${CalendarContract.Calendars.ACCOUNT_TYPE} = ?"
    val selectionArgs = arrayOf("FairBridge", CalendarContract.ACCOUNT_TYPE_LOCAL)

    resolver.query(
        CalendarContract.Calendars.CONTENT_URI,
        projection, selection, selectionArgs, null
    )?.use { cursor ->
        if (cursor.moveToFirst()) {
            return cursor.getLong(0)
        }
    }

    // Create new local calendar
    val values = ContentValues().apply {
        put(CalendarContract.Calendars.ACCOUNT_NAME, "FairBridge")
        put(CalendarContract.Calendars.ACCOUNT_TYPE, CalendarContract.ACCOUNT_TYPE_LOCAL)
        put(CalendarContract.Calendars.NAME, "FairBridge Custody")
        put(CalendarContract.Calendars.CALENDAR_DISPLAY_NAME, "FairBridge Custody")
        put(CalendarContract.Calendars.CALENDAR_COLOR, 0xFF1A73E8.toInt())
        put(CalendarContract.Calendars.CALENDAR_ACCESS_LEVEL,
            CalendarContract.Calendars.CAL_ACCESS_OWNER)
        put(CalendarContract.Calendars.OWNER_ACCOUNT, "FairBridge")
        put(CalendarContract.Calendars.VISIBLE, 1)
        put(CalendarContract.Calendars.SYNC_EVENTS, 1)
    }

    val uri = CalendarContract.Calendars.CONTENT_URI.buildUpon()
        .appendQueryParameter(CalendarContract.CALLER_IS_SYNCADAPTER, "true")
        .appendQueryParameter(CalendarContract.Calendars.ACCOUNT_NAME, "FairBridge")
        .appendQueryParameter(CalendarContract.Calendars.ACCOUNT_TYPE,
            CalendarContract.ACCOUNT_TYPE_LOCAL)
        .build()

    return ContentUris.parseId(resolver.insert(uri, values)!!)
}

private fun insertCalendarEvent(resolver: ContentResolver, calendarId: Long, event: JSONObject) {
    val values = ContentValues().apply {
        put(CalendarContract.Events.CALENDAR_ID, calendarId)
        put(CalendarContract.Events.TITLE, event.getString("title"))
        put(CalendarContract.Events.DESCRIPTION, event.optString("description", ""))
        put(CalendarContract.Events.DTSTART, event.getLong("startMs"))
        put(CalendarContract.Events.DTEND, event.getLong("endMs"))
        put(CalendarContract.Events.ALL_DAY, if (event.optBoolean("allDay", false)) 1 else 0)
        put(CalendarContract.Events.EVENT_TIMEZONE, event.optString("timezone", "UTC"))
        put(CalendarContract.Events.EVENT_COLOR, 0xFF1A73E8.toInt())
        // Mark as FairBridge-managed so we can identify/update later
        put(CalendarContract.Events.CUSTOM_APP_PACKAGE, "com.fairbridge.app")
        put(CalendarContract.Events.CUSTOM_APP_URI, "fairbridge://calendar/${event.getString("id")}")
    }
    resolver.insert(CalendarContract.Events.CONTENT_URI, values)
}
```

### 6.2 Runtime Permission Request

```typescript
import { PermissionsAndroid, Platform } from 'react-native';

async function requestCalendarPermission(): Promise<boolean> {
  if (Platform.OS !== 'android') return true;

  const granted = await PermissionsAndroid.requestMultiple([
    PermissionsAndroid.PERMISSIONS.WRITE_CALENDAR,
    PermissionsAndroid.PERMISSIONS.READ_CALENDAR,
  ]);

  return (
    granted[PermissionsAndroid.PERMISSIONS.WRITE_CALENDAR] === 'granted' &&
    granted[PermissionsAndroid.PERMISSIONS.READ_CALENDAR] === 'granted'
  );
}
```

---

## 7. WorkManager — Background Payment Status Sync

### 7.1 Why WorkManager

WorkManager is the correct Android API for deferrable, guaranteed background work. It survives process death, device reboots, and battery optimization. FairBridge uses it to poll for payment status updates when the app is in the background — particularly important for ACH payments which can take 1-3 business days.

### 7.2 Worker Implementation

```kotlin
// android/app/src/main/java/com/fairbridge/PaymentSyncWorker.kt
class PaymentSyncWorker(context: Context, workerParams: WorkerParameters) :
    CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            val apiBaseUrl = applicationContext.getString(R.string.api_base_url)
            val sessionToken = getStoredSessionToken() ?: return Result.success()

            // Fetch pending payment statuses from backend
            val response = httpClient.get("$apiBaseUrl/api/v1/payments/pending") {
                header("Authorization", "Bearer $sessionToken")
            }

            if (response.status.isSuccess()) {
                val updates = response.body<List<PaymentUpdate>>()

                // Send local notification for any terminal state changes
                updates.filter { it.isTerminalState() }.forEach { update ->
                    sendPaymentNotification(update)
                }

                // Store results in local DB / shared preferences for app to read on next open
                storePaymentUpdates(updates)

                Result.success()
            } else if (response.status.value in 500..599) {
                // Server error — retry with backoff
                Result.retry()
            } else {
                // 4xx — don't retry, something is wrong with auth/request
                Result.success()
            }
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }
}
```

### 7.3 WorkManager Scheduling

```kotlin
// android/app/src/main/java/com/fairbridge/WorkManagerSetup.kt
fun schedulePaymentSync(context: Context) {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build()

    val syncRequest = PeriodicWorkRequestBuilder<PaymentSyncWorker>(
        repeatInterval = 15,
        repeatIntervalTimeUnit = TimeUnit.MINUTES,
        // Flex window: run anywhere in the last 5 minutes of the interval
        flexTimeInterval = 5,
        flexTimeIntervalUnit = TimeUnit.MINUTES
    )
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
        .addTag("payment_sync")
        .build()

    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        "payment_sync",
        ExistingPeriodicWorkPolicy.KEEP, // Don't restart if already scheduled
        syncRequest
    )
}
```

**15-minute minimum**: WorkManager enforces a 15-minute minimum interval for periodic work. For real-time payment updates, FCM push notifications (Section 2) are the primary delivery mechanism. WorkManager is the fallback for when FCM is delayed by battery optimization.

### 7.4 Immediate Reconnection Sync (NetworkCallback + One-Shot WorkRequest)

The 15-minute periodic job is too slow for the offline-queue flush use case. When the device regains connectivity after being offline, FairBridge must immediately sync any queued expenses. Implement this via `ConnectivityManager.NetworkCallback`:

```kotlin
// android/app/src/main/java/com/fairbridge/NetworkReconnectModule.kt
class NetworkReconnectModule(private val context: Context) {

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            // Network just became available — enqueue a one-shot sync immediately
            enqueueImmediateSync()
        }
    }

    fun register() {
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()
        connectivityManager.registerNetworkCallback(request, networkCallback)
    }

    fun unregister() {
        connectivityManager.unregisterNetworkCallback(networkCallback)
    }

    private fun enqueueImmediateSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncRequest = OneTimeWorkRequestBuilder<PaymentSyncWorker>()
            .setConstraints(constraints)
            .addTag("payment_sync_immediate")
            .build()

        WorkManager.getInstance(context).enqueueUniqueWork(
            "payment_sync_immediate",
            ExistingWorkPolicy.REPLACE, // Replace any pending immediate sync
            syncRequest
        )
    }
}
```

**Expected latency**: ~30–90 seconds on stock Android after network reconnect. On Samsung/Xiaomi with battery optimization exemption: ~60–120 seconds. This is the trigger for TC-OFF-005 in the Android test plan.

Register the callback in `MainApplication.onCreate()` and unregister in `onTerminate()`. The callback is process-scoped — if the app process is killed while offline, the periodic WorkManager job handles sync on next background execution.

### 7.5 Boot Receiver

WorkManager re-schedules itself after device reboot, but the React Native app bridge may not be initialized. Use a `BroadcastReceiver` for the boot signal:

```kotlin
// android/app/src/main/java/com/fairbridge/BootReceiver.kt
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            WorkManagerSetup.schedulePaymentSync(context)
        }
    }
}
```

```xml
<!-- In AndroidManifest.xml -->
<receiver android:name=".BootReceiver" android:exported="false">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED" />
    </intent-filter>
</receiver>
```

---

## 8. Google Play Store — Financial Services Declaration

### 8.1 Play Console Declarations Required

FairBridge must complete the **Financial Services** declaration in Play Console before the app can be published or reviewed. Required declarations:

**App type**: Personal finance app with peer-to-peer payment functionality
**Payment processing**: Third-party (Stripe) — FairBridge does not hold funds
**Target audience**: Adults (18+) — not a family app in the Play Store sense

### 8.2 Sensitive Permissions Declaration

The following permissions require justification in Play Console:

| Permission | Justification |
|---|---|
| `CAMERA` | Receipt capture for expense documentation |
| `READ_CALENDAR` / `WRITE_CALENDAR` | Export custody schedule to device calendar |
| `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` | Reliable delivery of payment alerts |
| `FOREGROUND_SERVICE` | Background payment status sync |

### 8.3 Data Safety Section

Play Console Data Safety form responses:

**Data collected**:
- Name and email (required, account management, shared with Stripe for identity verification)
- Financial info: payment history, bank account (required, app functionality, encrypted in transit)
- Photos and videos: receipt images (optional, expense documentation, not shared with third parties except R2 storage)
- Device identifiers: FCM token (required, push notifications)

**Data NOT collected**:
- Location data
- Contacts
- SMS or call logs
- Health or fitness data
- Browsing or search history

**Data sharing**: Payment-related data shared with Stripe (payment processing). No data sold. No data used for advertising.

### 8.4 Target API Level

Must target API 35 (Android 15) for all new apps submitted after August 2025. `targetSdk 35` is set in `build.gradle` (Section 1.3).

---

## 9. ProGuard / R8 Obfuscation Rules

### 9.1 Stripe SDK Rules

```proguard
# proguard-rules.pro

# Stripe Android SDK — required to prevent R8 from stripping reflection-used classes
-keep class com.stripe.android.** { *; }
-keep class com.stripe.android.model.** { *; }
-keep class com.stripe.android.core.** { *; }
-keepclassmembers class com.stripe.android.** {
    @com.google.gson.annotations.SerializedName <fields>;
}

# Stripe 3DS2 (required for card payments, even if ACH is primary)
-keep class com.stripe.android.stripe3ds2.** { *; }

# Prevent stripping of Stripe's coroutines usage
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
```

### 9.2 React Native Rules

```proguard
# React Native core
-keep class com.facebook.react.** { *; }
-keep class com.facebook.hermes.** { *; }
-keep class com.facebook.jni.** { *; }
-dontwarn com.facebook.react.**

# react-native-keychain (uses reflection for Keystore access)
-keep class com.oblador.keychain.** { *; }
-keep class androidx.biometric.** { *; }

# react-native-vision-camera (CameraX)
-keep class com.mrousavy.camera.** { *; }
-keep class androidx.camera.** { *; }

# WorkManager
-keep class androidx.work.** { *; }
-keep class com.fairbridge.PaymentSyncWorker { *; }

# Firebase / FCM
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.firebase.**
```

### 9.3 General Security Rules

```proguard
# Remove logging in release builds
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int d(...);
    public static int v(...);
    public static int i(...);
}

# Prevent deobfuscation via stack traces (keep mapping file for crash reporting)
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Keep custom exceptions for meaningful crash reports
-keep public class * extends java.lang.Exception

# Remove debug-only code
-assumenosideeffects class kotlin.jvm.internal.Intrinsics {
    static void checkParameterIsNotNull(java.lang.Object, java.lang.String);
    static void checkNotNullParameter(java.lang.Object, java.lang.String);
}
```

### 9.4 Upload Mapping File

After each release build, upload the `mapping.txt` file to Firebase Crashlytics (or equivalent crash reporting service) so that obfuscated stack traces in production crashes can be deobfuscated. This is required to debug production payment failures.

```bash
# In CI/CD pipeline after release build
./gradlew bundleRelease
# Upload mapping to Crashlytics
./gradlew uploadCrashlyticsMappingFileRelease
```

---

## 10. Cross-Platform Parity with iOS

The following table documents Android vs iOS implementation differences for features that appear in both platform specs. This ensures the program-manager can identify any gaps.

| Feature | Android | iOS |
|---|---|---|
| Push notifications | FCM high-priority + channels | APNs + time-sensitive interruption level |
| Credential storage | Android Keystore / EncryptedSharedPreferences | Keychain (`kSecAttrAccessibleWhenUnlockedThisDeviceOnly`) |
| Screenshot prevention | `FLAG_SECURE` blocks screenshots AND recording | **Platform limit**: iOS cannot block static screenshots at OS level |
| Screen recording detection | `FLAG_SECURE` blocks recording capture automatically | `UIScreen.capturedDidChangeNotification` + BlurView overlay |
| App switcher masking | `FLAG_SECURE` blanks thumbnail on financial screens | `AppState 'inactive'` + BlurView (global, unconditional) |
| Camera | CameraX via react-native-vision-camera v4 | AVFoundation via react-native-vision-camera v4 (same TS API) |
| Gallery selection | System Photo Picker (API 33+, no permission); `READ_EXTERNAL_STORAGE` on API 24–32 | PHPickerViewController (no library permission, iOS 14+) |
| Calendar export | CalendarContract — writes to device calendar directly | EventKit write-only OR `.ics` share sheet fallback |
| Background sync | WorkManager 15-min periodic (guaranteed) + NetworkCallback one-shot on reconnect | BGAppRefreshTask (discretionary, OS-scheduled) |
| Battery/background | `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` + OEM AutoStart (Samsung, Xiaomi, Huawei) | No equivalent — APNs handles wakeup without exemption |
| Notification permission | Runtime `POST_NOTIFICATIONS` (API 33+ only); denial count tracked; permanent deny → Settings | Runtime always required; pre-prompt rationale screen; permanent deny → Settings deep link |
| Notification batching | FCM `collapse_key: "expense_update_{user_id}"` | APNs `apns-collapse-id: "expense_update_{user_id}"` (same format) |
| Stripe bank linking | Chrome Custom Tab (shares Chrome cookies); fallback to `ACTION_VIEW` | SFSafariViewController (shares Safari cookies) |
| Payee invite deep link | Android App Links (`https://` + `assetlinks.json`) | Universal Links (`https://` + `apple-app-site-association`) |
| Quick Exit (DV safety) | `finishAndRemoveTask()` — removes from Recents entirely | `UIApplication.shared` home simulation |
| Minimum OS | Android 7.0 (API 24) ~95% coverage | iOS 16.0 ~97% coverage |

**Confirmed platform asymmetry — DV safety disclosure required**: Android `FLAG_SECURE` blocks both static screenshots and screen recording on financial screens. iOS can detect and overlay screen recording via `UIScreen.capturedDidChangeNotification` but cannot prevent static screenshots at the OS level. This difference must be disclosed in FairBridge's DV safety documentation and reviewed by security-eng in Section 11.

**Notification collapse key alignment (CONFIRMED)**: Backend must set both `collapse_key` (FCM Android field) and `apns-collapse-id` (APNs HTTP/2 header) to the same value `expense_update_{user_id}`. Both platforms collapse to a single "N expenses awaiting approval" notification. Backend-eng owns this dual-field dispatch.

**Background sync authoritative path (CONFIRMED)**: FCM/APNs push is the authoritative ACH payment status delivery mechanism on both platforms. WorkManager (Android) and BGAppRefreshTask (iOS) are belt-and-suspenders fallbacks only.

---

## 11. Expo Configuration Summary

`app.json` Android-specific section:
```json
{
  "expo": {
    "android": {
      "package": "app.fairbridge",
      "versionCode": 1,
      "compileSdkVersion": 35,
      "targetSdkVersion": 35,
      "minSdkVersion": 24,
      "adaptiveIcon": {
        "foregroundImage": "./assets/icon-foreground.png",
        "backgroundColor": "#FFFFFF"
      },
      "permissions": [
        "POST_NOTIFICATIONS",
        "RECEIVE_BOOT_COMPLETED",
        "VIBRATE",
        "CAMERA",
        "WRITE_CALENDAR",
        "READ_CALENDAR",
        "FOREGROUND_SERVICE",
        "FOREGROUND_SERVICE_DATA_SYNC",
        "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
        "ACCESS_NETWORK_STATE",
        "USE_BIOMETRIC",
        "USE_FINGERPRINT"
      ],
      "googleServicesFile": "./google-services.json",
      "allowBackup": false
    },
    "plugins": [
      [
        "react-native-vision-camera",
        {
          "cameraPermissionText": "FairBridge needs camera access to capture receipts",
          "enableMicrophonePermission": false
        }
      ],
      "expo-notifications",
      "expo-secure-store",
      [
        "expo-build-properties",
        {
          "android": {
            "compileSdkVersion": 35,
            "targetSdkVersion": 35,
            "minSdkVersion": 24
          }
        }
      ]
    ]
  }
}
```

---

## 12. Native Module Registration

All custom native modules must be registered in `MainApplication.kt`:

```kotlin
// android/app/src/main/java/com/fairbridge/MainApplication.kt
override fun getPackages(): List<ReactPackage> = listOf(
    MainReactPackage(),
    NotificationChannelPackage(),    // Creates FCM channels on startup
    BatteryOptimizationPackage(),    // Battery exemption prompt (all OEMs)
    SecureScreenPackage(),           // FLAG_SECURE management
    CalendarPackage(),               // CalendarContract export
    ChromeTabPackage(),              // Chrome Custom Tabs for Stripe flows
    QuickExitPackage(),              // DV safety quick exit
)

override fun onCreate() {
    super.onCreate()
    // Create notification channels immediately on app start
    NotificationChannelModule(this).createChannels()
    // Schedule background payment sync
    WorkManagerSetup.schedulePaymentSync(this)
}
```

---

## 13. UX-Driven Android Requirements

Additional implementation requirements derived from `UX-Flows-Spec.md` Screens 1.6, 2.0–2.5, 7.4, 8.3, 9.x.

### 13.1 Chrome Custom Tabs for Stripe Flows (Screens 1.6, 2.5)

Stripe Financial Connections and Stripe Connect Express onboarding must open in a Chrome Custom Tab — NOT a `WebView`. Chrome Custom Tabs share the user's Chrome cookie jar, enabling credential-free bank OAuth (user already logged into their bank in Chrome). `WebView` does not share cookies and breaks this flow.

```kotlin
// android/app/src/main/java/com/fairbridge/ChromeTabModule.kt
@ReactMethod
fun openInCCT(url: String) {
    val activity = currentActivity ?: return
    val chromePackage = getChromePackage(activity)

    if (chromePackage != null) {
        val customTabsIntent = CustomTabsIntent.Builder()
            .setToolbarColor(ContextCompat.getColor(activity, R.color.fairbridge_blue))
            .setShowTitle(true)
            .build()
        customTabsIntent.intent.setPackage(chromePackage)
        customTabsIntent.launchUrl(activity, Uri.parse(url))
    } else {
        // Fallback: open in default browser via ACTION_VIEW
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
    }
}

private fun getChromePackage(context: Context): String? {
    val candidates = listOf(
        "com.android.chrome",           // Chrome stable
        "com.chrome.beta",              // Chrome Beta
        "com.chrome.dev",               // Chrome Dev
        "org.mozilla.firefox",          // Firefox (supports CCT)
        "com.samsung.android.sbrowser", // Samsung Internet (supports CCT)
    )
    val pm = context.packageManager
    return candidates.firstOrNull { pkg ->
        try { pm.getPackageInfo(pkg, 0); true } catch (e: PackageManager.NameNotFoundException) { false }
    }
}
```

```typescript
// React Native — open Stripe URL in CCT
import { NativeModules } from 'react-native';
const { ChromeTabModule } = NativeModules;

async function openStripeConnect(stripeUrl: string) {
  ChromeTabModule.openInCCT(stripeUrl);
}
```

**Screen 1.6 (payer bank linking)** and **Screen 2.5 (payee bank linking)** both use this. The CCT closes automatically when Stripe redirects back to `fairbridge://stripe-callback` — handle the intent in the manifest:

```xml
<activity android:name=".MainActivity">
  <intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="fairbridge" android:host="stripe-callback" />
  </intent-filter>
</activity>
```

### 13.2 Android App Links for Payee Invite (Screens 2.0–2.2)

Payee invite links must use Android App Links (verified deep links) so that tapping the invite in SMS/email opens the app directly rather than the browser. If the app is not installed, the link falls back to the web landing page.

**Manifest intent filter** (requires asset links verification at `https://app.fairbridge.app/.well-known/assetlinks.json`):
```xml
<activity android:name=".MainActivity">
  <intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https"
          android:host="app.fairbridge.app"
          android:pathPrefix="/invite" />
  </intent-filter>
</activity>
```

**`assetlinks.json`** must be served at `https://app.fairbridge.app/.well-known/assetlinks.json` with the app's release keystore SHA-256 fingerprint. This is a backend/infra requirement to coordinate with backend-eng.

**React Native — read the invite token on app launch**:
```typescript
import { Linking } from 'react-native';

async function getInitialInviteToken(): Promise<string | null> {
  const url = await Linking.getInitialURL();
  if (url?.includes('/invite/')) {
    return url.split('/invite/')[1].split('?')[0];
  }
  return null;
}

// Also handle links when app is already open
Linking.addEventListener('url', ({ url }) => {
  if (url?.includes('/invite/')) {
    const token = url.split('/invite/')[1].split('?')[0];
    navigateToPayeeOnboarding(token);
  }
});
```

After install and first launch, the invite token must be preserved through the signup flow (store in `AsyncStorage` until account creation completes, then POST to backend to link the pair).

### 13.3 Notification Permission — Denial Count Tracking (Screen 8.3)

Android allows `requestPermissions` for `POST_NOTIFICATIONS` up to 2 times before the system permanently suppresses the dialog (showing "Don't ask again"). Track the denial count to show the correct recovery UI.

```typescript
import { PermissionsAndroid, Linking, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

async function requestNotificationPermissionWithTracking(): Promise<'granted' | 'denied' | 'permanent_deny'> {
  if (Platform.OS !== 'android' || Platform.Version < 33) {
    return 'granted'; // API <33: notifications granted by default, skip flow
  }

  const denialCount = parseInt(await AsyncStorage.getItem('notif_denial_count') ?? '0');

  const result = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
    {
      title: 'Enable payment alerts',
      message: 'FairBridge needs notification permission to alert you when expenses need approval or payments are processed.',
      buttonPositive: 'Enable Notifications',
      buttonNegative: 'Not now',
    }
  );

  if (result === PermissionsAndroid.RESULTS.GRANTED) {
    await AsyncStorage.removeItem('notif_denial_count');
    return 'granted';
  }

  if (result === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN || denialCount >= 1) {
    // Permanent deny — link to app settings
    return 'permanent_deny';
  }

  // First denial — can still re-ask
  await AsyncStorage.setItem('notif_denial_count', String(denialCount + 1));
  return 'denied';
}

function openAppNotificationSettings() {
  Linking.openSettings(); // Opens ACTION_APPLICATION_DETAILS_SETTINGS for this app
}
```

**UX gate**: On `permanent_deny`, show a banner with "Open Settings" button that calls `openAppNotificationSettings()`. Do not block onboarding permanently — show a "Continue without notifications" secondary button after permanent deny, per UX spec Screen 8.3.

### 13.4 OEM Battery Exemption — Samsung and Huawei/Honor (Flow 9)

Section 3.2 already covers Xiaomi MIUI/HyperOS. Additional OEM-specific handling per UX Flow 9:

```kotlin
fun getOemBatterySettingsIntent(context: Context): Intent? {
    val manufacturer = Build.MANUFACTURER.lowercase()
    val pkg = context.packageName

    return when {
        manufacturer == "samsung" -> {
            // Samsung One UI: Settings > Apps > [App] > Battery > Unrestricted
            // Also prompt user to check "Allow background activity" in Samsung's app battery settings
            Intent().apply {
                component = ComponentName(
                    "com.samsung.android.lool",
                    "com.samsung.android.sm.ui.battery.BatteryActivity"
                )
            }.takeIf { it.resolveActivity(context.packageManager) != null }
        }
        manufacturer.contains("huawei") || manufacturer.contains("honor") -> {
            // Huawei/Honor EMUI: Protected Apps setting
            Intent().apply {
                component = ComponentName(
                    "com.huawei.systemmanager",
                    "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"
                )
            }.takeIf { it.resolveActivity(context.packageManager) != null }
        }
        else -> null // Fall back to standard ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
    }
}
```

**Fallback for unrecognized OEMs**: Show generic message with link to `https://dontkillmyapp.com` (as specified in UX Flow 9). Open via `Linking.openURL('https://dontkillmyapp.com')`.

**Prompt sequence per UX Flow 9 / Screen 9.1**:
1. Show in-app explanation screen with OEM-specific copy (detect manufacturer)
2. User taps "Allow" → launch OEM intent (or standard exemption intent)
3. User returns from settings → check `isIgnoringBatteryOptimizations()` again
4. If still not exempted → show "Notifications may be delayed" warning card (non-blocking)

### 13.5 DV Safety — Quick Exit (Screen 7.4)

The Quick Exit button on Screen 7.4 must:
1. Immediately leave FairBridge and show a neutral app (e.g., open weather/maps)
2. Clear FairBridge from the Recents list so an observer cannot return to it via the task switcher

```kotlin
// android/app/src/main/java/com/fairbridge/QuickExitModule.kt
@ReactMethod
fun quickExit() {
    val activity = currentActivity ?: return
    activity.runOnUiThread {
        // 1. Remove from Recents (API 21+)
        activity.finishAndRemoveTask()

        // 2. Open a neutral app (Google Maps or default home) — looks like normal phone use
        val intent = Intent(Intent.ACTION_MAIN).apply {
            addCategory(Intent.CATEGORY_HOME)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        activity.startActivity(intent)
    }
}
```

`finishAndRemoveTask()` is preferred over `moveTaskToBack(true)` — it removes the app from Recents entirely rather than just moving it behind other apps. This is the correct DV safety behavior: an abuser checking Recents will not see FairBridge.

### 13.6 Accessibility Requirements

Per UX spec accessibility section:

**Touch target size**: All interactive elements must be ≥ 48×48dp. In React Native:
```typescript
// Enforce minimum touch target via hitSlop on small elements
<TouchableOpacity hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }} style={{ width: 32, height: 32 }}>
```

**TalkBack labels on currency amounts**: All `Text` components displaying monetary values must have explicit `accessibilityLabel` that spells out the amount naturally:
```typescript
<Text
  accessibilityLabel={`${amount} dollars`}
  accessible={true}
>
  {formatCurrency(amount)}
</Text>
```

**Font scaling**: Do not use `allowFontScaling={false}` anywhere. All text must respect the user's system font size setting. Use `sp` units (React Native's default for `fontSize`) — never `dp` for font sizes.

**FLAG_SECURE and TalkBack**: There is a known conflict on some OEM skins where `FLAG_SECURE` + TalkBack causes content to be inaccessible to screen readers. If this is detected in testing, the mitigation is to use `importantForAccessibility="no-hide-descendants"` on the secure container and provide an alternative accessible description via a visually-hidden element. Document in Known Limitations if encountered.

---

*Spec version: 1.2 | Date: 2026-03-18 | Author: android-dev*
