import { API_BASE } from "./messenger-config.js";
import { authSecret } from "./messenger-crypto.js";

const messages = {
  invalid_credentials:
    "Could not verify this account. Check your username and password. If you already submitted deletion, try signing in to check whether it completed.",
  confirmation_mismatch: "Type the exact username again to confirm deletion.",
  protected_admin:
    "This administrator account is protected from self-deletion. Your account was not deleted.",
  rate_limited: "Too many attempts. Wait 15 minutes before trying again.",
};

export function mountAccountDeletion(
  container,
  { username = "", onDeleted, onCancel } = {},
) {
  let busy = false;
  // Static markup only; account names and responses are assigned as text/value.
  container.innerHTML = `<form class="deletion-form">
    <label for="delete-username">Username</label><input id="delete-username" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" pattern="[a-z0-9_]{3,24}" minlength="3" maxlength="24" required>
    <label for="delete-password">Confirm your password</label><div class="deletion-password"><input id="delete-password" name="password" type="password" autocomplete="current-password" minlength="12" maxlength="128" required><button type="button" id="delete-show-password" aria-label="Show password" aria-pressed="false">Show</button></div>
    <label for="delete-confirmation">Type your username again to confirm</label><input id="delete-confirmation" autocomplete="off" autocapitalize="none" spellcheck="false" maxlength="24" required aria-describedby="delete-consequence">
    <p id="delete-consequence" class="deletion-warning">This permanently deletes your account and its server-side conversations for both participants. This cannot be undone.</p>
    <p id="delete-status" class="deletion-status" role="status" aria-live="polite"></p>
    <div class="deletion-actions"><button type="button" id="delete-cancel" class="secondary">Cancel</button><button type="submit" id="delete-submit" class="deletion-danger">Permanently delete my account</button></div>
  </form>`;
  const $ = (id) => container.querySelector("#" + id);
  const form = container.querySelector("form");
  $("delete-username").value = username;
  $("delete-username").readOnly = !!username;
  $("delete-cancel").hidden = !onCancel;
  function say(text, error = false) {
    $("delete-status").textContent = text;
    $("delete-status").dataset.error = String(error);
    $("delete-status").setAttribute("role", error ? "alert" : "status");
  }
  function hidePassword() {
    $("delete-password").type = "password";
    $("delete-show-password").textContent = "Show";
    $("delete-show-password").setAttribute("aria-label", "Show password");
    $("delete-show-password").setAttribute("aria-pressed", "false");
  }
  $("delete-show-password").onclick = () => {
    const show = $("delete-password").type === "password";
    $("delete-password").type = show ? "text" : "password";
    $("delete-show-password").textContent = show ? "Hide" : "Show";
    $("delete-show-password").setAttribute(
      "aria-label",
      show ? "Hide password" : "Show password",
    );
    $("delete-show-password").setAttribute("aria-pressed", String(show));
  };
  $("delete-cancel").onclick = () => {
    if (!busy) {
      form.reset();
      hidePassword();
      onCancel?.();
    }
  };
  form.onsubmit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const name = $("delete-username").value.trim().toLowerCase();
    const confirmation = $("delete-confirmation").value;
    if (confirmation !== name) {
      say(messages.confirmation_mismatch, true);
      $("delete-confirmation").focus();
      return;
    }
    let password = $("delete-password").value;
    $("delete-password").value = "";
    hidePassword();
    busy = true;
    form.querySelectorAll("input,button").forEach((e) => (e.disabled = true));
    say("Verifying and deleting your account…");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      const secret = await authSecret(password, name);
      password = null;
      const response = await fetch(API_BASE + "/api/account/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: name,
          password: secret,
          confirmation,
        }),
        credentials: "omit",
        cache: "no-store",
        signal: controller.signal,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(
          messages[data.error] ||
            "Deletion was not confirmed. Enter your password again and retry.",
        );
      if (data.deleted !== true)
        throw new Error(
          "Deletion was not confirmed. Try signing in to check your account before retrying.",
        );
      form.reset();
      hidePassword();
      say("Your account has been deleted.");
      onDeleted?.();
    } catch (error) {
      say(
        error.name === "AbortError"
          ? "The server took too long; deletion is not confirmed. Try signing in to check your account before retrying."
          : error instanceof TypeError
            ? "Could not reach the server. Deletion is not confirmed. Reconnect and check your account before retrying."
            : error.message,
        true,
      );
    } finally {
      password = null;
      clearTimeout(timer);
      busy = false;
      form
        .querySelectorAll("input,button")
        .forEach((e) => (e.disabled = false));
    }
  };
  return {
    isBusy: () => busy,
    clear: () => {
      form.reset();
      hidePassword();
    },
  };
}
