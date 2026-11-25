# Self-service account deletion

Entry points: Messages → Account settings → Delete my account, and the public
`https://cipher.drewclark.io/delete-account` page. Public links open separately
so existing cipher drafts are not discarded. Android uses the same bundled
dialog; the public page does not require installing the app.

The user re-enters the password and types the exact username as confirmation.
The raw password is not sent: the shared client authentication derivation
produces the existing domain-separated secret. No credentials or deletion
tokens are stored in local storage or URLs. The public page also works for
suspended users who cannot obtain a normal sign-in session.

`POST /api/account/delete` requires exactly `{username,password,confirmation}`.
It independently verifies credentials inside the deletion write transaction.
It uses the existing authentication IP/account rate limits, JSON body limits,
exact-origin CORS and no-store responses. A bearer token alone cannot delete an
account, and target user IDs are rejected. Configured administrator IDs are
always rejected with `protected_admin` before any deletion SQL. The companion
authenticated `GET /api/account/deletion-status` returns `{allowed:boolean}`.

One transaction removes the identity/password verifier/encrypted key backup,
all of that user's conversations and both participants' messages in them,
memberships, sessions, push devices/outbox, account status, own retry tombstones
and admin events involving the account. Unrelated accounts/conversations and
device-only lesson progress remain. Persistent non-identifying numeric counters
prevent reuse of removed IDs. Account/name-based rate counters are removed;
network anti-abuse counters remain until their existing expiry/pruning. This
retention is disclosed on the public page. Already saved client copies and
already delivered notifications cannot be recalled.

The active-service deletion returns `{deleted:true}` only after commit. Failed
requests roll back. Uncertain network/timeouts explicitly do not claim success.
The app clears its current chat keys, drafts, identity and notification state
only after confirmed deletion. A deleted username may be registered again, but
it receives a new ID/key identity and no restored history.

## Verification — November 25, 2026

- All 245 Python tests pass, including five focused self-deletion tests for
  protected admin, suspended access, credential/confirmation checks, all-session
  revocation, related data removal, unrelated data preservation, rollback,
  concurrent deletion and safe username reuse.
- Browser tests exercise public and in-app flows against an isolated API using
  synthetic accounts: wrong password, incorrect confirmation, cancel, network
  failure, password visibility, input clearing, focus, protected synthetic admin,
  unrelated cipher-draft preservation and 320/390/768/1440px layouts.
- Public-page WCAG A/AA scans report zero findings; 200% phone text does not
  overflow. Phone/tablet/desktop screenshots were inspected.
- Both deployed web entry points deleted disposable accounts successfully.
  Live checks confirmed revocation of their tokens and removal of both sides of
  the encrypted probe conversation. Both probe accounts were cleaned up.
- Production `aiandrew631` was checked only through sign-in/read-only role and
  deletion-eligibility checks: it exists, remains administrator, and cannot
  self-delete. No production admin deletion request was sent.
- The updated debug APK builds and is installed on the connected Pixel.
  Physical Android dialog/touch testing remains pending while the phone is
  locked; browser viewports do not substitute for that check.

API and static page are deployed to the existing free Azure services. Source
changes are included with the Android CI update. This completes one release
requirement, not a claim of overall Google Play policy approval.

Internal review heuristics: hierarchy 9, consistency 9, feedback 9,
responsiveness 9, usability 8.5, accessibility 8.5, performance 8. Prioritized
follow-ups: unlocked-phone keyboard/landscape checks, screen-reader testing and
field latency measurement. No measured Core Web Vitals claim is made.
