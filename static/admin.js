import { API_BASE } from "./messenger-config.js";
import { authSecret } from "./messenger-crypto.js";
const $ = (id) => document.getElementById(id);
const make = (tag, text, cls) => {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
};
let token = null,
  generation = 0,
  page = 1,
  messagePage = 1,
  query = "",
  pending = null,
  busy = false,
  loadRevision = 0;
const labels = {
  suspend: "Suspend account",
  restore: "Restore account",
  "revoke-sessions": "Sign out all devices",
  "delete-message": "Delete message",
  "delete-all-messages": "Delete all messages",
  "delete-other-accounts": "Remove other accounts and messages",
};
const explanations = {
  suspend:
    "Stops sign-in, new messages and push alerts. Conversation history is kept. You can restore access later.",
  restore:
    "Allows this account to sign in again. Old sessions stay signed out. Push alerts can resume after a new sign-in on an opted-in device.",
  "revoke-sessions":
    "Ends every login session and stops push alerts for this account. The person can sign in again.",
};
function status(text, error = false) {
  $("status").textContent = text;
  $("status").dataset.error = String(error);
  $("status").setAttribute("role", error ? "alert" : "status");
}
function reset() {
  token = null;
  generation++;
  loadRevision++;
  $("admin-workspace").hidden = true;
  $("admin-login").hidden = false;
  $("accounts").replaceChildren();
  $("audit").replaceChildren();
  $("summary").replaceChildren();
  $("messages").replaceChildren();
  $("password").value = "";
  pending = null;
  if ($("action-dialog").open) $("action-dialog").close();
}
const errors = {
  invalid_credentials: "Username or password is incorrect.",
  admin_required: "This account does not have administrator access.",
  unauthorized: "Your session ended. Sign in again.",
  account_suspended: "This account is suspended.",
  rate_limited: "Too many requests. Wait a moment and retry.",
  protected_admin: "Administrator accounts are protected.",
  confirmation_mismatch: "The username does not match. Check it and retry.",
  reason_required: "Enter a reason of 3–240 characters.",
};
async function api(path, body, credential = token) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(API_BASE + path, {
      method: body === undefined ? "GET" : "POST",
      credentials: "omit",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(credential ? { Authorization: "Bearer " + credential } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      if (
        (response.status === 401 || data.error === "admin_required") &&
        credential &&
        credential === token
      )
        reset();
      throw new Error(errors[data.error] || "Request failed. Please retry.");
    }
    return data;
  } catch (e) {
    if (e instanceof TypeError)
      throw new Error(
        "Could not reach the server. Check your connection and retry.",
      );
    if (e.name === "AbortError")
      throw new Error(
        "The server took too long. Refresh to check whether the action completed.",
      );
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
const date = (value) =>
  value ? new Date(value * 1000).toLocaleString() : "Unavailable";
function accounts(data) {
  $("accounts").replaceChildren();
  $("empty").hidden = data.accounts.length > 0;
  $("account-count").textContent =
    `${data.total} matching account${data.total === 1 ? "" : "s"}`;
  $("page-label").textContent =
    `Page ${data.page} of ${Math.max(1, Math.ceil(data.total / data.pageSize))}`;
  $("previous").disabled = page === 1;
  $("next").disabled = page * data.pageSize >= data.total;
  $("summary").replaceChildren(
    ...Object.entries({
      Accounts: data.summary.accounts,
      Suspended: data.summary.suspended,
      "Active sessions": data.summary.sessions,
      Messages: data.summary.messages,
    }).map(([label, value]) => {
      const box = make("div");
      box.append(make("dt", label), make("dd", String(value)));
      return box;
    }),
  );
  for (const a of data.accounts) {
    const li = make("li"),
      details = make("div"),
      heading = make("div", undefined, "account-heading"),
      badge = make(
        "span",
        a.suspended ? "Suspended" : "Active",
        "account-state",
      );
    badge.dataset.suspended = String(!!a.suspended);
    heading.append(make("h3", a.username), badge);
    if (a.isAdmin)
      heading.append(make("span", "Administrator", "account-state"));
    details.append(heading);
    const counts = make("p", undefined, "account-meta");
    for (const text of [
      `ID ${a.id}`,
      `${a.sessions} sessions`,
      `${a.devices} push devices`,
      `${a.conversations} conversations`,
      `${a.messages} sent`,
    ])
      counts.append(make("span", text));
    details.append(
      counts,
      make(
        "p",
        `Created: ${date(a.created)} · Last sign-in: ${date(a.last_login)}`,
        "admin-muted",
      ),
    );
    li.append(details);
    if (!a.isAdmin) {
      const actions = make("div", undefined, "account-actions");
      for (const action of [
        a.suspended ? "restore" : "suspend",
        "revoke-sessions",
      ]) {
        const button = make("button", labels[action], "secondary");
        button.type = "button";
        button.setAttribute("aria-label", `${labels[action]}: ${a.username}`);
        button.onclick = () => {
          pending = { account: a, action, trigger: button };
          $("action-title").textContent = `${labels[action]}: ${a.username}`;
          $("action-description").textContent = explanations[action];
          $("confirmation-label").textContent =
            "Type the account’s exact username";
          $("confirm-action").textContent = "Confirm";
          $("confirm-action").classList.remove("danger");
          $("confirmation").value = "";
          $("reason").value = "";
          $("action-error").textContent = "";
          $("action-dialog").showModal();
          $("confirmation").focus();
        };
        actions.append(button);
      }
      li.append(actions);
    } else li.append(make("p", "Protected account", "admin-muted"));
    $("accounts").append(li);
  }
}
function openDeletion(message, trigger) {
  const all = !message;
  const action = all ? "delete-all-messages" : "delete-message";
  const confirmation = all ? "DELETE ALL MESSAGES" : String(message.id);
  pending = {
    action,
    account: { username: confirmation },
    trigger,
    path: all
      ? "/api/admin/messages/delete-all"
      : `/api/admin/messages/${message.id}/delete`,
  };
  $("action-title").textContent = all
    ? "Delete all stored messages?"
    : `Delete message #${message.id}?`;
  $("action-description").textContent =
    (all
      ? "Every stored message"
      : `Message #${message.id} from ${message.sender} to ${message.recipient}`) +
    " will be permanently removed from the server for both people. Accounts stay. Already downloaded copies and delivered notifications cannot be recalled. This cannot be undone.";
  $("confirmation-label").textContent = all
    ? "Type DELETE ALL MESSAGES to confirm"
    : `Type ${message.id} to confirm`;
  $("confirmation").value = "";
  $("reason").value = "";
  $("action-error").textContent = "";
  $("confirm-action").textContent = all
    ? "Delete all messages"
    : "Delete message";
  $("confirm-action").classList.add("danger");
  $("action-dialog").showModal();
  $("confirmation").focus();
}
function messages(data) {
  $("messages").replaceChildren();
  $("messages-empty").hidden = data.messages.length > 0;
  $("message-count").textContent =
    `${data.total} stored message${data.total === 1 ? "" : "s"}`;
  $("delete-all-messages").disabled = data.total === 0;
  $("messages-previous").disabled = messagePage === 1;
  $("messages-next").disabled = messagePage * data.pageSize >= data.total;
  $("messages-page").textContent =
    `Page ${messagePage} of ${Math.max(1, Math.ceil(data.total / data.pageSize))}`;
  for (const m of data.messages) {
    const row = make("li"),
      detail = make("div");
    detail.append(
      make("h3", `Message #${m.id}`),
      make("p", `${m.sender} → ${m.recipient}`, "admin-muted"),
      make("p", date(m.created), "admin-muted"),
    );
    const button = make("button", "Delete message", "secondary danger");
    button.type = "button";
    button.setAttribute("aria-label", `Delete message #${m.id}`);
    button.onclick = () => openDeletion(m, button);
    row.append(detail, button);
    $("messages").append(row);
  }
}
async function load() {
  const e = generation;
  const request = ++loadRevision;
  status("Loading accounts…");
  $("refresh").disabled = true;
  try {
    const [data, audit, messageData] = await Promise.all([
      api(`/api/admin/accounts?q=${encodeURIComponent(query)}&page=${page}`),
      api("/api/admin/audit"),
      api(`/api/admin/messages?page=${messagePage}`),
    ]);
    if (e !== generation || request !== loadRevision) return;
    accounts(data);
    messages(messageData);
    $("audit").replaceChildren();
    if (!audit.events.length)
      $("audit").append(make("li", "No admin actions yet."));
    for (const event of audit.events) {
      const item = make("li");
      item.append(
        make(
          "strong",
          `${event.actor} → ${event.target}: ${labels[event.action] || event.action}`,
        ),
        make("p", event.reason),
        make("p", date(event.created), "admin-muted"),
      );
      $("audit").append(item);
    }
    status("Accounts up to date.");
  } catch (error) {
    if (e === generation && request === loadRevision)
      status(error.message, true);
  } finally {
    if (request === loadRevision) $("refresh").disabled = false;
  }
}
$("login-form").onsubmit = async (event) => {
  event.preventDefault();
  if (busy) return;
  busy = true;
  $("login-submit").disabled = true;
  status("Signing in…");
  const e = generation;
  let issued = null;
  try {
    const username = $("username").value.trim().toLowerCase();
    const password = $("password").value;
    $("password").value = "";
    const secret = await authSecret(password, username);
    const login = await api("/api/login", { username, password: secret }, null);
    issued = login.token;
    await api("/api/admin/me", undefined, issued);
    if (e !== generation) {
      await api("/api/logout", {}, issued);
      return;
    }
    token = issued;
    issued = null;
    $("admin-identity").textContent = `Signed in as ${username}`;
    $("admin-login").hidden = true;
    $("admin-workspace").hidden = false;
    page = 1;
    messagePage = 1;
    query = "";
    $("search").value = "";
    await load();
    $("search").focus();
  } catch (e) {
    if (issued) await api("/api/logout", {}, issued).catch(() => {});
    status(e.message, true);
  } finally {
    busy = false;
    $("login-submit").disabled = false;
  }
};
$("show-password").onclick = () => {
  const show = $("password").type === "password";
  $("password").type = show ? "text" : "password";
  $("show-password").textContent = show ? "Hide" : "Show";
  $("show-password").setAttribute(
    "aria-label",
    show ? "Hide password" : "Show password",
  );
  $("show-password").setAttribute("aria-pressed", String(show));
};
$("sign-out").onclick = async () => {
  if (busy) return;
  const old = token;
  reset();
  status("Signing out…");
  try {
    await api("/api/logout", {}, old);
    status("Signed out.");
  } catch {
    status(
      "Local session cleared. Server sign-out could not be confirmed; the session will expire.",
      true,
    );
  }
};
$("search-form").onsubmit = (event) => {
  event.preventDefault();
  if (busy) return;
  query = $("search").value.trim().toLowerCase();
  page = 1;
  load();
};
$("refresh").onclick = () => load();
$("delete-all-messages").onclick = () =>
  openDeletion(null, $("delete-all-messages"));
$("messages-previous").onclick = () => {
  messagePage--;
  load();
};
$("messages-next").onclick = () => {
  messagePage++;
  load();
};
$("previous").onclick = () => {
  page--;
  load();
};
$("next").onclick = () => {
  page++;
  load();
};
$("cancel-action").onclick = () => {
  if (!busy) $("action-dialog").close();
};
$("action-dialog").addEventListener("cancel", (event) => {
  if (busy) event.preventDefault();
});
$("action-dialog").addEventListener("close", () => {
  pending?.trigger?.focus();
  pending = null;
});
$("action-form").onsubmit = async (event) => {
  event.preventDefault();
  if (busy || !pending) return;
  const { account, action, path } = pending;
  if ($("confirmation").value !== account.username) {
    $("action-error").textContent = path
      ? "Type the exact confirmation text shown above."
      : "Type the exact username to confirm.";
    return;
  }
  busy = true;
  $("confirm-action").disabled = true;
  $("cancel-action").disabled = true;
  try {
    const result = await api(
      path || `/api/admin/accounts/${account.id}/${action}`,
      {
        [path ? "confirmation" : "username"]: $("confirmation").value,
        reason: $("reason").value.trim(),
      },
    );
    $("action-dialog").close();
    if (path) messagePage = 1;
    await load();
    status(
      path
        ? `Deleted ${result.deleted.messages} message${result.deleted.messages === 1 ? "" : "s"}.`
        : `${labels[action]} completed for ${account.username}.`,
    );
  } catch (e) {
    $("action-error").textContent = e.message;
    if (!$("action-dialog").open) status(e.message, true);
  } finally {
    busy = false;
    $("confirm-action").disabled = false;
    $("cancel-action").disabled = false;
  }
};
