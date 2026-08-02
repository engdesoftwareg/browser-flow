# browser-flow

Automação de navegador escrita como **JSON**, não como código. Descreva os passos em um arquivo, rode um comando, o Chrome faz o resto.

```bash
python3 browser_flow.py flows/form.json
```

## Problema

Tarefas repetitivas no navegador — abrir um site, preencher o mesmo formulário, conferir se apareceu, salvar o comprovante em imagem — consomem minutos todo dia e erram quando a pessoa está cansada.

Escrever um script Playwright para cada tarefa resolve, mas cria um problema novo: quem não programa não consegue alterar nada, e cada rotina vira mais um arquivo `.py` para manter.

## Solução

Um único executor genérico. Cada rotina passa a ser um JSON legível, que qualquer pessoa da equipe consegue ler e editar:

```json
{
  "steps": [
    { "action": "goto", "url": "https://example.com/cadastro" },
    { "action": "fill", "label": "Nome", "value": "Maria" },
    { "action": "fill", "placeholder": "Email", "value": "maria@exemplo.com" },
    { "action": "check", "label": "Aceito os termos" },
    { "action": "click", "role": "button", "name": "Enviar" },
    { "action": "wait", "selector": "#resultado", "state": "visible" },
    { "action": "screenshot", "path": "comprovante.png" }
  ]
}
```

Decisões de projeto que valem citar:

- **Elementos por rótulo, não por CSS frágil.** `label`, `placeholder` e `role`/`name` sobrevivem a mudanças de layout; `#form > div:nth-child(3) > input` não.
- **Segredo nunca no JSON.** Escreva `${SITE_PASSWORD}` no fluxo e o valor vem do ambiente ou do `.env` — que está no `.gitignore`.
- **Perfil persistente.** A sessão fica em `.chrome-profile/` (também ignorado pelo Git), então você loga uma vez e os fluxos seguintes já entram autenticados.
- **Falha com endereço.** Ao dar erro, o programa imprime o número e o conteúdo exato do passo que quebrou, e sai com código `1` (erro) ou `2` (timeout) — dá para usar em `cron` e em CI.

### Ações disponíveis

`goto` · `click` · `fill` · `type` · `press` · `check` · `uncheck` · `select` · `wait` · `screenshot` · `print`

## Como rodar

```bash
git clone https://github.com/engdesoftwareg/browser-flow.git
cd browser-flow

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chrome

cp .env.example .env          # opcional, só se seus fluxos usarem ${VAR}

python3 browser_flow.py flows/form.json          # demo local, abre o Chrome
python3 browser_flow.py flows/form.json --headless   # sem janela
```

Opções: `--headless` (sem janela) · `--slow 150` (pausa entre ações, em ms) · `--keep-open` (mantém o Chrome aberto no fim) · `--profile CAMINHO`.

## Resultado

O fluxo de demonstração (`flows/form.json`) executa **8 passos — navegar, preencher 2 campos, selecionar, marcar checkbox, enviar, aguardar confirmação e salvar screenshot — em 2,8 s** em modo headless, e entrega o `form.png` como comprovante da execução.

A mesma rotina feita à mão leva alguns minutos e depende de alguém lembrar de salvar a evidência. Aqui ela roda sozinha, sempre igual, e pode ser agendada no `cron`.

## Licença

MIT
