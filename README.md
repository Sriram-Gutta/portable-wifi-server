# Portable Wireless Network Server

A standalone Wi-Fi access point + HTTP server running on the **Raspberry Pi Pico W / Pico 2W**. The board hosts its own wireless network — no router, no external internet — and serves a small interactive web page that clients can reach by joining the AP and visiting the Pico's IP.

This repo contains **two implementations of the same project**:

| Implementation | Language | Path |
|---|---|---|
| Bare-metal, lwIP-based | Embedded C/C++ | [`c-sdk/`](c-sdk/) |
| Higher-level, rapid prototype | MicroPython | [`micropython/`](micropython/) |

The C version is built against the official Pico SDK + lwIP; the MicroPython version uses the `network` and `socket` modules. Both expose the same UX: connect to the `PicoW_Server` SSID, open the IP in a browser, and you get a control page.

## What it does

- **Brings up a Wi-Fi AP** with WPA2 (SSID `PicoW_Server`, password `12345678` — change these before deploying).
- **Hosts an HTTP server on port 80** that responds with a small HTML control panel.
- **Toggles the onboard LED** from the browser (`/lighton`, `/lightoff`).
- **Reads the RP2040/RP2350 internal temperature sensor** via ADC channel 4 and displays it on the page.
- **Shuts the server down cleanly** from the browser (`/close`).
- **Serves PDF files to clients** (MicroPython version): the `/pdf/<filename>` route streams a PDF from the Pico's filesystem in 1 KB chunks. The C version has the UI hooks for media slots but does not yet read from flash.

## Hardware

- Raspberry Pi Pico W or Pico 2W (any board with the CYW43 Wi-Fi chip)
- USB cable for power and flashing
- That's it — no shield, no external network

## Repo layout

```
portable-wifi-server/
├── c-sdk/                       # C implementation (Pico SDK + lwIP)
│   ├── Portable_Wifi_Server.c   # AP setup, TCP server, HTTP handlers
│   ├── CMakeLists.txt           # Build config (links pico_cyw43_arch_lwip_poll, hardware_adc)
│   ├── lwipopts.h               # Trimmed lwIP options for the Pico
│   └── pico_sdk_import.cmake
├── micropython/                 # MicroPython implementation
│   ├── web_server.py            # AP, socket server, request routing
│   └── tools.py                 # Internal temperature sensor helper
├── LICENSE
└── README.md
```

## Building & flashing — C version

Requires the [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk) and an ARM toolchain. The included `CMakeLists.txt` and `pico_sdk_import.cmake` are set up for the Pico VS Code extension, but plain CMake works too.

```bash
cd c-sdk
mkdir build && cd build
cmake -DPICO_BOARD=pico_w ..      # or pico2_w for the Pico 2W
make -j
```

Hold `BOOTSEL` while plugging in the Pico, then copy the resulting `Portable_Wifi_Server.uf2` onto the `RPI-RP2` drive that appears.

## Running — MicroPython version

1. Flash the [official MicroPython firmware for Pico W / Pico 2W](https://micropython.org/download/) using BOOTSEL + drag-and-drop.
2. Copy both files in [`micropython/`](micropython/) to the board (Thonny → File → Save to Pico, or `mpremote`):
   ```
   web_server.py
   tools.py
   ```
3. Run `web_server.py`. The Pico prints `AP up at http://192.168.4.1`.

## Using it

1. On your phone or laptop, join the Wi-Fi network **`PicoW_Server`** (password `12345678`).
2. Open a browser to `http://192.168.4.1`.
3. You'll see the control panel: LED on/off, the live temperature reading, and shutdown.

## Notes on the design

- **lwIP in `NO_SYS` mode.** The C version uses `pico_cyw43_arch_lwip_poll`, so the main loop calls `cyw43_arch_poll()` instead of relying on an RTOS. `lwipopts.h` strips lwIP down to just IPv4 + TCP + UDP + ICMP to keep the footprint small.
- **Static HTML, formatted in C with `snprintf`.** No template engine — the page is a single string with `%s` / `%.2f` placeholders for LED state and temperature.
- **MicroPython version uses blocking `socket.accept()`** in a `while True` loop. Simple, and fine for a single client at a time, which is the realistic use case for a portable AP.
- **Temperature** comes from ADC channel 4 (the internal silicon sensor) using the datasheet's standard `27 - (V - 0.706) / 0.001721` formula.

## License

MIT — see [LICENSE](LICENSE).
