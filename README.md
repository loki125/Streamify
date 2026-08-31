# Streamify

Streamify is a lightweight, resource-efficient desktop frontend for watching live streams on Linux. It interacts directly with Streamlink and embeds the MPV media player natively into a PyQt5 window, bypassing the heavy CPU and memory overhead of modern web browsers.

---

## Backend

### 1. Streamlink Manager
> Manages the Streamlink API and communicates with the UI.

- [ ] Init & start Streamlink session
- [ ] Select player
- [ ] Twitch integration
- [ ] Check status
- [ ] Launch / stop stream

---

### 2. StreamDB
> Local database to store and track followed streams.

- [x] Init JSON file
- [x] Add / remove stream
- [x] Add / remove category
- [x] Search stream

```json
{
  "streams": [
    {
      "name": "",
      "url": "",
      "category": [],
      "live": false
    }
  ],
  "categories": []
}
```

---

### 3. Twitch Integration
> Handles developer API keys and logic for extracting follow lists.

- [ ] Init Twitch sign-in flow
- [ ] Fetch follow list

---

### 4. Player Configuration
> Player selection and custom keybind settings.

- [ ] Init settings JSON
- [ ] Load settings
- [ ] Set player

```json
{
  "player": "",
  "chat_active": false,
  "pause_start_key": "",
  "mute_unmute_key": "",
  "volume_num": 0,
  "default_quality": ""
}
```

---

## UI
- [ ] Main window layout (PyQt5)
- [ ] Stream list & category selector
- [ ] Embedded MPV player widget
