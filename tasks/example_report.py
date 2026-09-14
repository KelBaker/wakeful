"""Exemplo de tarefa com argumento. Troque pelo seu script real."""
import argparse
import sys
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

if args.verbose:
    print(f"[example_report] modo verbose, rodando em {datetime.now().isoformat()}")
else:
    print("[example_report] rodando")

sys.exit(0)
