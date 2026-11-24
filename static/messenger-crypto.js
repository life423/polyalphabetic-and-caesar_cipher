import { encode, decode } from "./message-crypto.js";
const utf8 = new TextEncoder();
const text = new TextDecoder("utf-8", { fatal: true });
const iterations = 600000;
function canonicalPublic(key) {
  if (
    !key ||
    key.kty !== "EC" ||
    key.crv !== "P-256" ||
    typeof key.x !== "string" ||
    typeof key.y !== "string" ||
    decode(key.x).length !== 32 ||
    decode(key.y).length !== 32
  )
    throw new Error("Invalid conversation identity.");
  return { kty: "EC", crv: "P-256", x: key.x, y: key.y };
}
async function passwordMaterial(password) {
  if (
    typeof password !== "string" ||
    password.length < 12 ||
    password.length > 128
  )
    throw new Error("Use a password of 12–128 characters.");
  return crypto.subtle.importKey(
    "raw",
    utf8.encode(password),
    "PBKDF2",
    false,
    ["deriveKey", "deriveBits"],
  );
}
async function wrappingKey(password, salt) {
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", hash: "SHA-256", iterations, salt },
    await passwordMaterial(password),
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}
export async function authSecret(password, username) {
  // Domain-separated from backup encryption: the raw password is never sent.
  const salt = utf8.encode(
    "CipherCraft sign-in v1:" + username.trim().toLowerCase(),
  );
  return encode(
    await crypto.subtle.deriveBits(
      { name: "PBKDF2", hash: "SHA-256", iterations, salt },
      await passwordMaterial(password),
      256,
    ),
  );
}
export async function createIdentity(password, username) {
  const pair = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveBits"],
  );
  const publicKey = canonicalPublic(
    await crypto.subtle.exportKey("jwk", pair.publicKey),
  );
  const jwk = await crypto.subtle.exportKey("jwk", pair.privateKey);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: utf8.encode("CipherCraft identity backup v1"),
      tagLength: 128,
    },
    await wrappingKey(password, salt),
    utf8.encode(JSON.stringify(jwk)),
  );
  const privateKey = await crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    ["deriveBits"],
  );
  return {
    publicKey,
    privateKey,
    keyBackup: { salt: encode(salt), iv: encode(iv), ct: encode(ct) },
    authSecret: await authSecret(password, username),
  };
}
export async function unlockIdentity(password, backup, expectedPublicKey) {
  if (!backup || typeof backup.ct !== "string" || backup.ct.length > 6000)
    throw new Error("Invalid identity backup.");
  const salt = decode(backup.salt),
    iv = decode(backup.iv);
  if (salt.length !== 16 || iv.length !== 12)
    throw new Error("Invalid identity backup.");
  const bytes = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: utf8.encode("CipherCraft identity backup v1"),
      tagLength: 128,
    },
    await wrappingKey(password, salt),
    decode(backup.ct),
  );
  const jwk = JSON.parse(text.decode(bytes));
  const publicKey = canonicalPublic(jwk);
  if (
    expectedPublicKey &&
    JSON.stringify(publicKey) !==
      JSON.stringify(canonicalPublic(expectedPublicKey))
  )
    throw new Error("Account identity does not match its encrypted backup.");
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    ["deriveBits"],
  );
}
async function conversationKey(privateKey, peerPublicKey, conversationId) {
  const peer = await crypto.subtle.importKey(
    "jwk",
    canonicalPublic(peerPublicKey),
    { name: "ECDH", namedCurve: "P-256" },
    false,
    [],
  );
  const secret = await crypto.subtle.deriveBits(
    { name: "ECDH", public: peer },
    privateKey,
    256,
  );
  const material = await crypto.subtle.importKey("raw", secret, "HKDF", false, [
    "deriveKey",
  ]);
  return crypto.subtle.deriveKey(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt: utf8.encode("CipherCraft conversation v1:" + conversationId),
      info: utf8.encode("authenticated puzzle transport"),
    },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}
const aad = (conversationId, senderId) =>
  utf8.encode(
    JSON.stringify([
      "CipherCraft chat v1",
      String(conversationId),
      String(senderId),
    ]),
  );
function validatePayload(payload) {
  if (
    !payload ||
    payload.v !== 1 ||
    !["message", "challenge"].includes(payload.kind) ||
    typeof payload.text !== "string" ||
    !payload.text.trim() ||
    payload.text.length > 5000
  )
    throw new Error("Unsupported conversation message.");
  if (
    payload.kind === "challenge" &&
    (!["Caesar", "Vigenère", "Rail Fence", "Affine"].includes(payload.cipher) ||
      (payload.hint !== undefined &&
        (typeof payload.hint !== "string" || payload.hint.length > 160)) ||
      (payload.hideCipher !== undefined &&
        typeof payload.hideCipher !== "boolean"))
  )
    throw new Error("Invalid cipher challenge.");
  if (
    payload.solutionHash !== undefined &&
    (typeof payload.solutionHash !== "string" ||
      !/^[a-f0-9]{64}$/.test(payload.solutionHash))
  )
    throw new Error("Invalid solution check.");
  return payload;
}
export async function encryptChat(
  privateKey,
  peerPublicKey,
  conversationId,
  senderId,
  payload,
) {
  validatePayload(payload);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: aad(conversationId, senderId),
      tagLength: 128,
    },
    await conversationKey(privateKey, peerPublicKey, conversationId),
    utf8.encode(JSON.stringify(payload)),
  );
  return { v: 1, iv: encode(iv), ct: encode(ct) };
}
export async function decryptChat(
  privateKey,
  peerPublicKey,
  conversationId,
  senderId,
  envelope,
) {
  if (
    !envelope ||
    envelope.v !== 1 ||
    typeof envelope.ct !== "string" ||
    envelope.ct.length > 40000 ||
    typeof envelope.iv !== "string" ||
    decode(envelope.iv).length !== 12
  )
    throw new Error("Unsupported encrypted message.");
  const bytes = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: decode(envelope.iv),
      additionalData: aad(conversationId, senderId),
      tagLength: 128,
    },
    await conversationKey(privateKey, peerPublicKey, conversationId),
    decode(envelope.ct),
  );
  return validatePayload(JSON.parse(text.decode(bytes)));
}
export async function fingerprint(publicKey) {
  const value = canonicalPublic(publicKey);
  const digest = await crypto.subtle.digest(
    "SHA-256",
    utf8.encode(JSON.stringify([value.crv, value.x, value.y])),
  );
  return [...new Uint8Array(digest)]
    .map((n) => n.toString(16).padStart(2, "0"))
    .join("")
    .match(/.{1,4}/g)
    .join(" ");
}
