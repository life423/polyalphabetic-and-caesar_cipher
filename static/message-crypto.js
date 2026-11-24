// Versioned, bounded AES-GCM envelope. Keys are never part of the envelope.
export const MAX_BYTES = 2000;
const encoder = new TextEncoder();
const aad = encoder.encode("CipherCraft message v1");
export function encode(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}
export function decode(text) {
  if (!/^[A-Za-z0-9_-]+$/.test(text)) throw new Error("Invalid encoding.");
  const bytes = Uint8Array.from(
    atob(text.replace(/-/g, "+").replace(/_/g, "/")),
    (c) => c.charCodeAt(0),
  );
  if (encode(bytes) !== text) throw new Error("Invalid encoding.");
  return bytes;
}
export function parseMessage(input) {
  let text = input.trim();
  if (text.length > 4096) throw new Error("This message is too large.");
  const sharedLink = text.match(/https?:\/\/[^\s#]+\/#message=[A-Za-z0-9_-]+/);
  if (sharedLink) text = sharedLink[0];
  if (/^https?:\/\//i.test(text)) {
    const url = new URL(text);
    text = url.hash;
  }
  if (text.startsWith("#message=")) text = text.slice(9);
  const value = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(decode(text)),
  );
  if (
    !value ||
    value.v !== 1 ||
    value.alg !== "A256GCM" ||
    Object.keys(value).sort().join(",") !== "alg,ct,iv,v"
  )
    throw new Error("Unsupported message format.");
  if (typeof value.iv !== "string" || typeof value.ct !== "string")
    throw new Error("Invalid message.");
  const iv = decode(value.iv),
    ciphertext = decode(value.ct);
  if (
    iv.length !== 12 ||
    ciphertext.length < 17 ||
    ciphertext.length > MAX_BYTES + 16
  )
    throw new Error("Invalid message size.");
  return {
    iv,
    ciphertext,
    token: encode(encoder.encode(JSON.stringify(value))),
  };
}
export async function encryptMessage(text) {
  const bytes = encoder.encode(text);
  if (!text.trim() || bytes.length > MAX_BYTES)
    throw new Error(
      `Write a message of up to ${MAX_BYTES.toLocaleString()} UTF-8 bytes.`,
    );
  const keyBytes = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, [
    "encrypt",
  ]);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv, additionalData: aad, tagLength: 128 },
    key,
    bytes,
  );
  const token = encode(
    encoder.encode(
      JSON.stringify({
        v: 1,
        alg: "A256GCM",
        iv: encode(iv),
        ct: encode(ciphertext),
      }),
    ),
  );
  return { token, key: encode(keyBytes) };
}
export async function decryptMessage(input, unlock) {
  const { iv, ciphertext } = parseMessage(input);
  const bytes = decode(unlock.trim());
  if (bytes.length !== 32)
    throw new Error("Use the complete 43-character unlock key.");
  const key = await crypto.subtle.importKey("raw", bytes, "AES-GCM", false, [
    "decrypt",
  ]);
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv, additionalData: aad, tagLength: 128 },
    key,
    ciphertext,
  );
  return new TextDecoder("utf-8", { fatal: true }).decode(plaintext);
}
