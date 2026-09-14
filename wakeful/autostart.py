"""Liga/desliga o wakeful iniciar sozinho no login do Windows.

Usa a pasta Startup do usuário (shell:startup) em vez de mexer no Task
Scheduler nativo ou no registro -- é o mecanismo mais simples de reverter
(é só apagar o .bat) e não exige privilégio de administrador.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _startup_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("Variável de ambiente APPDATA não encontrada (isso só funciona no Windows).")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _bat_path() -> Path:
    return _startup_dir() / "wakeful.bat"


def _exe_path() -> Path:
    # o entry point gui_scripts (wakeful-ui.exe) fica ao lado do python.exe
    # do mesmo venv/instalação que está rodando este processo agora
    return Path(sys.executable).parent / "wakeful-ui.exe"


def is_enabled() -> bool:
    return _bat_path().exists()


def enable() -> None:
    exe = _exe_path()
    if not exe.exists():
        raise FileNotFoundError(
            f"wakeful-ui.exe não encontrado em {exe} — rode 'pip install -e .' nesse ambiente antes."
        )
    _bat_path().write_text(f'start "" "{exe}"\n', encoding="utf-8")


def disable() -> None:
    _bat_path().unlink(missing_ok=True)
