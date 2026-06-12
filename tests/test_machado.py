"""Testes do Machado.

Cada regra tem ao menos um caso positivo e os falsos positivos clássicos
têm casos negativos. Rodar: pytest -q
"""

import json

import pytest

from machado import MotorEstilo, ConfigMotor


@pytest.fixture(scope="module")
def motor():
    return MotorEstilo()


def categorias(motor, texto):
    return {o.categoria for o in motor.analisar(texto).ocorrencias}


def regras(motor, texto):
    return {o.regra_id for o in motor.analisar(texto).ocorrencias}


# ----------------------------------------------------------------- regex ---

def test_gerundismo_ir_estar(motor):
    assert "gerundismo" in categorias(motor, "Vou estar te enviando o contrato.")


def test_gerundismo_estar_futuro(motor):
    assert "gerundismo" in categorias(motor, "Estarei transferindo sua ligação.")


def test_gerundio_legitimo_nao_dispara(motor):
    assert "gerundismo" not in categorias(motor, "Estou enviando o contrato agora.")


def test_pleonasmo_ha_atras(motor):
    assert "rx_pleonasmo_ha_atras" in regras(motor, "Isso aconteceu há dois anos atrás.")


def test_ha_sem_atras_nao_dispara(motor):
    assert "rx_pleonasmo_ha_atras" not in regras(motor, "Isso aconteceu há dois anos.")


def test_pleonasmo_direcional(motor):
    assert "pleonasmo" in categorias(motor, "Ele subiu para cima depressa.")


def test_cliche(motor):
    assert "cliche" in categorias(motor, "Antes de mais nada, vamos ao orçamento.")


def test_atraves_de(motor):
    assert "rx_cliche_atraves_de" in regras(motor, "Avisei através do aplicativo.")


def test_o_mesmo_pronominal(motor):
    assert "rx_cliche_o_mesmo_pronominal" in regras(
        motor, "O cliente recebeu o boleto e pagou o valor ao mesmo."
    )


def test_ao_mesmo_tempo_nao_dispara(motor):
    assert "rx_cliche_o_mesmo_pronominal" not in regras(
        motor, "As duas equipes trabalham ao mesmo tempo."
    )


def test_marcador_ia_metadiscurso(motor):
    assert "marcador_ia" in categorias(
        motor, "É importante ressaltar que os dados foram revisados."
    )


def test_marcador_ia_travessao(motor):
    assert "rx_ia_travessao_parentetico" in regras(
        motor, "O modelo — treinado em português — superou a linha de base."
    )


def test_travessao_de_dialogo_nao_dispara(motor):
    assert "rx_ia_travessao_parentetico" not in regras(
        motor, "— Bom dia — disse ela.\n— Bom dia."
    )


def test_marcador_ia_nao_e_apenas(motor):
    assert "rx_ia_nao_e_apenas" in regras(
        motor, "Não é apenas uma ferramenta, é uma mudança de paradigma."
    )


# ----------------------------------------------------------------- spacy ---

def test_voz_passiva(motor):
    assert "voz_passiva" in categorias(motor, "O relatório foi escrito pela equipe.")


def test_adjetivo_em_ido_nao_e_passiva(motor):
    assert "voz_passiva" not in categorias(motor, "O processo foi rápido.")


def test_nominalizacao(motor):
    assert "nominalizacao" in categorias(
        motor, "A equipe vai realizar a implementação do módulo."
    )


def test_frase_longa(motor):
    texto = ("A reunião que estava marcada para a próxima semana foi adiada "
             "porque a sala maior do prédio principal ficou indisponível para "
             "o período da manhã e ninguém conseguiu encontrar outro espaço "
             "com capacidade suficiente para acomodar todos os participantes "
             "convidados pela coordenação geral do programa de formação.")
    assert "frase_longa" in categorias(motor, texto)


def test_queismo(motor):
    texto = ("O documento que recebemos diz que o prazo que combinamos depende "
             "da verba que a diretoria aprovar.")
    assert "queismo" in categorias(motor, texto)


def test_adverbios_mente(motor):
    assert "adverbios_em_mente" in categorias(
        motor, "O sistema respondeu rapidamente e corretamente aos testes."
    )


def test_repeticao_lexical(motor):
    texto = ("O atendimento melhorou. O time de atendimento cresceu. "
             "Mesmo assim, o atendimento ainda recebe reclamações.")
    assert "repeticao_lexical" in categorias(motor, texto)


# ----------------------------------------------------------------- motor ---

def test_texto_enxuto_quase_limpo(motor):
    resultado = motor.analisar(
        "A diretoria aprovou o sistema em março. A equipe mede os resultados "
        "no fim do mês."
    )
    assert resultado.estatisticas["por_severidade"]["atencao"] == 0
    assert "gerundismo" not in {o.categoria for o in resultado.ocorrencias}


def test_json_serializavel(motor):
    resultado = motor.analisar("Vou estar verificando isso há dias atrás.")
    dados = json.loads(motor.para_json(resultado))
    assert dados["ocorrencias"], "JSON deve conter as ocorrências"
    campos = dados["ocorrencias"][0].keys()
    for campo in ("regra_id", "categoria", "explicacao", "sugestao", "inicio", "fim"):
        assert campo in campos


def test_ocorrencias_ordenadas_por_posicao(motor):
    resultado = motor.analisar(
        "Antes de mais nada, vou estar revisando o texto que foi escrito há "
        "anos atrás."
    )
    posicoes = [o.inicio for o in resultado.ocorrencias]
    assert posicoes == sorted(posicoes)


def test_config_personalizada():
    motor = MotorEstilo(ConfigMotor(max_palavras_frase=5))
    resultado = motor.analisar("Esta frase curta tem exatamente sete palavras aqui.")
    assert "frase_longa" in {o.categoria for o in resultado.ocorrencias}


def test_nome_proprio_em_ado_nao_e_passiva(motor):
    assert "voz_passiva" not in categorias(motor, "O autor preferido dela é o Machado.")
