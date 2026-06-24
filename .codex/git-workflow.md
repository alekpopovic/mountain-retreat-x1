# Git Workflow

After every user prompt that changes repository files:

1. Check status.
2. Stage changed files.
3. Commit with a concise message.
4. Push to the configured remote.
5. Report the commit hash and push result.

If staging, committing, or pushing is blocked by permissions, authentication, or missing remotes, report the exact blocker.

Do not hide uncommitted repository changes from the user.

