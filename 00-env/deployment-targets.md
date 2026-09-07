# Deployment Targets

Where the opencode web UI will actually run. **Decision pending (FU-002).**

| Option | Pros | Cons |
|---|---|---|
| dev-station only | fastest loop; no infra | phone can't reach it off-LAN |
| dgx-node-01 (192.168.1.202) | always-on; opencode servers already run there historically (s004 gdx); near the model gateway | shares RAM with vLLM stack — watch memory |
| dgx-node-02 (192.168.1.249) | always-on; lighter load | not the gateway host |
| VPS/relay (future) | phone-anywhere | cost + setup |

Follow-ups: FU-002 (which host), FU-006 (remote access path: LAN / Tailscale / tunnel).
