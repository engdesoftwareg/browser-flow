import json
from pathlib import Path

import pytest

import browser_flow


# --- expansão de variáveis de ambiente --------------------------------------

def test_expand_env_substitui_variavel(monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", "segredo123")
    assert browser_flow.expand_env("${SITE_PASSWORD}") == "segredo123"


def test_expand_env_percorre_estruturas_aninhadas(monkeypatch):
    monkeypatch.setenv("SITE_USER", "maria")
    passos = [{"action": "fill", "value": "${SITE_USER}", "meta": {"tags": ["${SITE_USER}"]}}]

    resultado = browser_flow.expand_env(passos)

    assert resultado[0]["value"] == "maria"
    assert resultado[0]["meta"]["tags"] == ["maria"]


def test_expand_env_mantem_placeholder_quando_variavel_nao_existe(monkeypatch):
    monkeypatch.delenv("VARIAVEL_INEXISTENTE", raising=False)
    assert browser_flow.expand_env("${VARIAVEL_INEXISTENTE}") == "${VARIAVEL_INEXISTENTE}"


def test_expand_env_preserva_tipos_nao_textuais():
    assert browser_flow.expand_env({"timeout": 5000, "full_page": True}) == {
        "timeout": 5000,
        "full_page": True,
    }


# --- leitura do .env ---------------------------------------------------------

def test_load_env_nao_sobrescreve_ambiente_existente(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comentario\nSITE_USER=do_arquivo\nSITE_PASSWORD=do_arquivo\n\n", encoding="utf-8")
    monkeypatch.setenv("SITE_USER", "ja_definido")
    monkeypatch.delenv("SITE_PASSWORD", raising=False)

    browser_flow.load_env(env)

    import os

    assert os.environ["SITE_USER"] == "ja_definido"
    assert os.environ["SITE_PASSWORD"] == "do_arquivo"


def test_load_env_ignora_arquivo_ausente(tmp_path):
    browser_flow.load_env(tmp_path / "nao_existe.env")  # não deve levantar


# --- carga dos passos --------------------------------------------------------

def test_load_steps_aceita_lista_e_objeto_com_steps(tmp_path):
    como_lista = tmp_path / "lista.json"
    como_lista.write_text(json.dumps([{"action": "goto", "url": "https://example.com"}]), encoding="utf-8")
    como_objeto = tmp_path / "objeto.json"
    como_objeto.write_text(
        json.dumps({"steps": [{"action": "goto", "url": "https://example.com"}]}), encoding="utf-8"
    )

    assert browser_flow.load_steps(como_lista) == browser_flow.load_steps(como_objeto)


def test_load_steps_rejeita_formato_invalido(tmp_path):
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text(json.dumps({"passos": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="lista de passos"):
        browser_flow.load_steps(arquivo)


# --- resolução de URL --------------------------------------------------------

def test_resolve_url_mantem_enderecos_absolutos():
    assert browser_flow.resolve_url("https://example.com") == "https://example.com"


def test_resolve_url_converte_caminho_local_em_file_uri(tmp_path, monkeypatch):
    pagina = tmp_path / "pagina.html"
    pagina.write_text("<h1>ok</h1>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert browser_flow.resolve_url("pagina.html") == pagina.as_uri()


# --- os fluxos versionados continuam válidos ---------------------------------

@pytest.mark.parametrize("fluxo", sorted((Path(__file__).parent.parent / "flows").glob("*.json")))
def test_fluxos_de_exemplo_sao_validos(fluxo):
    passos = browser_flow.load_steps(fluxo)

    assert passos, f"{fluxo.name} está vazio"
    for passo in passos:
        assert passo.get("action") in browser_flow.ACOES_SUPORTADAS, passo


# --- execução de passo -------------------------------------------------------

def test_run_step_exige_action():
    with pytest.raises(ValueError, match="faltou action"):
        browser_flow.run_step(page=None, step={"url": "https://example.com"}, index=1)


def test_run_step_rejeita_action_desconhecida():
    with pytest.raises(ValueError, match="action desconhecida"):
        browser_flow.run_step(page=None, step={"action": "voar"}, index=3)
