# Previewing

## CLI

Use the canonical launcher:

```bash
budgetwars --mode classic
budgetwars --mode desktop
```

Dedicated entry points are also available:

```bash
budgetwars-classic
budgetwars-desktop
```

## Windows Preview Scripts

Repo-root preview launchers:

```bat
live_preview.bat
live_preview_classic.bat
live_preview_desktop.bat
```

Behavior:
- prefer `.venv\Scripts\python.exe`
- then scan `%LocalAppData%\Programs\Python\Python*`
- then fall back to `python`
- fail clearly if Python is unavailable
- pass through extra CLI args

Examples:

```bat
live_preview_classic.bat --seed 42
live_preview_desktop.bat --load autosave.json
```

`live_preview.bat` defaults to Classic mode.

## macOS Preview Scripts

Repo-root double-click launchers:

```bash
open_classic.command
open_desktop.command
```

Behavior:
- prefer `.venv/bin/python`
- then fall back to `python3`
- then fall back to `python`
- fail clearly if Python is unavailable
- bootstrap `.venv` and install runtime deps if needed
- pass through extra CLI args

Examples:

```bash
./open_classic.command --seed 42
./open_desktop.command --load autosave.json
```
