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
