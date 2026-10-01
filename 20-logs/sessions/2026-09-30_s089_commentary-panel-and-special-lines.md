# s089 — Commentary: 15 lines, honest timestamps, two special lines, sound management

Session opened 2026-09-30 16:45 UTC · not deployed at the user's instruction
Goal: a batch of follow-ups on the spoken-commentary feature, all finished before
a single deploy so there is one build to verify rather than four.

## The batch, and what each one turned out to need

**Only 15 lines in the web UI.** `RENDERED_ENTRIES` was 200. Straightforward —
except the user's answer to "which layer" was *also* delete the old audio, which
makes it a sound-management decision too (below).

**Relative time updating every minute.** This was **a bug, not a formatting
change**: `getRelativeTime` is a pure function, so "2 minutes ago" was computed
once on render and then frozen. A panel nobody interacts with showed timestamps
that quietly went stale. One signal bumped every 60s fixes it, and it has to
live **inside** the component — at module scope `onCleanup` has no scope to bind
to and the interval outlives every panel. I wrote it at module scope first and
moved it.

**A closing line when the agent stops.** Worth a model call because the
alternative is a panel that simply goes quiet, which reads as a crash.

**A decision line when it is blocked.** Also worth one, and it has to do the job
the blocking UI cannot from a single spoken line: say what is being decided, then
name the real option labels — it is spoken aloud and has to stand on its own.

**Fix the bugs.** The user's answer: the open problems, plus anything review
found. Three more came out of it.

**Sound file management.** Retention 100 → 15, matching the display, so audio and
text age out together rather than one outlasting the other by 85 lines.

**Folder hygiene.** `/tmp/opencode` had 234 files loose in one directory.

## Bugs found and fixed

**A pending decision was re-announced every 30 seconds.** The time gap was the
wrong guard: an unanswered decision stays pending for as long as the reader looks
away, so a long turn produced the same line over and over. The guard is now the
decision's **own content** — announced once, quiet until a *different* decision
arrives or the blocking clears.

**Three maps leaked per session.** `leases`, `wasBusy` and the decision signature
were keyed by session and never pruned, so a server up for a week held
bookkeeping for every session it had ever seen. Dropped together when the lease
expires.

**The special lines shared the narration's in-flight guard.** A narration call is
measured at 43–99s, so a closing line could never fire while the commentator was
thinking — exactly when it is wanted. They have their own guard and their own fork.

**`test:httpapi` was edited but never run** (FU-124, closed here). Running it
found a **stale scenario left for the deleted `POST /commentary/speech`** from the
s088 proxy swap. Now **235 pass, 0 fail, 0 missing, 0 extra**.

## Ordering choices worth recording

- **The decision line wins over the closing one.** A session blocked on a
  permission is *also* technically idle, and "done" would be a lie about what
  happened.
- **`closing` needs the busy→idle transition**, not merely being idle: a session
  that was never busy would otherwise produce a closing line about work that never
  happened.
- **Retention and display are one decision.** 15 in the panel and 100 on disk
  means the audio for a line you can no longer read outlasts it by 85.

## Reconciliation (FU-125)

The database and the file store are two separate things and nothing kept them
honest: a sweep deletes files, a restore brings a database without its directory,
and a hand `rm -rf` does both at once. `reconcileAudio` runs once per instance
and clears `audio` on any row whose file is gone. It also repairs the four rows an
earlier `rm -rf` of mine orphaned (seq 153/154/156/157).

## Folder hygiene

`/tmp/opencode`: 234 loose files → `logs/ screenshots/ probes/ bundles/ json/
audio/ backups/ rollback-bin/ scratch/`. Deleted **1.85 GB** of stale SQLite
backups and rollback binaries with the user's explicit yes; kept the twelve `.bak`
source files (250 KB total). **1.9 GB → 82 MB.**

`50-projects/p003-opencode-fork/testing/` was left alone: 784 KB, dated filenames,
and already gitignored (`.gitignore:33`).

## Gates

- `bun turbo typecheck` **30/30**
- app `test:unit` **830 pass / 0 fail**
- opencode commentary + audio + speech-target + commentary-http **90/0**
- `test:httpapi` **235 pass, 0 fail, 0 missing, 0 extra**

## Commits

| Commit | What |
|---|---|
| `c034937` | 15 lines + honest timestamps |
| `c4ed0d0` | retention 15, reconcile, `kind` column, both special lines, panel marking, i18n ×62 |
| `675459f` | review fixes: decision signature, map eviction |

## Not deployed

At the user's instruction: one build at the end, not four. So nothing here has been
run against a real browser or a real narration yet — in particular the two special
lines have never fired, and `kind` has never been rendered.

## Also still open

- **The `[audio]` trace and 5 `console.error` exceptions are still in production.**
  They were the thing that found the `Illegal invocation` bug, and the user has
  been complaining about them. They should come out once the feature is confirmed.
- FU-125 is closed; FU-124 is closed.