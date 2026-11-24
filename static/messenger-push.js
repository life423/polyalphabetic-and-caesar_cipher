// Android alerts contain routing IDs only. Authentication and message keys stay in memory.
const native = window.Capacitor?.isNativePlatform();
const bridge = native ? window.Capacitor.Plugins.CipherPush : null;
const push = native ? window.Capacitor.Plugins.PushNotifications : null;
const $ = (id) => document.getElementById("chat-notification-" + id);
let initialized,
  openApp,
  context = null,
  generation = 0,
  pending = null,
  waiter = null;
function report(message) {
  if ($("status")) $("status").textContent = message;
}
function valid(data) {
  return (
    data &&
    ["conversationId", "recipientId", "messageId"].every((key) =>
      /^[1-9][0-9]{0,17}$/.test(String(data[key] || "")),
    )
  );
}
function opened(data) {
  if (!valid(data)) return;
  pending = {
    conversationId: String(data.conversationId),
    recipientId: String(data.recipientId),
    messageId: String(data.messageId),
  };
  openApp?.();
  if (context)
    Promise.resolve(context.onOpen?.(pending)).catch(() =>
      report("Open Messages to view the new message."),
    );
}
export function takePushMessage(userId) {
  if (!pending || pending.recipientId !== String(userId)) return null;
  const value = pending;
  pending = null;
  return value;
}
export function initializePush(onOpen) {
  if (onOpen) openApp = onOpen;
  if (!bridge || !push) return Promise.resolve();
  if (initialized) return initialized;
  initialized = (async () => {
    await bridge.addListener("messageNotificationOpened", opened);
    await push.addListener("registration", ({ value }) => {
      if (typeof value !== "string") return;
      if (waiter) waiter.resolve(value);
      else if (context?.enabled && context.token !== value) {
        const owner = context;
        bind(owner, value).catch(() => {
          if (context === owner)
            report("Notification registration needs a retry.");
        });
      }
    });
    await push.addListener("registrationError", () =>
      waiter?.reject(
        new Error(
          "Could not register this phone for notifications. Please retry.",
        ),
      ),
    );
    await push.addListener("pushNotificationReceived", () =>
      context?.onReceived?.(),
    );
    opened(await bridge.takeLaunchNotification());
  })();
  initialized.catch(() => {
    initialized = null;
    report("Notification setup could not load. Reopen Messages to retry.");
  });
  return initialized;
}
async function bind(owner, token) {
  if (context !== owner) return;
  await owner.api("/api/push/register", {
    token,
    installationId: owner.installationId,
  });
  if (context !== owner) return;
  owner.token = token;
  owner.enabled = true;
  owner.wanted = true;
  await bridge.setEnabled({ enabled: true });
}
function draw(owner, text) {
  if (context !== owner) return;
  $("enable").hidden = owner.enabled;
  $("disable").hidden = !owner.enabled && !owner.wanted;
  $("settings").hidden = !owner.settings;
  report(text);
}
async function register(owner, ask) {
  const state = await bridge.getStatus();
  if (context !== owner) return;
  owner.installationId = state.installationId;
  if (!state.configured)
    throw new Error("Notifications need the one-time Firebase app setup.");
  if (!(await owner.api("/api/push/status")).configured)
    throw new Error(
      "Notification delivery is not configured on the server yet.",
    );
  let permission = await push.checkPermissions();
  if (ask && permission.receive !== "granted")
    permission = await push.requestPermissions();
  if (context !== owner) return;
  if (
    permission.receive !== "granted" ||
    !(await bridge.getStatus()).notificationsEnabled
  ) {
    owner.settings = permission.receive === "denied";
    throw new Error(
      owner.settings
        ? "Android notifications are blocked. Enable them in Settings."
        : "Allow notifications to receive message alerts.",
    );
  }
  await push.createChannel({
    id: "ciphercraft_messages",
    name: "Messages",
    description: "New encrypted messages",
    importance: 4,
    visibility: 0,
  });
  let timer;
  const token = new Promise((resolve, reject) => {
    waiter = { resolve, reject };
    timer = setTimeout(
      () =>
        reject(new Error("Notification registration timed out. Please retry.")),
      30000,
    );
  });
  // Attach a rejection handler immediately, including when native register fails first.
  token.catch(() => {});
  try {
    await push.register();
    const value = await token;
    if (context !== owner) return;
    await bind(owner, value);
    if (context !== owner) return;
    owner.settings = false;
    draw(
      owner,
      "Notifications are on. New messages can alert you while the app is closed.",
    );
  } finally {
    clearTimeout(timer);
    waiter = null;
  }
}
async function enable(owner, ask) {
  if (context !== owner || owner.busy) return;
  owner.busy = true;
  $("enable").disabled = $("disable").disabled = true;
  report("Setting up message notifications…");
  try {
    await register(owner, ask);
  } catch (error) {
    if (context === owner) {
      owner.enabled = false;
      draw(owner, error.message);
    }
  } finally {
    if (context === owner) {
      owner.busy = false;
      $("enable").disabled = $("disable").disabled = false;
    }
  }
}
export async function setPushSession(options) {
  if (!bridge || !push) return;
  const version = ++generation;
  await initializePush();
  if (version !== generation) return;
  const owner = { ...options, enabled: false, settings: false, busy: false };
  context = owner;
  document.getElementById("chat-notifications").hidden = false;
  const state = await bridge.getStatus();
  if (context !== owner) return;
  owner.installationId = state.installationId;
  owner.configured = state.configured;
  owner.wanted = state.enabled;
  $("enable").onclick = () => enable(owner, true);
  $("disable").onclick = async () => {
    if (context !== owner || owner.busy) return;
    owner.busy = true;
    $("disable").disabled = true;
    try {
      await owner.api("/api/push/unregister", {
        installationId: owner.installationId,
      });
      await bridge.setEnabled({ enabled: false });
      if (owner.configured) await push.unregister();
      await push.removeAllDeliveredNotifications();
      if (context === owner) {
        owner.enabled = false;
        owner.wanted = false;
        draw(owner, "Message notifications are off for this phone.");
      }
    } catch {
      if (context === owner)
        report(
          "Could not turn off delivery. Please retry or turn off notifications in Android Settings.",
        );
    } finally {
      if (context === owner) {
        owner.busy = false;
        $("disable").disabled = false;
      }
    }
  };
  $("settings").onclick = () => bridge.openSettings();
  if (!state.configured) {
    $("enable").disabled = true;
    draw(owner, "Notifications need the one-time Firebase app setup.");
  } else if (state.enabled) await enable(owner, false);
  else draw(owner, "Receive message alerts even when CipherCraft is closed.");
  if (pending && context === owner)
    Promise.resolve(owner.onOpen?.(pending)).catch(() =>
      report("Open Messages to view the new message."),
    );
}
export function clearPushSession() {
  ++generation;
  const owner = context;
  context = null;
  if (waiter) waiter.reject(new Error("Notification registration cancelled."));
  document.getElementById("chat-notifications").hidden = true;
  report("");
  if (bridge) bridge.setEnabled({ enabled: false }).catch(() => {});
  if (push && owner?.configured) {
    push.unregister().catch(() => {});
    push.removeAllDeliveredNotifications().catch(() => {});
  }
}
