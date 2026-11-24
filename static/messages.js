import {
  encryptMessage,
  decryptMessage,
  parseMessage,
} from "./message-crypto.js";
import { openMessenger } from "./messenger.js";
const $ = (id) => document.getElementById(id);
const native = window.Capacitor?.isNativePlatform()
  ? window.Capacitor.Plugins.CipherFiles
  : null;
let initialized = false,
  generation = 0,
  busy = false;
const available = () => !!globalThis.crypto?.subtle;
function status(text, error = false) {
  $("msg-status").textContent = text;
  $("msg-status").dataset.error = String(error);
}
function controls() {
  $("msg-encrypt").disabled = $("msg-decrypt").disabled = busy || !available();
  $("msg-encrypt").textContent = busy ? "Working…" : "Encrypt message";
}
function mode(receive) {
  for (const name of ["send", "receive"]) {
    const active = (name === "receive") === receive;
    $("msg-" + name).hidden = !active;
    $("msg-" + name + "-tab").setAttribute("aria-selected", String(active));
    $("msg-" + name + "-tab").tabIndex = active ? 0 : -1;
  }
}
function invalidate() {
  generation++;
  busy = false;
  controls();
  status("");
}
function clearPackage() {
  $("msg-package").hidden = true;
  $("msg-link").value = $("msg-out-key").value = "";
  $("msg-out-key").type = "password";
  $("msg-reveal").textContent = "Show key";
  $("msg-reveal").setAttribute("aria-pressed", "false");
}
async function copy(id, sensitive = false) {
  const text = $(id).value,
    token = generation;
  if (!text) return;
  try {
    if (native) await native.copyText({ text, sensitive });
    else await navigator.clipboard.writeText(text);
    if (token === generation)
      status(
        sensitive
          ? "Unlock key copied. Give it to your recipient separately from the link."
          : "Encrypted link copied. Share it with your recipient.",
      );
  } catch {
    if (token !== generation) return;
    status("Copy is unavailable. Select the field and copy it manually.", true);
    $(id).focus();
    $(id).select();
  }
}
export function openMessages(incoming = "") {
  openMessenger();
  if (!initialized) {
    initialized = true;
    $("msg-unavailable").hidden = available();
    for (const name of ["send", "receive"]) {
      $("msg-" + name + "-tab").onclick = () => mode(name === "receive");
      $("msg-" + name + "-tab").onkeydown = (e) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
        e.preventDefault();
        const receive =
          e.key === "End" || (e.key !== "Home" && name === "send");
        mode(receive);
        $(receive ? "msg-receive-tab" : "msg-send-tab").focus();
      };
    }
    $("msg-plain").oninput = () => {
      invalidate();
      clearPackage();
    };
    for (const id of ["msg-incoming", "msg-in-key"])
      $(id).oninput = () => {
        invalidate();
        $("msg-opened").hidden = true;
        $("msg-cleartext").textContent = "";
      };
    $("msg-encrypt").onclick = async () => {
      if (busy || !available()) return;
      const token = ++generation;
      busy = true;
      clearPackage();
      controls();
      status("Encrypting on this device…");
      try {
        const result = await encryptMessage($("msg-plain").value);
        if (token !== generation) return;
        // Native localhost cannot be shared; always use the public application address.
        const base = window.Capacitor?.isNativePlatform()
          ? "https://cipher.drewclark.io/"
          : new URL("./", location.href).href;
        $("msg-link").value = base.split("#")[0] + "#message=" + result.token;
        $("msg-out-key").value = result.key;
        $("msg-package").hidden = false;
        status(
          "Encrypted link ready. Share the link, then give the key separately.",
        );
      } catch (e) {
        if (token === generation)
          status(e.message || "Encryption failed. Try again.", true);
      } finally {
        if (token === generation) {
          busy = false;
          controls();
        }
      }
    };
    $("msg-decrypt").onclick = async () => {
      if (busy || !available()) return;
      const token = ++generation;
      busy = true;
      controls();
      $("msg-opened").hidden = true;
      $("msg-cleartext").textContent = "";
      status("Checking and decrypting…");
      try {
        const text = await decryptMessage(
          $("msg-incoming").value,
          $("msg-in-key").value,
        );
        if (token !== generation) return;
        $("msg-cleartext").textContent = text;
        $("msg-opened").hidden = false;
        status("Message decrypted on this device.");
        $("msg-opened-title").focus();
      } catch {
        if (token === generation)
          status(
            "Could not decrypt. Check the complete message and unlock key with the sender. The message may have been changed.",
            true,
          );
      } finally {
        if (token === generation) {
          busy = false;
          controls();
        }
      }
    };
    $("msg-copy-link").onclick = () => copy("msg-link");
    $("msg-copy-key").onclick = () => copy("msg-out-key", true);
    $("msg-reveal").onclick = () => {
      const show = $("msg-out-key").type === "password";
      $("msg-out-key").type = show ? "text" : "password";
      $("msg-reveal").textContent = show ? "Hide key" : "Show key";
      $("msg-reveal").setAttribute("aria-pressed", String(show));
    };
    $("msg-share").hidden = !native?.shareText && !navigator.share;
    $("msg-share").onclick = async () => {
      const text = $("msg-link").value,
        token = generation;
      if (!text) return;
      try {
        if (native?.shareText) await native.shareText({ text });
        else
          await navigator.share({
            title: "Encrypted CipherCraft message",
            text: "Open this message in CipherCraft. Ask me separately for the unlock key.",
            url: text,
          });
        if (token === generation)
          status(
            "Share action finished. Delivery is handled by the app you choose.",
          );
      } catch (e) {
        if (token === generation)
          status(
            e.name === "AbortError"
              ? "Sharing cancelled. Your encrypted link is still ready."
              : "Sharing is unavailable. Use Copy link instead.",
            e.name !== "AbortError",
          );
      }
    };
    $("msg-clear").onclick = () => {
      invalidate();
      clearPackage();
      for (const id of ["msg-plain", "msg-incoming", "msg-in-key"])
        $(id).value = "";
      $("msg-opened").hidden = true;
      $("msg-cleartext").textContent = "";
      status(
        "Messages and keys cleared from this tab. Previously copied or shared content is unchanged.",
      );
    };
    controls();
  }
  if (incoming) {
    $("msg-links-details").open = true;
    invalidate();
    mode(true);
    $("msg-in-key").value = "";
    $("msg-cleartext").textContent = "";
    $("msg-opened").hidden = true;
    if (incoming.length > 4096) {
      $("msg-incoming").value = "";
      status("This message is too large.", true);
      return;
    }
    $("msg-incoming").value = incoming;
    try {
      parseMessage(incoming);
      status(
        "Encrypted message loaded. Enter the separate unlock key from your sender.",
      );
    } catch {
      status(
        "This link does not contain a supported CipherCraft message. Ask the sender for the complete link.",
        true,
      );
    }
  }
}
