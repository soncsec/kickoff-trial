# Roadmap

The short version. Detail lives in GitHub milestones and issues.

## Now: M1: Working to-do API

All task endpoints (create, list, get, update, delete) work against SQLite,
with tests, merged through issue → pull request → green CI.
[Milestone](https://github.com/soncsec/kickoff-trial/milestone/1)

## Next

- M2: Everyday use: filter tasks by done or not done, and sort by creation time.
- M3: Due dates: an optional due date per task, and a list of overdue tasks.

## Later

- Export and import tasks as JSON.
- Tags on tasks.

## Not planned

- Accounts or sign-in: one local user.
- Deployment: it runs on the operator's machine only.
- Web pages or a frontend: HTTP API only.
- External services or secrets.
