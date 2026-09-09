// KNOWLEDGE/ wiki prototype data — what the librarian agent maintains in the repo.
// Seeded with REAL findings from engine run 20260908-0233 research substrate.
const KNOWLEDGE = {
  "concurrency-sqlite": {
    title: "SQLite concurrency: multi-station safety",
    desc: "Cross-cutting run lessons: atomic cashiering, guarded writes, no lost updates, no over-sell.",
    tldr: "One connection per request, SQLite WAL, and guarded UPDATE statements (rowcount==0 as the conflict signal) keep a single stock.db safe across concurrent stations — never check-then-update.",
    prose: "A cloud POS is a shared-database problem: N cashier stations mutate one SQLite file. The pattern that works is to give every request its own connection (with busy_timeout), use WAL so readers never block writers, and express every mutation as a single guarded UPDATE whose rowcount tells you whether the operation won or lost a race. Check-then-update across two statements is a TOCTOU bug and is explicitly rejected.",
    summary: "How the POS keeps a single stock.db consistent across concurrent stations.",
    facts: [
      ["Mode", "SQLite WAL journal_mode; busy_timeout set; one connection per request"],
      ["Stock decrement", "UPDATE items SET quantity=quantity-? WHERE id=? AND quantity>=? — atomic, never negative"],
      ["Concurrency proof", "4-thread test on this box (Python 3.12.3 / SQLite 3.45.1) — no negative stock, no duplicate receipts"],
      ["Guarded writes", "UPDATE ... WHERE id=? AND version=? ; rowcount==0 ⇒ conflict (409)"]
    ],
    findings: [
      {kf:"Atomic charge = one transaction", body:"checkout() wraps stock check-and-decrement, receipt-number minting and the transaction+line inserts in ONE `with conn:` block, so a charge is all-or-nothing under interleaved requests.", src:"run 20260908-0233 §1"},
      {kf:"Rowcount bug — no RETURNING", body:"cursor.rowcount reads sqlite3_changes(); it reports 0 after a table is dropped/recreated even if rows changed. Keep the version guard and read the fresh row with a separate SELECT; never attach RETURNING to the guarded UPDATE.", src:"run 20260908-0233 §2"}
    ],
    sources: [
      "https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.rowcount",
      "https://github.com/python/cpython/issues/93421",
      "https://www.sqlite.org/wal.html",
      "https://www.sqlite.org/lockingv3.html"
    ],
    related: ["cloud-pos/item-crud.md","cloud-pos/refunds.md","cloud-pos/cashiering.md"]
  },
  "barcode-qr-scanning": {
    title: "Barcode & QR scanner input",
    desc: "Cross-cutting: hardware input path on the register page.",
    tldr: "A keyboard-wedge barcode scanner behaves as a fast keyboard (digits + Enter); a camera-decoded QR string is the same event — both ride the identical GET /scan/{code} lookup and keydown-buffer add-to-ticket path.",
    prose: "There is no need for a separate QR code path. A keyboard-wedge scanner bursts keystrokes then Enter; a camera decoder produces a plain string. Treating both as the same 'scan event' keeps the server surface to one lookup route and one client-side buffer, documented as identical for the cashier.",
    summary: "A keyboard-wedge barcode scanner is just a fast keyboard (digits burst + Enter). A camera-decoded QR string is handled identically.",
    facts: [
      ["Barcode path", "keyboard-wedge burst → keydown buffer → Enter terminator → GET /scan/{code}"],
      ["QR path", "camera-decoded string (e.g. \"017\" or URL tail) → identical scan event"]
    ],
    findings: [
      {kf:"Shared lookup route", body:"QR (hardware camera) and barcode both resolve via GET /scan/{code} → 200 JSON {id,name,price_cents,quantity}, 404 for unknown/inactive. Research §4/5 classifies them as the same handler.", src:"run 20260908-0233 §4/5"}
    ],
    sources: ["https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent"],
    related: ["cloud-pos/catalog.md"]
  },
  "engine-sub-cycle-flow": {
    title: "Engine: DEC-012 sub-cycle flow",
    desc: "Knowledge about the self* engine's own operating model.",
    tldr: "Engineers run ONE at a time under a per-cycle 12h budget; unfinished tasks are 'half' with worktree+branch+session preserved; the marathon then runs small sub-cycles (N.1, N.2) that finish ONLY half-done work before QA/review/ship.",
    prose: "Hard-parking a run because one engineer task is slow turns transient slowness into a stop-the-world decision. Instead the engine records unfinished work as 'half' — keeping the branch, worktree and opencode session — and flows it into a follow-up sub-cycle, so progress stays monotonic and the product only manages boundary decisions. Never-started tasks roll forward to the next main cycle.",
    summary: "The engine's cycle flow: sequential engineers, per-cycle budget, half-done work resumed in sub-cycles.",
    facts: [
      ["Engineer concurrency", "max_parallel = 1 (sequential), per-task timeout_secs = 7200"],
      ["Per-cycle budget", "engineer.cycle_time_secs = 43200 (12h); on budget, remaining tasks roll to cycle N+1"],
      ["Sub-cycle resume", "active_ids = half_ids when the cycle key has a dot (e.g. '4.1')"],
      ["Ship gate", "each sub-cycle still runs QA → reviewer → ship on the completed delta"]
    ],
    findings: [
      {kf:"No park-on-timeout", body:"DEC-012 replaces 'timeout → park for product' with continuous flow: half-done work keeps its branch, worktree and opencode session so a sub-cycle resumes exactly where the engineer stopped.", src:"40-knowledge/decisions-log.md DEC-012"}
    ],
    sources: ["../../40-knowledge/decisions-log.md"],
    related: ["cloud-pos/index.md"]
  },
  "cloud-pos": {
    title: "Cloud POS",
    desc: "stdlib-only cloud point-of-sale: HTML cashiering, HK tax records, concurrent multi-station.",
    summary: "No product tag — grouped pages.",
    pages: {
      "index": {
        title: "Overview",
        desc: "A browser-first POS served by a stdlib Python HTTPServer + SQLite (WAL). Dock / undock lanes.",
        summary: "Any station on the LAN opens the register page, builds a multi-line sale from the item catalog, charges it atomically, and lands on an HTML receipt — all against one shared, concurrency-safe SQLite backend. Receipt numbering is sequential per year (2026-0001).",
        related: ["cloud-pos/auth-gate.md","cloud-pos/item-crud.md","cloud-pos/refunds.md","concurrency-sqlite/barcode-qr-scanning.md"]
      },
      "auth-gate": {
        title: "Auth gate",
        desc: "Every route except /login requires a session; uniform 303 redirect over the feature registry.",
        summary: "A single early check in POSHandler.do_GET/do_POST redirects 303 → /login for any unauthenticated request (except GET/POST /login). New feature routes inherit the gate automatically.",
        facts: [
          ["Cookie", "opaque session token in users/sessions table; HttpOnly + SameSite=Lax"],
          ["Roles", "seeded cashier + manager roles; POS_CASHIER_PASSWORD / POS_MANAGER_PASSWORD env"],
          ["Lifetime", "POS_SESSION_HOURS (default 12h)"]
        ],
        sources: ["https://owasp.org/www-community/controls/Session_Management_Cheat_Sheet"]
      },
      "item-crud": {
        title: "Item CRUD + optimistic locking",
        desc: "Edit / re-price / adjust / soft-delete items from any station with version-guarded writes.",
        summary: "POST /items/{id}/update|adjust|delete, each a guarded UPDATE ... WHERE id=? AND active=1 AND version=?; rowcount==0 ⇒ 409 (a competing station changed the row). Soft delete sets active=0; receipt line snapshots preserve history.",
        facts: [
          ["Routes", "POST /items/{id}/update (name,price), /adjust (signed qty), /delete (soft)"],
          ["409 guard", "version=version+1 in the same statement; no RETURNING (rowcount bug)"],
          ["Sync", "every successful mutation emits catalog.changed → SSE fan-out"]
        ],
        findings: [
          {kf:"Golden rule for guarded writes", body:"Bump version AND check it in ONE statement; rowcount==0 means stale → 409. Never check-then-update across two statements (TOCTOU).", src:"run 20260908-0233 §2"}
        ],
        sources: ["https://github.com/python/cpython/issues/93421","https://alexanderobregon.substack.com/p/optimistic-concurrency-with-sql-version"],
        related: ["cloud-pos/index.md","concurrency-sqlite/engine-sub-cycle-flow.md"]
      },
      "refunds": {
        title: "Refund flow",
        desc: "Refund referencing the original receipt; atomic stock re-credit with over-refund protection.",
        summary: "POST /refund inside ONE transaction: re-credit each sale line's stock (UPDATE items SET quantity=quantity+? WHERE id=?), insert a refunds row, and reject over-refund (SUM(refunds) > total) with 400 — the transaction sale row is never deleted. GET /refunds is a manager audit.",
        facts: [
          ["Table", "refunds(id, receipt_no, refund_cents, reason, refunded_by, created_at)"],
          ["Stock re-credit", "single guarded UPDATE per line from the transaction_lines snapshot"],
          ["Over-refund", "SUM(refunds.refund_cents) > transactions.total_cents ⇒ 400, nothing written"]
        ],
        findings: [
          {kf:"HK tax period report", body:"tax.py period totals: gross - refunded = net. Refunded sums come from the refunds table per receipt — the table must exist (ensure_refunds) so the report always runs.", src:"run 20260908-0233 tax feature"}
        ],
        related: ["cloud-pos/cashiering.md","cloud-pos/tax-hk.md"]
      },
      "cashiering": {
        title: "Cashiering (sale / receipt)",
        desc: "Multi-line ticket, atomic charge, sequential receipt, payment methods, charge flow.",
        summary: "GET / renders the register (catalog + current-sale ticket with item_id/quantity rows and a payment-method select). POST /charge records the sale atomically: stock check-and-decrement (never negative), sequential receipt {year}-{no:04d}, transaction + line inserts, then 303 → /receipts/{no}.",
        facts: [
          ["Payment methods", "cash, card, octopus, fps, alipayhk, wechatpayhk, payme, store-credit"],
          ["Receipt format", "{year}-{no:04d} e.g. 2026-0001, minted from receipt_sequences"],
          ["Snapshots", "line name/price snapshotted at sale time (history survives item edits/soft-delete)"]
        ],
        related: ["cloud-pos/refunds.md","cloud-pos/tax-hk.md"]
      },
      "tax-hk": {
        title: "HK tax record keeping (s.51C)",
        desc: "HTML report + printable receipt export for Inland Revenue record-keeping.",
        summary: "HK has no VAT/GST; the binding requirement is s.51C IRO Cap.112: keep sufficient records of income, expenditure and itemized receipts for ≥7 years. This module produces those as plain HTML: period report (per-receipt refunded sums, gross/refunded/net) and per-receipt export.",
        findings: [
          {kf:"No gov template", body:"Hong Kong has no government-mandated invoice template; the report carries store identity (POS_STORE_NAME/POS_BRN), sequential receipt number, itemized lines, payment reference and refund references.", src:"Engine research — HK tax"}
        ],
        sources: ["https://www.ird.gov.hk/eng/tax/ine/bus.htm"]
      }
    }
  }
};

// Latest updates feed (maintained by the librarian; newest first)
const LASTUPD = [
  {cyc:"run 20260908-0233", msg:"Wiki seeded from researcher findings (auth-gate, item-crud, refunds, coupons stubs, tax-hk, concurrency)."},
  {cyc:"DEC-012", msg:"engine-sub-cycle-flow page created from decisions-log entry."},
  {cyc:"initial", msg:"KNOWLEDGE/ skeleton: index, product tree, per-topic pages, sources, recent updates."}
];
