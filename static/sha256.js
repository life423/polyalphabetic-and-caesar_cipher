// Shared by the free-form lab and guided lessons; no UI or persistence.
export async function sha256(bytes) {
  const buffer = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(buffer)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}
export function digestBits(hex) {
  return [...hex]
    .map((value) => parseInt(value, 16).toString(2).padStart(4, "0"))
    .join("");
}
