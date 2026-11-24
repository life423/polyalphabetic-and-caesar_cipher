# Account administration

Open `/admin` (or `/admin.html` on the local static server). This separate
workspace keeps administration out of the cipher tools and student workflows.
It uses the existing account password derivation and memory-only bearer login;
it never unlocks message keys or displays password hashes, backups or messages.

## Permissions and deployment

Set `CIPHER_MESSENGER_ADMIN_IDS` on the existing messenger API to the exact
comma-separated immutable numeric IDs authorized by the owner. Empty means no
administrators; malformed configuration fails startup. Usernames, registration
payloads, browser state and user-controlled role fields cannot grant access.
Changing the setting and restarting the API changes the designated accounts.
There is no browser role-assignment endpoint. All configured administrators are
protected from suspension and session revocation through this panel, preventing
accidental loss of access; use server operations for emergency admin revocation.

The owner designated `aiandrew631` as the sole administrator. Its password is
not stored in source, documentation, local plans or deployment artifacts.
The deployment stays on the existing free Azure resources; no new service is
required. Do not expose a database download or publish credentials to enable it.

## Tools

- Search literal username substrings and page through 25 accounts at a time.
- View account status, ID, creation/last-login dates where known, and counts of
  active sessions, push devices, conversations and sent messages.
- Suspend access, restore access, or revoke all sessions and notification
  bindings. Actions require the exact username and a 3–240-character reason.
- Review the latest 100 audit events with actor, target, action, reason and time.
  Reasons should contain no credentials or private message contents.
- The Messages section shows paginated ID, sender, recipient and timestamp
  metadata without ciphertext or decrypted contents. Each row has Delete message;
  the header has Delete all messages, disabled when empty. Individual deletion
  requires typing its ID; clearing history requires `DELETE ALL MESSAGES`.
  A reason is required. These actions permanently remove server copies for both
  participants. Already downloaded client copies and delivered notifications
  cannot be recalled.

Suspension preserves encrypted history and identity keys. It revokes existing
sessions and push bindings, prevents login and prevents new messages to/from
the account. Restore allows a new login; old tokens and device bindings remain
revoked. A notification already handed to Android cannot be recalled by the
server. A restored account must sign in; push alerts can resume on an opted-in
device after registration is renewed. Password reset is outside this increment:
resetting a password without the old wrapping key cannot recover encrypted keys.

The owner-only maintenance endpoint `POST /api/admin/accounts/delete-others`
requires a single configured administrator, a reason and the exact confirmation
`KEEP <owner username> DELETE OTHER ACCOUNTS`. It removes all other identities,
their sessions/device bindings, all conversations and messages, and obsolete
audit events about removed accounts in one transaction. It preserves the owner
and a metadata-only cleanup audit event. This is not exposed as a routine UI
button. Message deletion endpoints are `/api/admin/messages/ID/delete` and
`/api/admin/messages/delete-all`, with `{confirmation,reason}` bodies.

Persistent counters prevent reuse of account, conversation and message IDs after
cleanup. Message tombstones retain only sender ID/client UUID to reject delayed
resend retries (HTTP 410); no deleted message body is retained. Pending push
outbox rows are removed before messages; clearing history resets read markers.
New messages keep increasing IDs, so cached cursors and unread counts still work.

On November 24 the owner's requested production cleanup removed 10 accounts and
19 messages. A subsequent directory/message/role check confirmed only
`aiandrew631` remained with zero messages and working administrator access.
240 Python tests and the expanded individual/all-message deletion browser checks
passed. Both API and frontend updates are deployed; source is included in the release checkpoint.

## Database compatibility and tests

Startup adds `account_status` and `admin_audit` tables without rewriting existing
users, messages or keys. Older creation dates remain unknown rather than guessed.
Login records last sign-in; newly registered users record creation time.
Admin mutations, session revalidation and audit writes share one transaction.
JSON bearer authentication, existing exact-origin CORS, request limits and
admin-specific rate limits protect the API independently of the public HTML.

Run `python -m pytest tests/test_admin.py tests/test_messenger.py tests/test_push_notifications.py -q`.
For browser checks, run an isolated API on port 8504 with an empty database and
`CIPHER_MESSENGER_ADMIN_IDS=1`, serve `dist/static` on 8502, then run
`python -m tests.smoke_admin_browser`. Never point this test at production.
The browser check creates only synthetic accounts and checks role denial,
confirmation, suspension/restoration/revocation, audit, keyboard handling,
offline recovery and phone/tablet/desktop overflow at 320/390/768/1440px.

## Verified deployment — November 24, 2026
The live /admin route redirects to /admin.html and returns HTTP 200. Production sign-in for the designated owner and the metadata directory succeeded; the directory identifies aiandrew631 as the sole administrator. A regular synthetic test account receives HTTP 403. Push status remains configured. 237 Python tests pass; isolated browser actions and 320/390/768/1440px checks pass. Axe WCAG A/AA checks found no violations on sign-in, account lists at phone/tablet/desktop sizes, or the confirmation dialog. This does not replace assistive-technology testing. Source is included in the notification/admin release checkpoint; direct deployment was verified before the GitHub deployment.

Internal design review (heuristics, not measured product scores): hierarchy 9, consistency 9, responsiveness 9, interaction feedback 9, usability 8.5, accessibility 8.5, performance 8. Prioritized follow-ups: test real screen readers and enlarged text, validate account-management language with the owner, and measure field performance. No formal Core Web Vitals claim is made.
