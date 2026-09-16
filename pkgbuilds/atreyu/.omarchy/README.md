# atreyu

Installs the prebuilt Atreyu plugin tree from the `atreyu-{pkgver}-linux-x86_64.tar.gz` GitHub release asset into `/usr/share/omarchy/plugins/omarchy.atreyu/` (the directory name is the plugin id the shell scans for, not the package name), plus `LICENSE` and `THIRD_PARTY_NOTICES.md` under `/usr/share/licenses/atreyu/`. No install hook: Omarchy restarts the shell after `omarchy update`, and nothing here may write into a user home.

`options=('!strip' '!debug')` is load-bearing. `runtime/dist/atreyu-broker` and `runtime/dist/adapters/codex-acp` are static x86-64 ELF stubs with no section headers whose JavaScript payload sits after the code (see upstream `runtime/launcher/embedded-node-launcher.mjs`); they `execve("/usr/bin/env", "node", ...)`, so strip would corrupt them and there are no debug symbols to split.

Dependencies, cited as `file: tool` in the upstream tree:

- `nodejs>=22`: `runtime/launcher/embedded-node-launcher.mjs: node` (both launchers), `package.json: engines.node >=22`.
- `omarchy`: `*.qml: import qs.Commons / qs.Ui`; `scripts/install-hotkeys.sh`, `scripts/manage-voice-escape.sh: omarchy-shell`; `runtime/src/tools/desktop.ts`, `web-handoff.ts`, `pi-harness.ts: omarchy`; owns `/usr/share/omarchy`.
- `quickshell`: `*.qml: import Quickshell{,.Io,.Wayland,.Hyprland,.Services.Mpris}`.
- `hyprland`: `scripts/manage-voice-escape.sh: hyprctl` (required), `runtime/src/tools/desktop.ts`, `context-attachments.ts`, `herdr.ts: hyprctl`.
- `jq`: `scripts/manage-voice-escape.sh: jq` (required), `scripts/install-browser-companion.sh: jq`.
- `util-linux`: `scripts/install-hotkeys.sh: flock` (required).
- `imagemagick`: `runtime/src/images.ts: magick` (every stored image is normalized through it, so image handling fails outright without it).
- Optional, one feature each and probed before use: `grim` (`runtime/src/context-attachments.ts: grim`, screen capture), `wl-clipboard` (`runtime/src/broker.ts`, `tools/web-handoff.ts: wl-copy`, Copy action), `xdg-utils` (`runtime/src/broker.ts: xdg-open`, links), `uwsm` + `gtk3` (`runtime/src/tools/desktop.ts: uwsm-app -- gtk-launch`, app_open tool). All four ship in the Omarchy base install anyway; they are optdepends so `depends` states what the plugin needs to load, matching upstream `docs/delivery.md`. Also optional: `voxtype` (`runtime/src/dictation.ts`, `voxtype-vocabulary.ts`), `herdr` (`runtime/src/herdr.ts`), `tesseract` (`context-attachments.ts`), `libpulse` (`audio-devices.ts: pactl`), `pipewire-audio` (`tts.ts: pw-play`; the `pw-metadata` in `audio-devices.ts` is in `pipewire`, already an `omarchy` dependency), `ffmpeg` (`tts.ts`, metering only), `espeak-ng` (Kokoro TTS per upstream README), `openai-codex`/`opencode` (`providers.ts` ACP harnesses), `lua` (`scripts/install-hotkeys.sh: luac`, optional syntax check). Each is probed with `resolveExecutable` or `command -v` and degrades with a message when absent.

Release tracking: `bin/sync-upstream` follows `omacom/atreyu` GitHub releases (`vX.Y.Z`), reads the tarball digest from the `SHA256SUMS` asset, and rewrites `pkgver` and `sha256sums_x86_64`. The `x86_64` asset key maps to the arch-suffixed arrays, hence `source_x86_64`. `min_release_age: 24h` holds a fresh release for a day; `release_ring: fast` builds it straight to stable as well as edge.
