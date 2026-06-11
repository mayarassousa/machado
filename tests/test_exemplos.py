"""Testes sobre os textos de exemplo.

Cada arquivo em exemplos/ tem um perfil estilístico esperado; estes
testes garantem que o motor reconhece esse perfil. As asserções usam
apenas regras que funcionam igual nos dois modos de pipeline (reduzido
e completo), para que a suíte passe com ou sem o modelo treinado.
"""

from pathlib import Path

import pytest

from machado import MotorEstilo

PASTA = Path(__file__).parent.parent / "exemplos"
ARQUIVOS = sorted(p.name for p in PASTA.glob("*.txt"))


@pytest.fixture(scope="module")
def motor():
    return MotorEstilo()


def analisar(motor, nome):
    texto = (PASTA / nome).read_text(encoding="utf-8")
    return motor.analisar(texto)


@pytest.mark.parametrize("arquivo", ARQUIVOS)
def test_exemplo_analisa_sem_erro(motor, arquivo):
    resultado = analisar(motor, arquivo)
    assert resultado.estatisticas["palavras"] > 0


def test_corporativo_tem_o_repertorio_classico(motor):
    categorias = {o.categoria for o in analisar(motor, "corporativo.txt").ocorrencias}
    for esperada in ("gerundismo", "pleonasmo", "cliche", "marcador_ia"):
        assert esperada in categorias


def test_gerado_ia_tem_sotaque_alto(motor):
    resultado = analisar(motor, "gerado_ia.txt")
    assert resultado.estatisticas["indice_sotaque_ia_por_1000_palavras"] >= 50
    assert "marcador_ia" in {o.categoria for o in resultado.ocorrencias}


def test_academico_tem_nominalizacao_passiva_e_periodo_longo(motor):
    categorias = {o.categoria for o in analisar(motor, "academico.txt").ocorrencias}
    for esperada in ("nominalizacao", "voz_passiva", "frase_longa"):
        assert esperada in categorias


def test_jornalistico_tem_poucos_desvios(motor):
    resultado = analisar(motor, "jornalistico.txt")
    assert resultado.estatisticas["indice_sotaque_ia_por_1000_palavras"] == 0
    assert resultado.estatisticas["total_ocorrencias"] <= 5


def test_limpo_passa_quase_intacto(motor):
    resultado = analisar(motor, "limpo.txt")
    e = resultado.estatisticas
    assert e["por_severidade"]["atencao"] == 0
    assert e["indice_sotaque_ia_por_1000_palavras"] == 0
    categorias = {o.categoria for o in resultado.ocorrencias}
    for proibida in ("gerundismo", "pleonasmo", "cliche", "marcador_ia"):
        assert proibida not in categorias
    assert e["total_ocorrencias"] <= 1
