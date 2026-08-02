# browser-flow

[![tests](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml/badge.svg)](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml)
[![python](https://img.shields.io/badge/python-3.9%20%7C%203.11%20%7C%203.12-blue)](https://github.com/engdesoftwareg/browser-flow/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Versão em português](README.pt-BR.md)

Browser automation written as **JSON**, not as code. Describe the steps in a file, run one command, Chrome does the rest.

```bash
python3 browser_flow.py flows/form.json
```

## Problem

Repetitive browser work — open a site, fill in the same form, check that it went through, save the receipt as an image — eats minutes every day and goes wrong when the person doing it is tired.

Writing a Playwright script per task solves that but creates a new problem: whoever doesn't code can't change anything, and every routine becomes one more `.py` file to maintain.

## Solution

A single generic runner. Each routine becomes a readable JSON file that anyone on the team can edit:

```json
{
  "steps": [
    { "action": "goto", "url": "https://example.com/signup" },
    { "action": "fill", "label": "Nome", "value": "Maria" },
    { "action": "fill", "placeholder": "Email", "value": "maria@example.com" },
    { "action": "check", "label": "Aceito os termos" },
    { "action": "click", "role": "button", "name": "Enviar" },
    { "action": "wait", "selector": "#resultado", "state": "visible" },
    { "action": "screenshot", "path": "receipt.png" }
  ]
}
```

Design decisions worth mentioning:

- **Elements by label, not by brittle CSS.** `label`, `placeholder` and `role`/`name` survive layout changes; `#form > div:nth-child(3) > input` does not.
- **Secrets never in the JSON.** Write `${SITE_PASSWORD}` in the flow and the value comes from the environment or from `.env` — which is in `.gitignore`.
- **Persistent profile.** The session lives in `.chrome-profile/` (also git-ignored), so you log in once and later flows start already authenticated.
- **Failures with an address.** On error it prints the number and the exact content of the step that broke, and exits with code `1` (error) or `2` (timeout) — usable from `cron` and from CI.

### Available actions

`goto` · `click` · `fill` · `type` · `press` · `check` · `uncheck` · `select` · `wait` · `screenshot` · `print`

## Running it

```bash
git clone https://github.com/engdesoftwareg/browser-flow.git
cd browser-flow

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chrome

cp .env.example .env          # optional, only if your flows use ${VAR}

python3 browser_flow.py flows/form.json          # local demo, opens Chrome
python3 browser_flow.py flows/form.json --headless
```

Options: `--headless` · `--slow 150` (pause between actions, in ms) · `--keep-open` · `--profile PATH`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

**14 tests** that never open a browser — they run in ~0.1 s and cover `${VAR}` expansion, `.env` loading (which must never override the real environment), step format validation and URL resolution. A parametrized test walks every JSON in `flows/` and fails if one uses a non-existent action, so a broken example can't slip through.

CI runs on **Python 3.9, 3.11 and 3.12** for every push and pull request.

## Result

The demo flow (`flows/form.json`) runs **8 steps — navigate, fill 2 fields, select, tick a checkbox, submit, wait for confirmation and save a screenshot — in 2.8 s** headless, and produces `form.png` as proof of the run.

The same routine done by hand takes a few minutes and depends on someone remembering to save the evidence. Here it runs on its own, always the same way, and can be scheduled with `cron`.

## License

MIT
