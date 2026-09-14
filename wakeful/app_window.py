"""Entry point `wakeful-ui`: sobe a API FastAPI numa thread e abre como janela nativa.

O servidor HTTP só escuta em 127.0.0.1 — não é exposto na rede, é só o
transporte entre o backend Python e a janela (pywebview usa um WebView do
próprio Windows, não abre navegador).
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading

import uvicorn
import webview

from wakeful.runtime import Runtime
from wakeful.web.api import create_app

logger = logging.getLogger("wakeful.ui")

HOST = "127.0.0.1"
PORT = 8756


def main() -> None:
    parser = argparse.ArgumentParser(prog="wakeful-ui")
    parser.add_argument("-c", "--config", default="config.yaml")
    args = parser.parse_args()

    try:
        runtime = Runtime(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro no config: {exc}", file=sys.stderr)
        sys.exit(1)

    runtime.start()
    app = create_app(runtime)

    server_config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(server_config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    window = webview.create_window(
        "wakeful", f"http://{HOST}:{PORT}", width=980, height=680, min_size=(640, 420),
        transparent=True,  # deixa o fundo da webview transparente pro Mica/Acrylic aparecer atras
    )
    webview.start(_apply_windows_acrylic, window)

    # janela fechada -> encerra scheduler e servidor junto
    runtime.shutdown()
    server.should_exit = True


def _apply_windows_acrylic(window) -> None:
    """Aplica o efeito Mica/Acrylic nativo do Windows na janela, se disponivel.

    So funciona no Windows 10/11 com a lib pywinstyles instalada -- em outro
    SO (ou se a lib nao estiver presente) cai silenciosamente pro fundo solido
    definido no CSS, sem quebrar o app.
    """
    try:
        import pywinstyles

        pywinstyles.apply_style(window, "mica")
    except Exception:
        logger.info("Efeito Mica/Acrylic indisponivel (fora do Windows ou lib ausente) -- usando fundo solido.")


if __name__ == "__main__":
    main()
