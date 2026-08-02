#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_PROFILE = str(Path(__file__).resolve().parent / ".chrome-profile")


ENV_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")

ACOES_SUPORTADAS = frozenset(
    {
        "goto",
        "click",
        "fill",
        "type",
        "press",
        "check",
        "uncheck",
        "select",
        "wait",
        "screenshot",
        "print",
    }
)


def load_env(path=".env"):
    """Lê um .env simples (CHAVE=valor) sem sobrescrever o ambiente real."""
    env_file = Path(path)
    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def expand_env(value):
    """Troca ${VAR} pelo valor do ambiente, para que segredos fiquem fora do JSON."""
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.environ.get(match.group(1), match.group(0)), value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def load_steps(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        steps = data.get("steps")
    else:
        steps = data

    if not isinstance(steps, list):
        raise ValueError("O arquivo JSON precisa conter uma lista de passos ou {\"steps\": [...]}.")

    return expand_env(steps)


def resolve_url(url):
    """Local paths become file:// URLs so flows run on any machine."""
    if "://" in url:
        return url
    return Path(url).resolve().as_uri()


def text_selector(text):
    return f"text={text}"


def locator(page, step):
    if "selector" in step:
        found = page.locator(step["selector"])
    elif "label" in step:
        found = page.get_by_label(step["label"])
    elif "placeholder" in step:
        found = page.get_by_placeholder(step["placeholder"])
    elif "role" in step:
        found = page.get_by_role(step["role"], name=step.get("name"))
    elif "text" in step:
        found = page.locator(text_selector(step["text"]))
    else:
        raise ValueError("Passo precisa de selector, label, placeholder, role/name ou text.")

    if step.get("first"):
        return found.first
    if "nth" in step:
        return found.nth(int(step["nth"]))
    return found


def run_step(page, step, index):
    action = step.get("action")
    if not action:
        raise ValueError(f"Passo {index}: faltou action.")

    if action not in ACOES_SUPORTADAS:
        raise ValueError(f"Passo {index}: action desconhecida: {action}")

    timeout = step.get("timeout", 30000)

    if action == "goto":
        page.goto(resolve_url(step["url"]), wait_until=step.get("wait_until", "domcontentloaded"), timeout=timeout)
        return

    if action == "click":
        locator(page, step).click(timeout=timeout)
        return

    if action == "fill":
        locator(page, step).fill(str(step.get("value", "")), timeout=timeout)
        return

    if action == "type":
        locator(page, step).type(str(step.get("value", "")), delay=step.get("delay", 25), timeout=timeout)
        return

    if action == "press":
        target = locator(page, step) if any(key in step for key in ("selector", "label", "placeholder", "role", "text")) else page
        target.press(step["key"], timeout=timeout)
        return

    if action == "check":
        locator(page, step).check(timeout=timeout)
        return

    if action == "uncheck":
        locator(page, step).uncheck(timeout=timeout)
        return

    if action == "select":
        locator(page, step).select_option(step["value"], timeout=timeout)
        return

    if action == "wait":
        if "selector" in step or "text" in step or "label" in step or "placeholder" in step or "role" in step:
            locator(page, step).wait_for(state=step.get("state", "visible"), timeout=timeout)
        else:
            page.wait_for_timeout(int(step.get("ms", 1000)))
        return

    if action == "screenshot":
        output = step.get("path", "screenshot.png")
        page.screenshot(path=output, full_page=step.get("full_page", True))
        print(f"Screenshot salvo em: {output}")
        return

    if action == "print":
        value = step.get("value", "")
        if value == "title":
            print(page.title())
        elif value == "url":
            print(page.url)
        else:
            print(value)
        return

    raise ValueError(f"Passo {index}: action desconhecida: {action}")


def main():
    parser = argparse.ArgumentParser(description="Automacao simples do Chrome com Playwright.")
    parser.add_argument("arquivo", help="JSON com os passos da automacao.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help=f"Perfil do Chrome. Padrao: {DEFAULT_PROFILE}")
    parser.add_argument("--headless", action="store_true", help="Executa sem abrir janela.")
    parser.add_argument("--slow", type=int, default=150, help="Pausa entre acoes em ms. Padrao: 150.")
    parser.add_argument("--keep-open", action="store_true", help="Mantem o Chrome aberto ao terminar.")
    args = parser.parse_args()

    load_env()
    if args.profile == DEFAULT_PROFILE:
        args.profile = os.environ.get("BROWSER_FLOW_PROFILE") or DEFAULT_PROFILE

    steps = load_steps(args.arquivo)
    Path(args.profile).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=args.profile,
            channel="chrome",
            headless=args.headless,
            slow_mo=args.slow,
            viewport={"width": 1366, "height": 768},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            for index, step in enumerate(steps, start=1):
                print(f"{index}. {step.get('action')}")
                run_step(page, step, index)
        except PlaywrightTimeoutError as exc:
            print(f"Tempo esgotado no passo {index}: {step}", file=sys.stderr)
            print(exc, file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"Erro no passo {index}: {step}", file=sys.stderr)
            print(exc, file=sys.stderr)
            return 1
        finally:
            if args.keep_open and not args.headless:
                input("Automacao finalizada. Pressione ENTER para fechar o Chrome...")
            context.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
