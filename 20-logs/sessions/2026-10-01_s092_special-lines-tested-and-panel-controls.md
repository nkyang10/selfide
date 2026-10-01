# s092 — The two special lines, tested for real; narration moved into the panel; a mute button that finally reads

Session opened 2026-10-01 04:30 UTC · deployed `1.1.20261001074512`
Preceded by s091, which fixed the voice picker. This session did what FU-133 asks
for: **stop trusting gates and watch the feature actually run.**

## The two special lines had never been seen either

The picker had passed every gate and been unusable. The `closing` and `prompt`
lines were in the same position — built, tested, deployed, never once triggered.
So both were exercised against the live server with a real turn.

**`prompt` works.** Asked the agent to ask a question:

```
seq 1  kind=prompt  |  "The agent asks which path to take: A (Option A) | B (Option B)."
```

It names the real options from the live question, and the audio rendered. Done.

**`closing` never fired.** Not once, across several attempts. Measuring rather
than guessing gave the reason immediately: a turn that runs `ls` and answers took
**9.4 seconds**, and the tick interval is 10. `closing` required the tick to have
*observed* the session busy — and a turn that starts and finishes between two
ticks is never seen busy. **The one line whose entire purpose is "I have stopped"
did not fire for the quick work a reader most wants to be told about.**

### The user sharpened the definition, and the code was weaker than it

The user's requirement was not "idle": **no tool call running, no follow-up
pending, and do not say it at all if they prompt again straight away.** The code
checked `status.idle`, which is none of those things. Two additions:

- **The newest message must be a completed assistant reply.** A user message last
  means a follow-up is queued; an assistant message without `time.completed` means
  a tool call is still running. One condition rules out both.
- **`closingGrace`, 15 s — longer than the tick.** A reader who is about to type
  never hears it, because the session goes busy again long before the grace runs
  out and the timer is cleared.

## Then the grace period spent its own evidence

Deployed, and still silent. Watching a **124-second** turn: one narration line,
then nothing for 90 seconds after it finished.

The tick loop, walked:

| tick | busy | `wasBusy` reads | action |
|---|---|---|---|
| during turn | true | false | set **true**, return |
| idle #1 | false | **true** ✓ | overwrite to false, start grace, 0 s < 15 s → return |
| idle #2 | false | **false** ✗ | `unnarrated` also false — the narrator already moved the cursor → **return before the grace can matter** |

`wasBusy` is a one-tick signal and the grace spans several. **So any turn whose
work had already been narrated could never say anything** — which is every
narrated turn. The evidence is now a **latch**: set when a tick sees busy, spent
only when the line is actually written.

### The test that would have caught it is deliberately different

The earlier suite tested the *rule*. It was green, and the rule was never wrong —
the state feeding it was. The new suite **feeds it a sequence of ticks**.
Four of its six cases fail against the previous behaviour and pass against this
one.

Verified live afterwards:

```
turn 41 s → grace 15 s → t+90s one line, kind=closing, text=DONE-MARKER
           t+105s … t+150s unchanged: said once, not once per tick
```

## Then a new task: narration off by default, controls in the panel

The user asked for the commentary setting to default **off**, with the icon and
panel always present and the on/off switch in sync with the Settings value.

Two places already disagreed: the store default said `true` and the memo's `??`
fallback said `true` in a different file, so which one a fresh browser got
depended on which was consulted. Both are now `false`.

Asked what should happen to the panel's audio switch, and the answer was to keep
both — so it is no longer greyed out when narration is off. Disabling it made the
pair look broken and implied a link that does not exist.

Then: **remove the Settings row.** That left narration with no on/off control
anywhere, so it moved into the panel header beside the lines — one click rather
than a dialog. The row's dead description key was removed from **62 locales**; its
title survives because the panel switch reuses it rather than adding a second
English-only key. Audio became a **mute icon**, because it is a modifier on
narration rather than a peer of it, and two switches side by side said the
opposite. Muted by default, which it already was — the change was the
affordance, not the value.

Two audio icons were added; the icon set had 49 names and none of them audio.

## The mute button took two more tries

**Clicking it did nothing to the icon.** Not because the flag failed to flip —
`href` changed and it persisted — but because `IconButtonV2` took
`icon?: JSX.Element` and rendered it once. `icon={<Icon name={flag() ? …} />}`
reads the flag when the button is *created*. In Solid that form looks reactive and
is not. `icon` now also accepts a getter; additive, since every existing caller
passes a static element.

**Then it flipped but looked unchanged.** The two icons differed by a mark about
**3.6 units wide** in the corner of a 20-unit box — roughly three pixels at the
rendered size. Both glyphs are redrawn, and muted now takes a slash straight
across the whole icon, which is the only version legible at 20 px. The button also
carries `state` and `aria-pressed`.

Verified live:

```
before  : href=off  aria-pressed=false  data-state=pressed  stored=false
click 1 : href=on   aria-pressed=true   data-state=rest     stored=true
click 2 : href=off  aria-pressed=false  data-state=pressed  stored=false
```

## Three wrong diagnoses in a row, and what they cost

| What I said | What was true |
|---|---|
| the icon is not reactive | true, and the first fix missed the second construction site |
| the icon did not flip | it did flip — it was illegible |
| `paths: 0`, so no SVG rendered | **my probe was wrong** — this `Icon` uses a sprite `<use>`, never an inline `<path>` |

All three gates stayed green throughout: typecheck 30/30, app 845/0, opencode
545/0. None of them can see a third-party component throwing, a glyph too small to
read, or a probe querying the wrong DOM. **Every one of these was found by a person
pressing the thing.**

## Gates

- `bun turbo typecheck` **30/30**
- app `test:unit` **845 pass / 0 fail**, i18n parity **5/5** after 62 keys touched
- opencode commentary and server **545 pass / 0 fail**
- `test:httpapi` **236 pass / 0 fail / 0 missing / 0 extra** (unchanged)

## Still open

- **FU-126** — the `[audio]` trace is still in production. 18 `console.log` lines
  and 5 `console.error`. The watchdog inside it earned its place twice; the traces
  have not earned theirs since.
- **FU-133** — this session is the argument for it, twice over.