# Operations

## Where it runs

- **Production (demo):** Streamlit Community Cloud, deployed automatically from `main`.
- **Pre-release check:** run the app locally or deploy a second app from a test branch on Streamlit Community Cloud before merging larger changes.
- **CI:** GitHub Actions on every push and pull request (`.github/workflows/ci.yml`).

`main` is protected: changes arrive through pull requests that need a green CI. That is what keeps the automatic deploy safe.

## Data and backups

The app stores nothing: uploads live in memory for the session. The only persistent assets are the code and the fictional sample files, both in Git. Releases (tags) are the restore points. A copy of the repository can be kept with `git clone --mirror` if an extra backup is wanted.

## Logs

The app and the CLI log errors with Python's `logging` (level set by `FLOW_METRICS_LOG_LEVEL`). On Streamlit Community Cloud, open the app and choose **Manage app** to see the logs. Validation errors are shown to the user and are not logged as failures; unexpected errors are logged with a traceback and the user sees a generic message.

## Recovery

If a deploy breaks the demo:

1. Find the last good release on the GitHub **Releases** page (for example `v0.1.0`).
2. Revert the bad commit on a branch (`git revert <sha>`), open a pull request and merge it once CI is green. Streamlit redeploys `main` automatically.
3. If the platform itself is the problem, use **Reboot app** in the Streamlit Cloud menu, or redeploy from the release tag.

## Availability

The demo uses free hosting and sleeps after a period without visits; the first visit then takes a few seconds to wake it up. There are no real users or SLAs, so no uptime monitoring is set up. If that changes, a free uptime checker pointed at the app URL is the next step.
