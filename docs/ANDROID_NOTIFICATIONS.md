# Android message notifications

## Current implementation

Android uses the official Capacitor Push Notifications 8.1.3 plugin and Firebase
Cloud Messaging HTTP v1. Azure remains the message store/API. FCM is a no-cost
transport; no paid Azure plan, Notification Hub, database or SMS API is added.
References: [Capacitor setup](https://capacitorjs.com/docs/apis/push-notifications),
[Firebase Android setup](https://firebase.google.com/docs/cloud-messaging/android/get-started),
[server authentication](https://firebase.google.com/docs/cloud-messaging/send/v1-api),
[FCM pricing](https://firebase.google.com/pricing).

Activated and tested on November 24, 2026. The configured test APK is installed
on the connected Pixel 10 Pro XL. The API and static frontend were deployed to
the existing Azure services. These source changes remain on the local feature
branch until committed and merged; deployment does not imply a main-branch push.

## User behavior

After signing in, Android users can choose Enable notifications. Android 13+
asks for notification permission; denial has an Android Settings route. Opt-in
persists on that installation. Turning notifications off unregisters it and
clears delivered notifications. Explicit sign-out also revokes that session's
server bindings and deletes the local FCM token. Merely closing the app does
not sign the user out of push delivery: the OS can show a generic alert without
running the WebView or possessing message-decryption keys.

The alert says only “CipherCraft — You have a new encrypted message.” Its data
contains conversation, recipient and message IDs. No message body, classical
ciphertext, hint, solution, sender name, authentication secret or encryption key
is sent to FCM. Android shows no sensitive lock-screen preview. A tap opens
Messages and routes to that conversation after signing into the right account;
unlocked message keys and API login sessions still are not persisted. Tapping
an alert cannot silently switch to another account or discard a current draft.

Normal app dismissal/backgrounding is supported by FCM. Android Settings Force
stop, disabled notification permission, locked Android Private Space or vendor
battery restrictions can prevent alerts until the user reopens/unlocks the app.
Do not claim that a force-stopped app can always receive notifications. A real
closed-app test must use normal dismissal/process death, not adb force-stop.

## Backend and privacy

Authenticated push status/register/unregister routes bind a token to a random
installation UUID and the current account/session. Tokens cannot be taken over
by a different installation identifier. Session validity is checked inside the
registration transaction, preventing a late registration from resurrecting a
logged-out session. Device bindings expire after 30 days unless refreshed by a
new sign-in/registration. Up to five devices per account are supported.

Device-routing tokens are stored on Azure because FCM needs their raw value;
installation IDs and session tokens are hashed. No routing token or credential
is logged. A durable SQLite outbox is written atomically with a new message;
idempotent retries do not create a duplicate alert. Pending alerts coalesce per
conversation/device. Read, blocked, signed-out and expired targets are skipped.
Retry is bounded to five attempts and one day, with backoff; UNREGISTERED tokens
are removed. Network calls occur after commit and outside database write locks.
A daemon worker wakes on requests/new messages. F1 is still a sleeping/free beta
server, not an always-on SLA; pending retry timing depends on its availability.
Message sending succeeds even when notification delivery fails.

## Owner setup and maintenance

1. Sign in to Firebase with the owner's Google account. Create/select a project
   on the no-cost Spark plan and register Android package
   `io.drewclark.ciphercraft.beta`. Do not enable Analytics or paid services.
2. Download `google-services.json` to `mobile/android/app/google-services.json`.
   It is ignored in Git. It contains client project configuration, not the
   server credential, but still should be handled deliberately.
3. Configure a least-privileged service account permitted to send FCM messages.
   Keep its JSON/private key out of chat, Git, artifacts and the APK. Credential
   creation/grants and any Terms acceptance require the owner's explicit action
   or the applicable confirmation. The account's token_uri must be Google's
   official OAuth endpoint.
4. Store that JSON in Azure app setting `CIPHER_FCM_SERVICE_ACCOUNT`. Locally,
   `CIPHER_FCM_CREDENTIALS_FILE` may point to an ignored local JSON file. Never
   print the credential or put it in workflow YAML. Install the updated backend
   requirements and deploy the allowlisted API ZIP. The frontend must also be
   deployed before an installed new APK can use the new routes on Azure.
5. Rebuild/install the configured APK, sign in and enable notifications. Deliver
   a message from a separate website account while the app is normally closed;
   verify the actual Android alert, tap it, sign in and open/decode the correct
   conversation. Check sign-out, denial, blocking and token refresh behavior.

Without configuration the app still compiles and its existing tools/messenger
remain usable; the notification control truthfully reports setup is incomplete.
The development preview APK is not a completed notification-enabled release.

## Checks so far

- All 232 Python tests pass, including 13 notification tests for authenticated
  binding, registration limits, token ownership, same-phone account switches,
  logout/unregister, read/block suppression, durable retries/coalescing, device
  expiry, expired in-memory login sessions, private payloads and provider errors.
- Push component browser tests pass for opt-in, token rotation, disable,
  permission denial/settings, missing setup, sign-out during registration and
  account-specific tap routing at 320/390/768/1440px.
- The configured Android APK compiles with the official push plugin. Its SHA256
  is `1f9f18cc837c31d055b102c7a316ebc714be9b51bca8535e9c2246856b788313`.
- Real FCM registration passed after the Android notification permission prompt.
  Home followed by `am kill` stopped the app process (confirmed with `pidof`);
  no force-stop was used. A new Caesar challenge sent through
  `https://cipher.drewclark.io/` produced an Android notification with importance
  4, channel `ciphercraft_messages`, PRIVATE visibility, and only the generic
  title/body. The notification was verified in Android's notification records
  and visible notification-shade UI.
- Tapping the cold-start alert opened Messages. After login, the intended
  conversation opened automatically; both shift-7 decoding and the local AI
  recovered the sent message on the physical phone.
- Firebase project `ciphercraft-notifications` visibly reports Spark,
  no-cost ($0/month). Azure plan `asp-ciphercraft-free` reports F1 / Free.
  The dedicated `ciphercraft-push-sender` service account has the FCM API Admin
  role, with its credential in the Azure `CIPHER_FCM_SERVICE_ACCOUNT` setting.
  No billing activation or paid resources were added. Client configuration and
  the local credential are Git-ignored and excluded from deployment packages.

Review priorities: longer locked-phone/Doze and battery-restriction tests, large
text and screen-reader checks, and additional Android devices. The verified
closed-process test does not establish all-day delivery reliability or override
Android's explicit force-stop behavior.
