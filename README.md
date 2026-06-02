# Chunkify

A small, modern desktop utility to split large files into numbered chunks and reassemble them.

## Key features

- Split a single file into `_partNNN` chunk files.
- Merge selected chunk files back into one file (sorted by part number).
- Batch "Auto Split" and "Auto Merge" operations across directories.
- Live operation output panel with copy-to-clipboard.
- Light / Dark theme and responsive layout.

## Requirements

- Python 3.11+ (3.14 tested)
- PyQt5

## Install dependencies

Open PowerShell and run:

```powershell
python -m pip install pyqt5 pyinstaller
```

## Run the app (development)

From the project folder:

```powershell
python .\main.py
```

## Build a Windows executable

The project includes `main.spec` configured to embed `favicon.ico` and produce a single EXE named `Chunkify.exe`.

Build with PyInstaller:

```powershell
python -m PyInstaller main.spec
```

When the build completes, the standalone executable will be in:

```
dist\Chunkify.exe
```

Notes:
- The spec bundles `favicon.ico` so the running window and the exe contain the app icon.

## Project layout

- `main.py` — application entry point and resource loader
- `ui.py` — PyQt5 UI and layout
- `core.py` — file chunking/merging logic
- `main.spec` — PyInstaller spec used to build the EXE
- `favicon.ico` — app icon (embedded into the EXE)

## Quick usage

Split a file:

1. Open the `Split File` tab.
2. Drag a file into the drop area or click `Browse`.
3. (Optional) Set output directory and chunk size.
4. Click `Split File`.

Merge chunks:

1. Open the `Merge Files` tab.
2. Add chunk files (drag-drop or `Add Chunks...`).
3. Set the output filename and directory.
4. Click `Merge Files`.

Auto operations:

1. Open `Auto Operations` tab.
2. Select a directory (drag-drop supported).
3. Use `Auto Split Large Files` or `Auto Merge Chunks`.

## Troubleshooting

- If the GUI fails to start, ensure `PyQt5` is installed and you are using a compatible Python version.
- If the exe does not show the icon, rebuild with `python -m PyInstaller main.spec` — the spec includes the icon as bundled data.

---

If you'd like, I can also:

- Add a short GIF or screenshots showing the UI flow.
- Create a `requirements.txt` and a simple install script.
- Add CLI helpers for scripted batch operations.
