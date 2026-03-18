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
        "channel_id": "payments",
        "notification_priority": "PRIORITY_HIGH",
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

### 2.2 Notification Channels

Notification channels must be created before the first notification is displayed. FairBridge creates three channels at app startup in `MainApplication.onCreate()` via a native module.

| Channel ID | Display Name | Importance | Use Case |
|---|---|---|---|
| `payments` | Payment Alerts | `IMPORTANCE_HIGH` | Payment initiated, succeeded, failed, dispute |
| `expenses` | Expense Updates | `IMPORTANCE_DEFAULT` | New expense submitted, confirmed, disputed |
| `calendar` | Schedule Reminders | `IMPORTANCE_LOW` | Custody handoff reminders, calendar sync |

```kotlin
// android/app/src/main/java/com/fairbridge/NotificationChannelModule.kt
class NotificationChannelModule(private val context: Context) {

    fun createChannels() {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val paymentsChannel = NotificationChannel(
            "payments",
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
            "expenses",
            "Expense Updates",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Notifications for co-parent expense submissions and confirmations"
            lockscreenVisibility = Notification.VISIBILITY_PRIVATE
        }

        val calendarChannel = NotificationChannel(
            "calendar",
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
        "channel_id": "expenses",
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

### 7.4 Boot Receiver

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
| Push notifications | FCM high-priority + channels | APNs + time-sensitive |
| Credential storage | Android Keystore / EncryptedSharedPreferences | Keychain (kSecAttrAccessibleWhenUnlockedThisDeviceOnly) |
| Screen protection | FLAG_SECURE | Screen content masking in app switcher |
| Camera | CameraX via react-native-vision-camera | Same library (VisionCamera abstracts CameraX / AVFoundation) |
| Receipt selection | Activity picker (any file/photo app) | PHPickerViewController (no full library permission) |
| Calendar export | CalendarContract (device-native) | EventKit (.ics export) |
| Background sync | WorkManager (15-min periodic) | Background App Refresh (discretionary, OS-controlled) |
| Battery/background | REQUEST_IGNORE_BATTERY_OPTIMIZATIONS | No equivalent — APNs handles wakeup |
| Notification permission | Runtime (Android 13+ / API 33+) | Must request at runtime (iOS 10+) |
| Notification batching | FCM collapse keys | APNs collapse ID |
| Minimum OS | Android 7.0 (API 24) | iOS 16.0 |
| Financial screen protection | FLAG_SECURE (prevents screenshots) | UIScreen.isCaptured check + overlay |

**Key parity gap**: iOS has no equivalent to `FLAG_SECURE`. The iOS spec must implement an explicit content-masking overlay when `UIScreen.isCaptured` is true, or use `UITextField.isSecureTextEntry` for sensitive fields.

**WorkManager vs Background App Refresh**: Android's WorkManager provides guaranteed execution (will run when constraints met). iOS Background App Refresh is discretionary — the OS decides when to run it based on usage patterns. For FairBridge, FCM/APNs push is the authoritative delivery mechanism on both platforms; background sync is a belt-and-suspenders fallback.

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
    BatteryOptimizationPackage(),    // Battery exemption prompt
    SecureScreenPackage(),           // FLAG_SECURE management
    CalendarPackage(),               // CalendarContract export
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

*Spec version: 1.0 | Date: 2026-03-17 | Author: android-dev*
