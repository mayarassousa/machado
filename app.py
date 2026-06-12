"""Interface web do Machado (Gradio / Hugging Face Spaces).

Cole um texto e veja o diagnóstico: trechos destacados por categoria,
observações estruturais por frase, estatísticas e a saída JSON completa.

Uso local:  python app.py
No Hugging Face, este arquivo é o ponto de entrada do Space.
"""

from pathlib import Path

import gradio as gr

from machado import MotorEstilo
from machado.tipos import (
    ROTULOS_CATEGORIA, ROTULOS_SEVERIDADE,
    ATENCAO, SUGESTAO, INFORMATIVO,
    GERUNDISMO, PLEONASMO, CLICHE, PALAVRA_VAZIA, MARCADOR_IA,
    VOZ_PASSIVA, NOMINALIZACAO, REPETICAO,
    FRASE_LONGA, QUEISMO, ADVERBIO_MENTE, ADJETIVACAO,
)

MOTOR = MotorEstilo()

# Categorias com extensão de trecho (entram no destaque inline). As
# estruturais (frase longa, queísmo, advérbios, adjetivação) marcam a
# frase inteira e por isso aparecem em lista própria, não no destaque.
ROTULO_CURTO = {
    GERUNDISMO: "Gerundismo",
    PLEONASMO: "Pleonasmo",
    CLICHE: "Clichê",
    PALAVRA_VAZIA: "Corporativês",
    MARCADOR_IA: "Marcador de IA",
    VOZ_PASSIVA: "Voz passiva",
    NOMINALIZACAO: "Nominalização",
    REPETICAO: "Repetição",
}
ESTRUTURAIS = {FRASE_LONGA, QUEISMO, ADVERBIO_MENTE, ADJETIVACAO}

CORES = {
    "Gerundismo": "#fca5a5",
    "Pleonasmo": "#fdba74",
    "Clichê": "#fcd34d",
    "Corporativês": "#fde68a",
    "Marcador de IA": "#c4b5fd",
    "Voz passiva": "#93c5fd",
    "Nominalização": "#5eead4",
    "Repetição": "#f9a8d4",
}

_PRIORIDADE = {ATENCAO: 0, SUGESTAO: 1, INFORMATIVO: 2}


def _montar_destaques(texto, ocorrencias):
    """Converte ocorrências em segmentos para o HighlightedText.

    Destaques não podem se sobrepor; quando duas regras marcam a mesma
    região (acontece: um gerundismo dentro de uma nominalização), vence
    a de severidade maior e, em empate, a que começa antes. A tabela
    abaixo do destaque sempre traz a lista completa, sem esse corte.
    """
    candidatas = sorted(
        (o for o in ocorrencias if o.categoria in ROTULO_CURTO),
        key=lambda o: (o.inicio, _PRIORIDADE[o.severidade], o.fim - o.inicio),
    )
    segmentos, pos = [], 0
    for o in candidatas:
        if o.inicio < pos:
            continue
        if o.inicio > pos:
            segmentos.append((texto[pos:o.inicio], None))
        segmentos.append((texto[o.inicio:o.fim], ROTULO_CURTO[o.categoria]))
        pos = o.fim
    if pos < len(texto):
        segmentos.append((texto[pos:], None))
    return segmentos


def _resumo(resultado):
    e = resultado.estatisticas
    inicio = resultado.texto[:80].replace("\n", " ")
    if len(resultado.texto) > 80:
        inicio += "…"
    linhas = [
        f"Texto analisado: “{inicio}”",
        f"**{e['palavras']}** palavras em **{e['frases']}** frases "
        f"(média de {e['media_palavras_por_frase']} palavras por frase)",
        f"**{e['total_ocorrencias']}** ocorrências "
        f"({e['ocorrencias_por_1000_palavras']} por mil palavras): "
        f"{e['por_severidade'][ATENCAO]} de atenção, "
        f"{e['por_severidade'][SUGESTAO]} sugestões, "
        f"{e['por_severidade'][INFORMATIVO]} informativas",
        f"**Índice de sotaque de IA:** "
        f"{e['indice_sotaque_ia_por_1000_palavras']} por mil palavras",
        f"Pipeline: {resultado.modo_pipeline}"
        + (f" (regras inativas: {', '.join(resultado.regras_inativas)})"
           if resultado.regras_inativas else ""),
    ]
    return "\n\n".join(linhas)


def _estruturais(resultado):
    grupo = [o for o in resultado.ocorrencias if o.categoria in ESTRUTURAIS]
    if not grupo:
        return "Nenhuma observação estrutural."
    linhas = []
    for o in grupo:
        linhas.append(
            f"- **{ROTULOS_CATEGORIA[o.categoria]}** "
            f"[{ROTULOS_SEVERIDADE[o.severidade]}]: {o.explicacao} "
            f"Trecho: “{o.trecho}”"
        )
    return "\n".join(linhas)


def _tabela(resultado):
    return [
        [
            ROTULOS_CATEGORIA[o.categoria],
            ROTULOS_SEVERIDADE[o.severidade],
            o.trecho,
            o.explicacao,
            o.sugestao,
        ]
        for o in resultado.ocorrencias
    ]


def analisar_texto(texto):
    texto = (texto or "").strip()
    if not texto:
        return [("Cole um texto acima para analisar.", None)], "", "", [], {}
    resultado = MOTOR.analisar(texto)
    return (
        _montar_destaques(texto, resultado.ocorrencias),
        _resumo(resultado),
        _estruturais(resultado),
        _tabela(resultado),
        resultado.como_dict(),
    )


def _carregar_exemplos():
    pasta = Path(__file__).parent / "exemplos"
    ordem = ["corporativo", "gerado_ia", "academico", "jornalistico", "limpo"]
    exemplos = []
    for nome in ordem:
        arquivo = pasta / f"{nome}.txt"
        if arquivo.exists():
            exemplos.append([arquivo.read_text(encoding="utf-8").strip()])
    return exemplos


with gr.Blocks(title="Machado — revisor de estilo para PT-BR") as demo:
    gr.Markdown(
        "# 🪓 Machado\n"
        "Revisor de estilo para o português brasileiro. Duas camadas "
        "(regex e spaCy), saída explicável: cada marcação diz qual regra "
        "disparou, por quê e o que fazer. Os destaques cobrem os desvios "
        "pontuais; as observações por frase (período longo, queísmo, "
        "acúmulo de advérbios) aparecem logo abaixo."
    )
    entrada = gr.Textbox(
        label="Texto para análise",
        placeholder="Cole aqui o texto em português...",
        lines=8,
    )
    botao = gr.Button("Analisar", variant="primary")

    destaque = gr.HighlightedText(
        label="Desvios pontuais",
        color_map=CORES,
        show_legend=True,
        combine_adjacent=False,
    )
    resumo = gr.Markdown(label="Resumo")
    estruturais = gr.Markdown(label="Observações por frase")
    tabela = gr.Dataframe(
        headers=["Categoria", "Severidade", "Trecho", "Explicação", "Sugestão"],
        label="Todas as ocorrências",
        wrap=True,
        interactive=False,
    )
    with gr.Accordion("Saída JSON completa", open=False):
        saida_json = gr.JSON()

    saidas = [destaque, resumo, estruturais, tabela, saida_json]
    botao.click(analisar_texto, inputs=entrada, outputs=saidas)
    entrada.submit(analisar_texto, inputs=entrada, outputs=saidas)

    gr.Examples(
        examples=_carregar_exemplos(),
        inputs=entrada,
        outputs=saidas,
        fn=analisar_texto,
        run_on_click=True,
        cache_examples=False,
        label="Exemplos (comunicado corporativo, texto com cara de LLM, "
              "trecho acadêmico, nota jornalística, texto enxuto)",
    )

    # Editar o texto invalida o diagnóstico anterior: limpa a saída até
    # a próxima análise. (.input dispara só com edição do usuário, não
    # quando um exemplo preenche a caixa programaticamente.)
    def _limpar():
        return (
            [("Texto alterado. Clique em Analisar para atualizar o "
              "diagnóstico.", None)],
            "", "", [], {},
        )

    entrada.input(_limpar, None, saidas)

if __name__ == "__main__":
    demo.launch()
