# ChunkFlow

A clean, minimal desktop tool for splitting large files into chunks and merging them back together.

## Features

- Split a single file into numbered chunk files.
- Merge selected chunk files back into a single file.
- Auto split all large files in a directory.
- Auto merge detected chunk groups in a directory.
- Output log panel with detailed results and copy-to-clipboard support.
- Light/Dark theme toggle with a simple minimal UI.

## Getting Started

### Prerequisites

- Python 3.11+ (3.14 tested)
- PyQt5

### Install dependencies

```powershell
cd "d:\PythonScripts\GitTools\UAssetChunkify\Chunckify With UI"
python -m pip install pyqt5
```

### Run the app

```powershell
python .\main.py
```

## Build a Windows executable

This project already includes a `main.spec` file.

```powershell
cd "d:\PythonScripts\GitTools\UAssetChunkify\Chunckify With UI"
python -m pip install pyinstaller
python -m PyInstaller main.spec
```

After building, the generated executable is available in the `dist` folder as `main.exe`.

## Project Structure

- `main.py` — application entry point
- `ui.py` — PyQt5 user interface logic
- `core.py` — file chunking and merging functionality
- `main.spec` — PyInstaller build configuration
- `favicon.ico` — application icon asset

## How to Use

### Split File
1. Open the `Split File` tab.
2. Choose a source file.
3. Optionally choose an output directory.
4. Set the chunk size in MB.
5. Click `Split File`.

### Merge Files
1. Open the `Merge Files` tab.
2. Enter or browse for the output file path.
3. Add chunk files to merge.
4. Click `Merge Files`.

### Auto Operations
1. Open the `Auto Operations` tab.
2. Choose a directory.
3. Optionally choose an output directory.
4. Use `Auto Split Large Files` or `Auto Merge Chunks`.

## Notes

- The app preserves original file structure when an output directory is provided.
- Chunks are named using a `_partNNN` suffix, and merge order is determined by that number.
- Successful operations display a simple popup, and full details appear in the output panel.

## Suggestions

If you want, I can also add:

- drag-and-drop support for file selection
- an option to set a custom chunk filename pattern
- a `Clear output` button or recent operation history
