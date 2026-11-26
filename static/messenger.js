import {
  setPushSession,
  clearPushSession,
  takePushMessage,
} from "./messenger-push.js";
import { sha256 } from "./sha256.js";
import { API_BASE } from "./messenger-config.js";
import {
  authSecret,
  createIdentity,
  unlockIdentity,
  encryptChat,
  decryptChat,
  fingerprint,
} from "./messenger-crypto.js";
import { requestCipher } from "./app.js";
const $ = (id) => document.getElementById(`chat-${id}`);
const make = (tag, text, cls) => {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
};
const decryptedPayloads = new Set();
const ciphers = ["Caesar", "Vigenère", "Rail Fence", "Affine"];
let started = false,
  session = null,
  epoch = 0,
  view = 0,
  current = null,
  inbox = [],
  pending = null,
  revision = 0,
  sending = false,
  trusted = false,
  timer = null,
  refreshing = false,
  loading = null,
  seen = new Set(),
  cursor = null;
const visible = () =>
  !document.hidden &&
  !!document.getElementById("messages-panel")?.getClientRects().length &&
  !!document.getElementById("messenger-app")?.getClientRects().length;
const alive = (e, v) =>
  !!session && epoch === e && (v === undefined || view === v);
const keyJSON = (key) => JSON.stringify(key);
function notice(text = "", error = false) {
  $("status").textContent = text;
  $("status").dataset.error = String(error);
  $("status").setAttribute("role", error ? "alert" : "status");
  $("refresh").hidden = !error || !session;
}
function reason(e) {
  return navigator.onLine
    ? e.message || "Request failed. Please retry."
    : "You’re offline. Reconnect and retry.";
}
async function api(path, body, token = session?.token) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const r = await fetch(`${String(API_BASE).replace(/\/$/, "")}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const errors = {
        invalid_credentials: "Username or password is incorrect.",
        account_suspended:
          "This account is suspended. Contact the app administrator.",
        account_unavailable: "This account is unavailable for new messages.",
        message_deleted:
          "This message was deleted by an administrator and cannot be resent. Start a new message instead.",
        username_taken: "That username is already taken. Choose another.",
        unauthorized:
          "Your session has expired. Copy any draft you want to keep, then sign out and log in again.",
        rate_limited: "Too many requests. Wait a moment, then retry.",
        not_found:
          "That account or conversation could not be found. Check the exact username.",
        blocked: "This conversation is blocked. Unblock it before sending.",
        invalid_username: "Use 3–24 lowercase letters, numbers or underscores.",
        invalid_password: "Use a password of 12–128 characters.",
        invalid_request: "Check your entries and try again.",
      };
      throw new Error(
        r.status === 401 && token
          ? errors.unauthorized
          : errors[data.error] ||
            "The request could not be completed. Please retry.",
      );
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "The connection took too long. Your draft stays here; please retry.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
function fields(target, cipher) {
  target.replaceChildren();
  for (const name of cipher === "Affine" ? ["a", "b"] : ["key"]) {
    const l = make(
        "label",
        cipher === "Affine"
          ? `Key ${name}`
          : cipher === "Rail Fence"
            ? "Rails"
            : "Key",
      ),
      i = make("input");
    i.type = cipher === "Vigenère" ? "text" : "number";
    i.autocomplete = "off";
    i.required = true;
    if (cipher === "Rail Fence") i.min = "2";
    l.append(i);
    target.append(l);
  }
}
function readKey(target, cipher) {
  const a = [...target.querySelectorAll("input")].map((i) => i.value);
  return cipher === "Affine" ? a : a[0];
}
function mode() {
  const challenge = $("kind").value === "challenge";
  for (const id of ["cipher-label", "key-fields", "challenge-options"])
    $(id).hidden = !challenge;
  fields($("key-fields"), $("cipher").value);
  $("key-fields")
    .querySelectorAll("input")
    .forEach((i) => (i.required = challenge));
  $("cipher-note").hidden = !challenge || $("cipher").value !== "Rail Fence";
  $("send").textContent = challenge ? "Send challenge" : "Send message";
}
function controls() {
  $("send").disabled = sending || !trusted || !!current?.blocked;
  $("block").textContent = current?.blocked ? "Unblock" : "Block";
}
function showPassword(visible) {
  $("password").type = visible ? "text" : "password";
  $("password-toggle").setAttribute("aria-pressed", String(visible));
  $("password-toggle").setAttribute(
    "aria-label",
    visible ? "Hide password" : "Show password",
  );
  $("password-slash").toggleAttribute("hidden", !visible);
}
function reset() {
  clearPushSession();
  showPassword(false);
  document.getElementById("messenger-app").dataset.chatOpen = "false";
  for (const p of decryptedPayloads) {
    p.text = "";
    p.hint = "";
  }
  decryptedPayloads.clear();
  document
    .querySelectorAll("#chat-thread input, #chat-thread textarea")
    .forEach((i) => (i.value = ""));
  $("thread").textContent = "";
  epoch++;
  view++;
  session = null;
  current = null;
  inbox = [];
  pending = null;
  revision++;
  sending = false;
  trusted = false;
  seen.clear();
  cursor = null;
  loading = null;
  clearInterval(timer);
  timer = null;
  for (const id of [
    "thread",
    "conversations",
    "key-fields",
    "own-code",
    "peer-code",
    "peer-name",
  ])
    $(id).replaceChildren();
  for (const id of ["auth-form", "compose", "invite"]) $(id).reset();
  $("auth-form")
    .querySelectorAll("button")
    .forEach((b) => (b.disabled = false));
  $("password").value = "";
  $("account").textContent = "";
  $("account").hidden = true;
  $("block").disabled = false;
  $("send-status").textContent = "";
  $("auth").hidden = false;
  $("workspace").hidden = true;
  $("active").hidden = true;
  $("empty").hidden = false;
  $("signout").hidden = true;
  $("account-settings").hidden = true;
  $("account-settings").open = false;
  document.getElementById("chat-trust-warning")?.remove();
  notice();
  mode();
}
function renderInbox() {
  const focus = document.activeElement?.dataset?.conversation;
  $("conversations").replaceChildren();
  if (!inbox.length)
    $("conversations").append(make("p", "No conversations yet.", "chat-muted"));
  for (const c of inbox) {
    const b = make(
      "button",
      `${c.peer.username}${Number(c.unread) > 0 ? ` · ${c.unread} unread` : ""}${c.blocked ? " · Blocked" : ""}`,
      "chat-conversation",
    );
    b.type = "button";
    b.dataset.conversation = String(c.id);
    b.setAttribute(
      "aria-current",
      String(String(c.id) === String(current?.id)),
    );
    b.onclick = () => void choose(c);
    $("conversations").append(b);
    if (focus === String(c.id)) b.focus({ preventScroll: true });
  }
}
async function choose(c) {
  document.getElementById("messenger-app").dataset.chatOpen = "true";
  const e = epoch,
    v = ++view;
  for (const p of decryptedPayloads) {
    p.text = "";
    p.hint = "";
  }
  decryptedPayloads.clear();
  current = c;
  trusted = false;
  pending = null;
  revision++;
  sending = false;
  cursor = null;
  seen = new Set();
  $("thread").replaceChildren();
  $("compose").reset();
  mode();
  $("send-status").textContent = "";
  $("active").hidden = false;
  $("empty").hidden = true;
  $("peer-name").textContent = c.peer.username;
  $("own-code").textContent = $("peer-code").textContent = "";
  document.getElementById("chat-trust-warning")?.remove();
  controls();
  renderInbox();
  try {
    const [own, peer] = await Promise.all([
      fingerprint(session.user.publicKey),
      fingerprint(c.peer.publicKey),
    ]);
    if (!alive(e, v)) return;
    $("own-code").textContent = own;
    $("peer-code").textContent = peer;
    const k = `messenger-trust:${session.user.username}:${String(c.peer.id)}`;
    let previous;
    try {
      previous = localStorage.getItem(k);
    } catch {
      throw new Error(
        "Key verification storage is unavailable. Enable local storage and retry.",
      );
    }
    const accept = () => {
      localStorage.setItem(k, peer);
      trusted = true;
      document.getElementById("chat-trust-warning")?.remove();
      controls();
    };
    if (previous && previous !== peer) {
      const warning = make("div", undefined, "chat-error");
      warning.id = "chat-trust-warning";
      warning.setAttribute("role", "alert");
      warning.append(
        make(
          "p",
          "Their key changed. Sending and decryption are paused. Compare fingerprints through another trusted channel before accepting.",
        ),
      );
      const b = make("button", "I verified the changed key — accept");
      b.type = "button";
      b.onclick = () => {
        if (!alive(e, v)) return;
        try {
          accept();
          void load().catch((err) => {
            if (alive(e, v)) notice(reason(err), true);
          });
        } catch (err) {
          notice(reason(err), true);
        }
      };
      warning.append(b);
      $("thread").before(warning);
    } else accept();
    if (trusted) await load();
  } catch (err) {
    if (alive(e, v)) notice(reason(err), true);
  }
}
async function load() {
  if (
    !current ||
    !trusted ||
    !visible() ||
    !$("thread").getClientRects().length
  )
    return;
  const e = epoch,
    v = view,
    c = current,
    tag = `${e}:${v}`;
  if (loading === tag) return;
  loading = tag;
  try {
    let after = cursor;
    do {
      const data = await api(
        `/api/conversations/${encodeURIComponent(c.id)}/messages${after ? `?after=${encodeURIComponent(after)}` : ""}`,
      );
      if (!alive(e, v) || !visible() || !trusted) return;
      const messages = data.messages || [];
      for (const m of messages) {
        if (seen.has(String(m.id))) continue;
        let p;
        try {
          p = await decryptChat(
            session.privateKey,
            c.peer.publicKey,
            String(c.id),
            String(m.senderId),
            m.envelope,
          );
        } catch {
          p = {
            kind: "error",
            text: "Unable to decrypt this message. Verify key fingerprints.",
          };
        }
        if (!alive(e, v) || !visible() || !trusted) return;
        if (p && typeof p === "object") decryptedPayloads.add(p);
        renderMessage(m, p, e, v);
        seen.add(String(m.id));
        cursor = m.id;
      }
      if (!messages.length || !data.hasMore || String(after) === String(cursor))
        break;
      after = cursor;
    } while (alive(e, v) && visible());
    if (cursor && alive(e, v) && visible()) {
      await api(`/api/conversations/${encodeURIComponent(c.id)}/read`, {
        messageId: cursor,
      });
      if (alive(e, v)) {
        const item = inbox.find((i) => String(i.id) === String(c.id));
        if (item) item.unread = 0;
        renderInbox();
      }
    }
  } finally {
    if (loading === tag) loading = null;
  }
}
async function refresh() {
  if (!session || !visible() || refreshing) return;
  refreshing = true;
  const e = epoch;
  try {
    const data = await api("/api/conversations");
    if (!alive(e) || !visible()) return;
    inbox = data.conversations || [];
    renderInbox();
    if (current) {
      const next = inbox.find((c) => String(c.id) === String(current.id));
      if (
        next &&
        (keyJSON(next.peer.publicKey) !== keyJSON(current.peer.publicKey) ||
          next.blocked !== current.blocked)
      )
        await choose(next);
      else await load();
    }
    if (alive(e) && visible()) notice();
  } catch (err) {
    if (alive(e) && visible()) notice(reason(err), true);
  } finally {
    refreshing = false;
  }
}
function poll() {
  clearInterval(timer);
  timer = null;
  if (session && visible()) {
    void refresh();
    timer = setInterval(() => void refresh(), 5000);
  }
}
function renderMessage(m, p, e, v) {
  const own = String(m.senderId) === String(session.user.id),
    b = make("article", undefined, `chat-bubble${own ? " chat-own" : ""}`);
  b.append(make("div", own ? "You" : current.peer.username, "chat-muted"));
  if (
    !p ||
    typeof p.text !== "string" ||
    !["challenge", "message", "error"].includes(p.kind)
  )
    p = { kind: "error", text: "Unsupported message format." };
  if (p.kind === "challenge")
    b.append(
      make(
        "strong",
        p.hideCipher
          ? "Cipher challenge · cipher hidden"
          : `Cipher challenge · ${p.cipher}`,
      ),
    );
  b.append(make("p", p.text.slice(0, 5000), "chat-message-text"));
  if (p.kind === "challenge" && typeof p.hint === "string" && p.hint)
    b.append(make("p", `Hint: ${p.hint.slice(0, 160)}`, "chat-muted"));
  const date = new Date(
    typeof m.createdAt === "number" ? m.createdAt * 1000 : m.createdAt,
  );
  if (!isNaN(date)) b.append(make("div", date.toLocaleString(), "chat-muted"));
  if (!own && p.kind === "challenge") decodeControls(b, p, e, v);
  $("thread").append(b);
}
function decodeControls(b, p, e, v) {
  const wrap = make("div", undefined, "chat-stack"),
    label = make("label", "Decode as"),
    select = make("select"),
    keys = make("div", undefined, "chat-fields"),
    actions = make("div", undefined, "chat-actions"),
    decode = make("button", "Decode"),
    ai = make("button", "Try AI"),
    out = make("div", undefined, "chat-result");
  out.setAttribute("role", "status");
  for (const c of ciphers) select.append(make("option", c));
  select.value =
    !p.hideCipher && ciphers.includes(p.cipher) ? p.cipher : "Caesar";
  label.append(select);
  fields(keys, select.value);
  select.onchange = () => {
    fields(keys, select.value);
    invalidate();
  };
  keys.addEventListener("input", () => invalidate());
  function invalidate() {
    op++;
    out.replaceChildren();
    decode.disabled = ai.disabled = false;
  }
  decode.type = ai.type = "button";
  actions.append(decode, ai);
  wrap.append(label, keys, actions, out);
  b.append(wrap);
  let op = 0;
  const work = async (task) => {
    const ticket = ++op;
    decode.disabled = ai.disabled = true;
    out.replaceChildren(make("p", "Working…"));
    try {
      const value = await task();
      const matched =
        typeof value === "string" && p.solutionHash
          ? (await sha256(new TextEncoder().encode(value))) === p.solutionHash
          : null;
      if (!alive(e, v) || !trusted || ticket !== op) return;
      out.replaceChildren();
      if (value instanceof HTMLElement) out.append(value);
      else {
        out.append(
          make(
            "p",
            String(
              value || "No readable result. Try another key or ask for a hint.",
            ),
            "chat-decoded-text",
          ),
        );
        if (matched !== null)
          out.append(
            make(
              "p",
              matched
                ? "You cracked it! This matches the sender’s message."
                : "That key does not match yet. Try another key or ask for a hint.",
              matched ? "chat-solved" : "chat-muted",
            ),
          );
      }
    } catch (err) {
      if (alive(e, v) && ticket === op) out.textContent = reason(err);
    } finally {
      if (alive(e, v) && ticket === op) decode.disabled = ai.disabled = false;
    }
  };
  decode.onclick = () =>
    void work(() =>
      requestCipher("Decrypt", {
        text: p.text,
        cipher: select.value,
        key: readKey(keys, select.value),
        file_mode: false,
      }),
    );
  ai.onclick = () =>
    void work(async () => {
      const r = await requestCipher(p.hideCipher ? "crack" : "analyze", {
        text: p.text,
        cipher: p.hideCipher ? "Auto" : p.cipher,
        key: "",
        file_mode: false,
      });
      const candidates = p.hideCipher ? r?.candidates : r,
        list = make("div", undefined, "chat-stack");
      list.append(
        make(
          "p",
          "AI suggestions are guesses. Short messages may not provide enough evidence.",
        ),
      );
      if (!Array.isArray(candidates) || !candidates.length)
        list.append(
          make(
            "p",
            "No useful suggestion found. Try a manual key or ask for a hint.",
          ),
        );
      else
        for (const candidate of candidates) {
          const row = make("div"),
            button = make("button", "Try this key");
          row.append(
            make(
              "p",
              `${candidate.cipher || p.cipher} · ${candidate.label || JSON.stringify(candidate.key)}`,
            ),
            make("p", String(candidate.sample || ""), "chat-message-text"),
          );
          button.type = "button";
          button.onclick = () => {
            if (alive(e, v) && trusted)
              void work(() =>
                requestCipher("Decrypt", {
                  text: p.text,
                  cipher: candidate.cipher || p.cipher,
                  key: candidate.key,
                  file_mode: false,
                }),
              );
          };
          row.append(button);
          list.append(row);
        }
      return list;
    });
}
async function send(event) {
  event.preventDefault();
  if (sending || !trusted || !current || current.blocked) return;
  const e = epoch,
    v = view,
    c = current,
    r = revision;
  sending = true;
  controls();
  $("send-status").textContent = "Encrypting…";
  try {
    let attempt = pending;
    if (!attempt) {
      const text = $("text").value,
        kind = $("kind").value,
        cipher = $("cipher").value,
        hint = $("hint").value,
        hideCipher = $("hide").checked;
      if (!text.trim() || text.length > 2000)
        throw new Error("Enter 1–2,000 characters.");
      let p = { v: 1, kind: "message", text };
      if (kind === "challenge") {
        const encrypted = await requestCipher("Encrypt", {
          text,
          cipher,
          key: readKey($("key-fields"), cipher),
          file_mode: false,
        });
        if (!alive(e, v) || revision !== r) return;
        if (
          typeof encrypted !== "string" ||
          !encrypted ||
          encrypted.length > 5000
        )
          throw new Error("Cipher output must be 1–5,000 characters.");
        const expected = await requestCipher("Decrypt", {
          text: encrypted,
          cipher,
          key: readKey($("key-fields"), cipher),
          file_mode: false,
        });
        const solutionHash = await sha256(new TextEncoder().encode(expected));
        if (!alive(e, v) || revision !== r) return;
        p = {
          solutionHash,
          v: 1,
          kind: "challenge",
          cipher,
          text: encrypted,
          hint,
          hideCipher,
        };
      }
      const envelope = await encryptChat(
        session.privateKey,
        c.peer.publicKey,
        String(c.id),
        String(session.user.id),
        p,
      );
      if (!alive(e, v) || revision !== r) return;
      attempt = { clientId: crypto.randomUUID(), envelope };
      pending = attempt;
    }
    $("send-status").textContent = "Sending…";
    await api(
      `/api/conversations/${encodeURIComponent(c.id)}/messages`,
      attempt,
    );
    if (!alive(e, v)) return;
    if (pending === attempt && revision === r) {
      pending = null;
      $("compose").reset();
      mode();
    }
    $("send-status").textContent = "Sent.";
    await load();
  } catch (err) {
    if (alive(e, v))
      $("send-status").textContent =
        `${reason(err)}${pending ? " Press Send to retry safely." : ""}`;
  } finally {
    if (alive(e, v)) {
      sending = false;
      controls();
    }
  }
}
export function openMessenger() {
  if (!document.getElementById("messenger-app")) return;
  if (started) {
    poll();
    return;
  }
  started = true;
  mode();
  $("password-toggle").onpointerdown = (event) => {
    if (document.activeElement === $("password")) event.preventDefault();
  };
  $("password-toggle").onclick = () => {
    const input = $("password");
    const start = input.selectionStart,
      end = input.selectionEnd;
    showPassword(input.type === "password");
    input.setSelectionRange(start, end);
  };
  $("auth-form").onsubmit = async (event) => {
    event.preventDefault();
    if (!$("terms").checked) {
      notice("Confirm that you are 13 or older and agree to the Terms of Service before using Messages.", true);
      $("terms").focus();
      return;
    }
    const e = ++epoch,
      username = $("username").value,
      register = event.submitter?.value === "register";
    let password = $("password").value;
    showPassword(false);
    const buttons = [...$("auth-form").querySelectorAll("button")];
    buttons.forEach((b) => (b.disabled = true));
    notice(register ? "Creating account…" : "Unlocking account…");
    try {
      let identity, secret;
      if (register) {
        identity = await createIdentity(password, username);
        secret = identity.authSecret;
      } else secret = await authSecret(password, username);
      if (epoch !== e) return;
      const data = await api(
        register ? "/api/register" : "/api/login",
        {
          username,
          password: secret,
          ...(register
            ? { publicKey: identity.publicKey, keyBackup: identity.keyBackup }
            : {}),
        },
        null,
      );
      if (epoch !== e) return;
      if (
        register &&
        (await fingerprint(data.user.publicKey)) !==
          (await fingerprint(identity.publicKey))
      ) {
        throw new Error(
          "The server returned a different account identity. Please retry.",
        );
      }
      const privateKey = register
        ? identity.privateKey
        : await unlockIdentity(
            password,
            data.user.keyBackup,
            data.user.publicKey,
          );
      if (epoch !== e) return;
      session = { token: data.token, user: data.user, privateKey };
      const owner = session;
      void setPushSession({
        api: (path, body) => api(path, body, owner.token),
        onReceived: () => {
          if (session === owner) void refresh();
        },
        onOpen: async (message) => {
          if (session !== owner) return;
          if (String(owner.user.id) !== String(message.recipientId)) {
            notice(
              "Sign in to the account that received this notification.",
              true,
            );
            return;
          }
          if ($("text").value.trim()) {
            notice(
              "A new message is waiting. Finish or save your draft, then open it from the inbox.",
            );
            return;
          }
          try {
            const result = await api(
              "/api/conversations",
              undefined,
              owner.token,
            );
            if (session !== owner) return;
            const target = takePushMessage(owner.user.id);
            if (!target) return;
            inbox = result.conversations || [];
            renderInbox();
            const conversation = inbox.find(
              (item) => String(item.id) === target.conversationId,
            );
            if (conversation) await choose(conversation);
            else notice("That conversation is no longer available.", true);
          } catch {
            if (session === owner)
              notice(
                "Reconnect and open the inbox to view your new message.",
                true,
              );
          }
        },
      }).catch(() => {});
      $("account").textContent = "Your username: " + data.user.username;
      $("account").hidden = false;
      $("auth-form").reset();
      $("auth").hidden = true;
      $("workspace").hidden = false;
      $("signout").hidden = false;
      $("account-settings").hidden = false;
      notice();
      poll();
    } catch (err) {
      if (epoch === e) notice(reason(err), true);
    } finally {
      password = null;
      if (epoch === e) {
        $("password").value = "";
        showPassword(false);
        buttons.forEach((b) => (b.disabled = false));
      }
    }
  };
  $("back").onclick = () => {
    document.getElementById("messenger-app").dataset.chatOpen = "false";
    poll();
  };
  $("signout").onclick = () => {
    const token = session?.token;
    reset();
    void api("/api/logout", {}, token).catch(() => {});
  };
  $("delete-account").onclick = async () => {
    const owner = session;
    if (!owner) return;
    $("delete-account").disabled = true;
    try {
      const eligibility = await api(
        "/api/account/deletion-status",
        undefined,
        owner.token,
      );
      if (session !== owner) return;
      if (!eligibility.allowed) {
        notice(
          "This administrator account is protected from self-deletion. Your account was not deleted.",
          true,
        );
        $("status").focus();
        return;
      }
      const { mountAccountDeletion } = await import("./account-deletion.js");
      if (session !== owner) return;
      const dialog = document.createElement("dialog");
      dialog.id = "chat-delete-dialog";
      dialog.setAttribute("aria-labelledby", "chat-delete-title");
      dialog.innerHTML =
        '<h2 id="chat-delete-title">Delete your account?</h2><p>Your sign-in information, encrypted account keys, all server conversations involving you, sessions and push registrations will be removed. Copies other people saved and delivered notifications cannot be recalled. Offline lesson progress is kept.</p><div id="chat-delete-form"></div>';
      document.body.append(dialog);
      const form = mountAccountDeletion(
        dialog.querySelector("#chat-delete-form"),
        {
          username: owner.user.username,
          onCancel: () => dialog.close(),
          onDeleted: () => {
            dialog.close();
            if (session === owner) {
              reset();
              notice(
                "Your account has been deleted. Your other cipher tools and lesson progress are still available.",
              );
              $("status").focus();
            }
          },
        },
      );
      dialog.addEventListener("cancel", (event) => {
        if (form.isBusy()) event.preventDefault();
      });
      dialog.addEventListener("close", () => {
        form.clear();
        dialog.remove();
        if (session === owner) $("delete-account").focus();
      });
      dialog.showModal();
      dialog.querySelector("#delete-password").focus();
    } catch (error) {
      if (session === owner) notice(reason(error), true);
    } finally {
      $("delete-account").disabled = false;
    }
  };
  $("invite").onsubmit = async (event) => {
    event.preventDefault();
    const e = epoch,
      b = $("invite").querySelector("button");
    b.disabled = true;
    try {
      const data = await api("/api/conversations", {
        username: $("peer").value,
      });
      if (alive(e)) {
        $("peer").value = "";
        await choose(data.conversation);
        await refresh();
      }
    } catch (err) {
      if (alive(e)) notice(reason(err), true);
    } finally {
      b.disabled = false;
    }
  };
  $("block").onclick = async () => {
    if (!current) return;
    const e = epoch,
      v = view;
    $("block").disabled = true;
    try {
      await api(`/api/conversations/${encodeURIComponent(current.id)}/block`, {
        blocked: !current.blocked,
      });
      if (alive(e, v)) await refresh();
    } catch (err) {
      if (alive(e, v)) notice(reason(err), true);
    } finally {
      if (alive(e)) $("block").disabled = false;
    }
  };
  $("kind").onchange = $("cipher").onchange = mode;
  $("compose").onsubmit = send;
  $("compose").addEventListener("input", () => {
    revision++;
    pending = null;
    $("send-status").textContent = "";
  });
  $("refresh").onclick = () => {
    if (current && !trusted) void choose(current);
    else void refresh();
  };
  document.addEventListener("visibilitychange", poll);
  window.addEventListener("online", poll);
  window.addEventListener("offline", () => {
    if (session && visible())
      notice("You’re offline. Your draft stays here; reconnect to send.", true);
  });
  const observer = new MutationObserver(poll);
  let element = document.getElementById("messenger-app");
  while (element) {
    observer.observe(element, {
      attributes: true,
      attributeFilter: ["hidden", "class", "style", "aria-hidden"],
    });
    element = element.parentElement;
  }
  poll();
}
export default openMessenger;
