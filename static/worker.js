import { loadPyodide } from "./runtime/pyodide.mjs";
self.addEventListener("unhandledrejection", (event) => {
  self.postMessage({
    fatal: "The cipher engine could not load. Check your connection and retry.",
  });
  event.preventDefault();
});
try {
  const py = await loadPyodide({
    indexURL: new URL("./runtime/", import.meta.url).href,
  });
  const response = await fetch("./engine.zip");
  if (!response.ok) throw new Error("Unable to download the cipher engine.");
  py.unpackArchive(await response.arrayBuffer(), "zip", { extractDir: "/app" });
  py.runPython(`
import sys, json
sys.path.insert(0, '/app')
from src.services.web_service import transform_message, analyze_message, candidate_key, describe_key, crack_message
from src.services.cipher_service import CipherService
def dispatch(raw):
    p = json.loads(raw)
    if p['action'] == 'crack':
        return json.dumps(crack_message(p['text'], p['file_mode']))
    if p['action'] == 'generate':
        return json.dumps(CipherService().generate_substitution_key())
    if p['action'] == 'analyze':
        results = analyze_message(p['text'], p['cipher'], p['file_mode'])
        return json.dumps([dict(key=candidate_key(p['cipher'], r), label=describe_key(p['cipher'], candidate_key(p['cipher'], r)), sample=r.get('sample', '')) for r in results])
    return json.dumps(transform_message(p['text'], p['cipher'], p['action'], p['key'], p['file_mode']))
`);
  self.onmessage = ({ data }) => {
    try {
      py.globals.set("request_json", JSON.stringify(data));
      const result = JSON.parse(py.runPython("dispatch(request_json)"));
      self.postMessage({ id: data.id, result });
    } catch (error) {
      const lines = String(error.message).trim().split("\n");
      self.postMessage({
        id: data.id,
        error: lines.at(-1).replace(/^\w*Error: /, ""),
      });
    }
  };
  self.postMessage({ ready: true });
} catch (error) {
  self.postMessage({ fatal: String(error.message) });
}
