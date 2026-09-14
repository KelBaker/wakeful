# wakeful

Agendador de tarefas para Windows feito pra rodar scripts Python — incluindo
automações de interface (Selenium, pyautogui) que precisam da sessão
**desbloqueada**, ao contrário do Task Scheduler nativo, que é ruim pra isso
e roda tarefas de serviço numa sessão isolada sem acesso ao desktop.

## Por que não o Task Scheduler nativo?

- Cron expressions completas em vez da UI limitada de gatilhos.
- Log centralizado por execução (stdout/stderr/exit code/duração), sem abrir
  o Event Viewer.
- Retry e timeout configuráveis por tarefa.
- Pensado desde o início pra rodar automação de UI numa máquina dedicada —
  ver [docs/windows-setup.md](docs/windows-setup.md) pra como deixar a
  máquina logada e sem travar.

## Instalação

```bash
pip install -e .
```

## Uso

```bash
cp config.example.yaml config.yaml
# edite config.yaml com suas tarefas
wakeful
```

`config.yaml` nunca deve ir pro controle de versão — veja `.gitignore`.

## Formato do config

```yaml
tasks:
  - name: backup-diario
    command: ["python", "tasks/example_backup.py"]
    cron: "0 3 * * *"      # minuto hora dia mes dia-da-semana
    timeout_seconds: 1800
    retries: 1
    working_dir: "."
```

## Rodando numa máquina dedicada 24/7

Se a tarefa precisa de sessão desktop desbloqueada (automação de interface),
leia [docs/windows-setup.md](docs/windows-setup.md) — a estratégia é
autologon no boot + nunca deixar a sessão travar, não "desbloquear depois
de travada" (que exigiria simular Ctrl+Alt+Del e digitar senha, frágil e
invasivo). Essa configuração assume uma máquina **dedicada**, sem uso
humano concorrente; não é recomendada numa máquina de uso misto.

## Status

Em desenvolvimento inicial. Roadmap:

- [x] Engine de agendamento (cron) + execução com timeout/retry
- [x] Log em arquivo
- [ ] Notificação de falha (webhook/email)
- [ ] Ícone na bandeja do sistema (pystray) com status das tarefas
- [ ] UI mínima pra cadastrar tarefas sem editar YAML

## Licença

MIT — veja [LICENSE](LICENSE).
