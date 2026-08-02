# browser-flow

[![tests](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml/badge.svg)](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml)
[![python](https://img.shields.io/badge/python-3.9%20%7C%203.11%20%7C%203.12-blue)](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English version](README.md)

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

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

São **14 testes** que não abrem navegador — rodam em ~0,1 s e cobrem a expansão de `${VAR}`, a leitura do `.env` (que nunca sobrescreve o ambiente real), a validação do formato dos passos e a resolução de URLs. Um teste parametrizado percorre todos os JSONs de `flows/` e falha se algum usar uma ação inexistente, então exemplo quebrado não passa despercebido.

O CI roda em **Python 3.9, 3.11 e 3.12** a cada push e pull request.

## Resultado

O fluxo de demonstração (`flows/form.json`) executa **8 passos — navegar, preencher 2 campos, selecionar, marcar checkbox, enviar, aguardar confirmação e salvar screenshot — em 2,8 s** em modo headless, e entrega o `form.png` como comprovante da execução.

A mesma rotina feita à mão leva alguns minutos e depende de alguém lembrar de salvar a evidência. Aqui ela roda sozinha, sempre igual, e pode ser agendada no `cron`.

## Licença

MIT
