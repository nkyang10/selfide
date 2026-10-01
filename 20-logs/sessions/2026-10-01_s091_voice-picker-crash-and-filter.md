# s091 — The voice picker crashed on open; fixed, filtered, and made readable

Session opened 2026-10-01 03:30 UTC · deployed `1.1.20261001041357`
Preceded by s090, which built the picker and handed the coding over. This session
is the first one to actually **open the thing**.

## What the user saw

Opening the voice picker threw, every time:

```
SyntaxError: Failed to execute 'querySelector' on 'Element':
'[data-key="192.168.1.162:8880\nzh-HK-HiuMaanNeural"]' is not a valid selector
```

The feature was built, pushed, deployed and unit-tested across 78 files, and had
**never been opened**. The picker was not merely awkward; it was unusable.

## The cause, and the part that is not ours

The option key joined endpoint and voice with a **raw newline**:

```ts
const key = `${source.host}\n${entry.name}`
```

A newline is the obvious separator — neither part can contain one — and it is the
one character guaranteed to be invalid inside a quoted CSS attribute value.

The selector is built by **Kobalte**, unescaped:

```ts
// @kobalte/core  list-keyboard-delegate.ts
getItem(e) { return this.ref?.()?.querySelector(`[data-key="${e}"]`) }
```

So the fix belonged in our key, not in `node_modules`. `|` cannot appear in a
hostname (RFC 1035), a port, or a voice name, so it separates just as
unambiguously and survives the selector.

## Two mistakes of my own, in order

**The first fix did not work.** I changed the key in the catalogue helper and
shipped it. The picker still threw — on the *next* bundle. The panel was building
its own template for the Select value:

```tsx
value={(option) => `${option.host}\n${option.voice}`}   // ← still a newline
```

Two places building the same identity, and the test only pinned the helper that
the component did not use. **Only the user opening the picker found this.** Both
now go through `voiceKey`, and the call site says why it must not become a local
template again.

**I looked in the wrong place first.** I grepped for selector interpolation across
the app and fixed three unescaped sites (`prompt-input.tsx:826`,
`home-session-search-controller.ts:156`, `layout.tsx:503`) before locating the
actual thrower. Those three were real and worth fixing, but they were not the bug,
and I only found the real one by extracting the exact selector out of the served
bundle.

## Then: 323 options is not a picker

With it open, the next problem was obvious — 322 voices alphabetical, the reader's
own language 14 entries deep, labels reading `zh-HK-HiuMaanNeural`, which tells
you nothing about what you will hear.

- **`SelectV2` gained an opt-in `filterable` prop.** Opt-in because a search box is
  wrong for the many selects that have five options. **Exactly one call site
  passes it**; every other dropdown takes the original path unchanged.
- **The label is now the service's own description**, with the technical name kept
  beside it: *"Microsoft HiuMaan Online (Natural) - Chinese (Hong Kong SAR) ·
  zh-HK-HiuMaanNeural"*. The description was in the payload the whole time.
- **Matching is fuzzysort**, the matcher `useFilteredList` already uses, over the
  label, the technical name and the voice's aliases.

Verified against the **real 323-voice catalogue**, not assumed:

| Query | Found |
|---|---|
| `cantonese` | the two Cantonese voices + the baked voice |
| `hkmn` | `zh-HK-HiuMaanNeural` — a substring test cannot do this |
| `hong kong` | Chinese (Hong Kong) voices |
| `nova` | the baked voice, by alias |

One trap: Kobalte's Select owns the keyboard, so a keystroke reaching it is
treated as typeahead. The field keeps its own key events, and the query resets when
the menu closes so a stale filter cannot hide the list next time.

## Also verified while I was in there

The review that caught the picker problem also checked the thing I had been
worried about since s090 landed:

- **The voice picker is fully wired.** lease → `renderAudio` → `audio.render`, and
  all three paths pass it — narration, closing, decision. My worry that the UI
  picked a voice the server ignored was wrong.
- **SSRF protection is intact.** The client can send a host, and it still goes
  through `speechBaseUrl` before any request. 23 guard tests still green.
- **Three comments had become lies** and were corrected: "config-file only: the
  client never chooses a host" (false since the picker), "the oldest 100 for this
  session" (retention is 15), and "a host that is config rather than a field in a
  request body".

## Gate

- `bun turbo typecheck` **30/30**
- app `test:unit` **845 pass / 0 fail**
- i18n parity **5/5** (one new key × 62 locales)
- `test:httpapi` **236 pass / 0 fail / 0 missing / 0 extra** (unchanged)

## The lesson worth keeping

This feature passed every gate three times — 78 files, 1114 insertions, typecheck
clean, unit tests green, pushed, deployed — and was **completely non-functional**.
Not one of those gates could see it, because the failure was a DOM selector
thrown by a third-party component that no test in this repo renders.

**A feature that has never been opened is not tested.** The picker took three
deploys to become usable, and only the last one was found by the person using it.

That is the argument for a five-second manual check before shipping, not a
stronger gate.

## Still open

- **The `[audio]` trace is still in production** (FU-126): 18 `console.log` lines
  and 5 `console.error`. The watchdog inside it earned its place — it is what
  distinguished "the browser accepted `play()`" from "the media actually loaded",
  which is how the CSP block and the `Empty src attribute` false alarm were both
  caught. The traces should come out.
- The special lines and the `kind` marker have still never been seen in a browser.