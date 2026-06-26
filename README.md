# Streamify

Streamify is a lightweight, resource-efficient desktop frontend for watching live streams on Linux. It interacts directly with Streamlink and embeds the MPV media player natively into a PyQt5 window, bypassing the heavy CPU and memory overhead of modern web browsers.

---

## What We Currently Have

* **Lightweight Memory Footprint**: Uses only ~176 MB of RAM on startup and ~500 MB while streaming (including live video decoding), a fraction of what standard web browsers or Electron-based apps consume.
* **Native Player Embedding**: Embeds the `mpv` player directly inside the PyQt5 application container using OS window ID mapping (`--wid`).
* **Multi-threaded Status Checker**: Checks stream statuses in parallel using a fast, background thread pool (`concurrent.futures`) with clean UI progress integration.
* **Auto-Resetting Process Monitor**: Monitors active stream processes and resets launcher buttons automatically if the stream window is closed.
* **Dynamic Auto-Hiding Sidebar**: A hover-sensitive toggle bar that shrinks to a 3px strip when the sidebar is collapsed, providing an uninhibited, borderless view of your stream.
* **On-the-Fly Theme Toggle**: Quick switcher button (☀️/🌙) that dynamically restyles the entire application between Dark and Light mode without requiring a restart.
* **Stream & Category Management**: Clean dialogs for adding or deleting streams, custom platforms (URLs), and managing filtering categories.

---

## Future Features and Tasks

### Milestone 1: Core Streamlink & Playback UX
- [ ] **Dynamic Quality Detection**: Query the Streamlink API in real-time when selecting a channel to populate the quality dropdown with actual active stream options (e.g., `1080p60`, `720p60`, `audio_only`) instead of using hardcoded fallbacks.
- [ ] **Native MPV Key Bindings & Hotkeys**: Capture window key events to control the embedded media player natively (e.g., Space to pause, M to mute, Up/Down for volume adjustments).
- [ ] **Custom MPV Flags configuration**: Implement a lightweight local configuration file to pass custom flags directly to the embedded MPV process (such as forcing hardware GPU acceleration via `--hwdec=auto`).

### Milestone 2: Native Chat & Account Integration
- [ ] **Native IRC Twitch Chat**: Connect directly to Twitch's chat backend using lightweight WebSockets (IRC over WS) to display chat messages in a collapsible side panel, avoiding heavy web-view browser engines.
- [ ] **Twitch API Integration**: Implement Twitch Helix API calls (OAuth2 authentication) to allow users to securely import their list of followed channels and automatically populate the sidebar.

### Milestone 3: Desktop Integration & Background Alerts
- [ ] **Minimize to System Tray**: Add a native PyQt system tray utility to run quietly in the background when closed.
- [ ] **Desktop Notifications**: Implement a periodic background timer to monitor favorite streams and trigger a native Linux desktop notification immediately when a tracked streamer goes live.

### Milestone 4: Code Quality & Repository Packaging
- [X] **Refactor & Modularize Code**: Split the monolithic single-file script into a clean, structured package (e.g., `main.py`, `backend.py`, `ui.py`, and `styles.py`).
- [X] **Linux Desktop Launcher**: Create a standard Linux `.desktop` launcher file and application icon.
- [X] **Standard Python Packaging**: Set up a modern `pyproject.toml` file with proper dependency tracking.
- [ ] **Target Package Repositories**: Create and submit templates for packaging systems, with a primary focus on Void Linux's `xbps-packages` repository.

---
