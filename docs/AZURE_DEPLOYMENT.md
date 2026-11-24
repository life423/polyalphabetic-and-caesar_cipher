# CipherCraft web deployment

## Free custom-domain site

The primary browser app is `https://cipher.drewclark.io`.
Resource `ciphercraft-public` in `rg-ciphercraft` uses Azure Static Web Apps **Free**
in East US 2. Its default hostname is
`mango-bay-03a295b0f.5.azurestaticapps.net`. Azure manages HTTPS at no extra charge.
The Squarespace DNS record is CNAME `cipher` to that hostname. Root, mail,
nameservers and other subdomains do not need changing.

`static/` contains the interface and module worker. `scripts/build_static.py`
copies the pinned Pyodide runtime from `tools/runtime/package-lock.json` and
packages shared Python sources as `engine.zip` into ignored `dist/static/`.
All assets come from the same origin. The worker invokes the existing
`web_service` adapter; inputs are JSON data, never executable Python source.
Cipher-tool inputs, keys and file content stay in the browser. The optional
messenger sends encrypted conversations to its separate Azure API. This is client-side Python,
not an iframe or an API proxy. Existing validation and file semantics apply.

`.github/workflows/static-app.yml` builds, runs shared tests and exercises
the real WASM engine in Chromium before deploying pushes to main. It uses
repository secret `AZURE_STATIC_WEB_APPS_API_TOKEN`, scoped to this static app;
the token is never committed. Pull requests verify without deploying. The
workflow can also be run manually. Browser checks include six cipher types,
four analyzers, exact mixed-line-ending downloads, offline operations after
startup, independent sessions, loading failure/retry, keyboard navigation and
320/390/768/1440-pixel layouts.

Free hosting has Azure plan quotas. The first load downloads a Python runtime;
there is no offline reload/service-worker cache. Chromium is automated; Safari
and Firefox still need manual compatibility checks. Responsive screenshots do
not establish Core Web Vitals compliance or assistive-technology compatibility.

## Original Streamlit App Service

The browser app uses Streamlit and the same `CipherService`, core ciphers, and
analyzer as the desktop app. Desktop entry points and downloadable releases
remain separate from the web runtime.

## Azure resources

- Subscription: `drewclark.io`
- Resource group: `rg-ciphercraft` (resource-group metadata in East US 2)
- Linux App Service plan: `asp-ciphercraft-free`, **West US 2**, F1 Free
- App Service: `ciphercraft-drewclark`, Python 3.12
- URL: <https://ciphercraft-drewclark.azurewebsites.net/>
- Startup command: `sh startup.sh`
- App setting: `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- Health endpoint: `/_stcore/health`

Free-plan quota was unavailable in East US 2 and Central US; West US 2 accepted
the F1 plan. The free plan can sleep when idle and has Azure's shared CPU and
connection limits. Move to a paid plan if continuous availability or higher
concurrency is required; that is a separate hosting-cost decision.

## Deployments

`.github/workflows/web-app.yml` runs the shared tests, Streamlit AppTest tests,
critical lint, and real Chromium workflows at phone, tablet, and desktop sizes.
Successful pushes to `main` deploy a small source ZIP to App Service, restart
the worker to load the deployed Python code, and check its health endpoint.
This restart matters because production file watching is disabled and Oryx
extracts each deployment to a new runtime directory. The desktop CI/release
workflow continues independently.

GitHub authenticates with Entra workload federation (OIDC), not a client secret
or publish-profile password. The deployment identity is scoped to this web app
with the `Website Contributor` role. Its federated subject is
`repo:life423/polyalphabetic-and-caesar_cipher:ref:refs/heads/main`.

Repository variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_WEBAPP_NAME`
- `AZURE_RESOURCE_GROUP`
- `AZURE_WEBAPP_URL`

These variables are identity/resource identifiers, not authentication secrets.

For a manual deployment using an authenticated Azure CLI:

```bash
python scripts/package_web.py --output web-app.zip
az webapp deploy --resource-group rg-ciphercraft --name ciphercraft-drewclark \
  --src-path web-app.zip --type zip --track-status false
```

The packager explicitly includes the web entry point, runtime requirements,
Streamlit configuration, startup script, and Python source. It excludes local
environments, tests, credentials, and generated desktop executables. Azure's
Oryx builder installs runtime dependencies before starting Streamlit on port
8000. Keep startup shell scripts in LF format; the packager normalizes them.

## Verification

```bash
python -m pip install -e ".[dev,web,web-test]"
python -m pytest tests/ -q
python -m playwright install chromium
python -m streamlit run web_app.py --server.port 8501
# In another terminal:
python tests/smoke_web_browser.py --url http://127.0.0.1:8501
```

The same browser smoke script can verify the live URL. Screenshots are saved
under `.venv/web-browser-checks` by default. It checks encryption/decryption,
Vigenère key recovery and application, UTF-8 result downloads, multiline file
uploads, invalid analysis input, separate browser sessions, keyboard focus,
and touch layouts at 320, 390, and 768 pixels wide.

Messages and uploaded bytes stay in Streamlit session memory. The browser
interface never accepts server input/output paths, never deletes local files,
and does not use a shared message cache. New source or settings invalidate
displayed results; analysis candidates belong to their ciphertext and cipher.

## Messenger API — November 24, 2026

The existing F1 `ciphercraft-drewclark` App Service now hosts the messenger API,
not the legacy Streamlit UI. Its plan remains Free. `/api/health` responds over
HTTPS. A hosted test verified browser CORS, actual account/message writes,
server restart, persistent history and unlocking the saved encrypted identity.
The local frontend and rebuilt APK support this beta; the custom-domain static
frontend is unchanged until separately deployed.

Database: `/home/data/cipher-messenger.sqlite3`, outside application deployments.
Backend package: `python scripts/package_messenger.py --output dist/messenger-api.zip`.
Startup remains `sh startup.sh`, now using gunicorn for the API. The new
`messenger-api.yml` deployment workflow is separate; legacy Streamlit deployment
is opt-in to prevent accidental replacement of the API. See [Messenger](MESSENGER.md)
and [backend operations](../src/messenger/README.md).
