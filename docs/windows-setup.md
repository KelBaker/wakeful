# Configurando a máquina Windows dedicada

O `wakeful` roda como processo comum na sessão do usuário logado — de propósito,
**não** como Windows Service. Um serviço roda isolado na Session 0 (Session 0
isolation, desde o Windows Vista) e não tem acesso à área de trabalho, então
não consegue rodar automação de interface (Selenium com browser visível,
pyautogui, etc). Precisa ser um processo na sessão interativa.

Isso significa que a máquina precisa: (1) logar sozinha no boot e (2) nunca
travar a sessão depois disso. Os dois passos abaixo resolvem isso — pensados
pra uma **máquina dedicada**, sem uso humano concorrente. Numa máquina de uso
misto essa configuração não é recomendada (ver discussão no README).

## 1. Autologon no boot

Não edite a chave de registro `DefaultPassword` na mão — ela fica em texto
plano, legível por qualquer processo com acesso ao registro. Use o
[Autologon da Sysinternals](https://learn.microsoft.com/sysinternals/downloads/autologon):
ele guarda a senha criptografada via LSA secrets.

```
Autologon.exe <usuario> <dominio_ou_.> <senha>
```

Rode como administrador. Reinicie e confirme que a máquina sobe direto no
desktop sem pedir senha.

## 2. Nunca deixar a sessão travar

Autologon só ajuda no boot — não desbloqueia uma sessão já travada por
inatividade ou Win+L. A solução é impedir que ela trave:

- **Energia**: nunca dormir, nunca desligar tela com trava associada.
  ```
  powercfg /change standby-timeout-ac 0
  powercfg /change monitor-timeout-ac 0
  ```
- **Screensaver**: desabilite e garanta que não exige senha ao voltar
  (`HKCU\Control Panel\Desktop\ScreenSaveActive = 0`).
- **Se você acessa a máquina via RDP** pra manutenção: por padrão, ao
  desconectar do RDP a sessão do console fica travada, o que reintroduz o
  mesmo problema. Prefira reconectar a sessão do console em vez de deixá-la
  travada (`tscon`), ou evite depender de RDP pra essa máquina.

## 3. Subir o wakeful automaticamente

Coloque um atalho pra `wakeful` (ou `python -m wakeful`) na pasta Startup do
usuário:

```
shell:startup
```

Ou registre uma tarefa no Task Scheduler nativo com o gatilho "at log on",
opção "run only when user is logged on" — nesse uso o Task Scheduler nativo
serve bem, ele só não serve como *scheduler de tarefas recorrentes com
interface decente*, que é o que o wakeful resolve por cima.
