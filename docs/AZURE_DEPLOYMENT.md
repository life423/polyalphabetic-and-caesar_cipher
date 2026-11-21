# CipherCraft web deployment

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
