"""Camada 2 — Regras morfossintáticas (SpaCy).

Aqui ficam os desvios que regex não alcança com segurança: eles dependem
de segmentação de sentenças, classe gramatical, morfologia ou contagem
estrutural. A camada é *capability-aware*: cada regra declara o que exige
do pipeline e se desliga (avisando) quando o recurso não está disponível.

Dois modos de operação:
- "completo": pipeline treinado (pt_core_news_sm ou superior) — todas as
  regras ativas, com POS e morfologia refinando as heurísticas.
- "reduzido": spacy.blank("pt") + sentencizer — regras lexicais e
  estruturais continuam funcionando; as que exigem POS são desativadas.

Em produção, isso significa poder rodar uma primeira passada barata em
escala e reservar o pipeline caro para onde ele é necessário.
"""

from __future__ import annotations

import warnings
from collections import Counter

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

from .tipos import (
    Ocorrencia,
    ATENCAO, SUGESTAO, INFORMATIVO,
    VOZ_PASSIVA, ADVERBIO_MENTE, ADJETIVACAO, NOMINALIZACAO,
    FRASE_LONGA, QUEISMO, REPETICAO,
)

MODELO_PADRAO = "pt_core_news_sm"

# --------------------------------------------------------------------------- #
# Recursos lexicais                                                            #
# --------------------------------------------------------------------------- #

_FORMAS_SER = {
    "é", "são", "era", "eram", "foi", "foram", "será", "serão",
    "seria", "seriam", "sendo", "sido", "ser", "somos", "fomos", "fui",
}

# Particípios irregulares frequentes (não terminam em -ado/-ido)
_PARTICIPIOS_IRREGULARES = {
    "feito", "feita", "feitos", "feitas", "escrito", "escrita", "escritos",
    "escritas", "dito", "dita", "ditos", "ditas", "visto", "vista", "vistos",
    "vistas", "posto", "posta", "postos", "postas", "aberto", "aberta",
    "abertos", "abertas", "coberto", "coberta", "cobertos", "cobertas",
    "pago", "paga", "pagos", "pagas", "gasto", "gasta", "gastos", "gastas",
    "impresso", "impressa", "impressos", "impressas", "aceito", "aceita",
    "aceitos", "aceitas", "entregue", "entregues", "suspenso", "suspensa",
}

# Adjetivos em -ido/-ida que NÃO são particípios (anti-falso-positivo
# para o modo reduzido, sem POS)
_ADJETIVOS_EM_IDO = {
    "rápido", "válido", "sólido", "líquido", "ávido", "cândido", "lúcido",
    "nítido", "tímido", "úmido", "vívido", "esplêndido", "estúpido",
    "rígido", "árido", "híbrido", "ácido", "fluido", "intrépido", "mórbido",
}

# Verbos-suporte que disparam nominalização ("realizar a implementação")
_VERBOS_SUPORTE = ("realiz", "efetu", "promov", "proced", "executa", "execut")
_FORMAS_FAZER = {
    "fazer", "faz", "fazem", "fazia", "faziam", "fez", "fizeram",
    "fará", "farão", "faria", "fariam", "fazendo", "feito", "feita",
}
_SUFIXOS_NOMINALIZACAO = ("ção", "ções", "são", "sões", "mento", "mentos")

_STOPWORDS_REPETICAO = {
    "porque", "também", "ainda", "sobre", "entre", "quando", "muito",
    "muitos", "muita", "muitas", "outro", "outra", "outros", "outras",
    "mesmo", "mesma", "depois", "antes", "assim", "então", "neste",
    "nesta", "desse", "dessa", "deste", "desta", "aquele", "aquela",
    "todos", "todas", "podem", "poder", "estão", "serão", "foram",
}


# --------------------------------------------------------------------------- #
# Carregamento do pipeline                                                     #
# --------------------------------------------------------------------------- #

def carregar_nlp(nome_modelo: str = MODELO_PADRAO) -> tuple[Language, str]:
    """Carrega o pipeline de PT.

    Tenta o modelo treinado; na ausência dele, cai para um pipeline em
    branco com sentencizer e devolve o modo "reduzido". A análise nunca
    quebra por falta de modelo — ela apenas declara o que ficou de fora.
    """
    try:
        nlp = spacy.load(nome_modelo)
        return nlp, "completo"
    except OSError:
        warnings.warn(
            f"Modelo '{nome_modelo}' não encontrado; usando pipeline reduzido "
            f"(blank 'pt' + sentencizer). Para a análise completa: "
            f"python -m spacy download {nome_modelo}",
            stacklevel=2,
        )
        nlp = spacy.blank("pt")
        nlp.add_pipe("sentencizer")
        return nlp, "reduzido"


def _lema(token) -> str:
    """Lema quando o lematizador existe; forma minúscula caso contrário."""
    return token.lemma_.lower() if token.lemma_ else token.lower_


def _palavras(span: Span) -> list:
    return [t for t in span if t.is_alpha]


def _trecho_frase(sent: Span, limite: int = 70) -> str:
    txt = sent.text.replace("\n", " ").strip()
    return txt if len(txt) <= limite else txt[: limite - 1] + "…"


def _eh_participio(token, modo: str) -> bool:
    """Particípio com POS/morfologia no modo completo; heurística no reduzido."""
    if modo == "completo":
        if "Part" in token.morph.get("VerbForm"):
            return True
        # alguns particípios vêm etiquetados como ADJ; a morfologia decide
        return token.pos_ in {"VERB", "AUX"} and token.text.lower().endswith(
            ("ado", "ada", "ados", "adas", "ido", "ida", "idos", "idas")
        )
    # Maiúscula no meio da frase indica nome próprio (Machado, Furtado,
    # Alvarado…), não particípio — sem POS, a capitalização é o sinal.
    if token.text[:1].isupper() and not token.is_sent_start:
        return False
    palavra = token.lower_
    if palavra in _PARTICIPIOS_IRREGULARES:
        return True
    if len(palavra) <= 4:
        return False
    if palavra.endswith(("ado", "ada", "ados", "adas")):
        return True
    if palavra.endswith(("ido", "ida", "idos", "idas")):
        base = palavra.rstrip("s")
        if base.endswith("a"):
            base = base[:-1] + "o"
        return base not in _ADJETIVOS_EM_IDO
    return False


# --------------------------------------------------------------------------- #
# Regras                                                                       #
# --------------------------------------------------------------------------- #

def _r_frase_longa(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    ocs = []
    for sent in doc.sents:
        n = len(_palavras(sent))
        if n > cfg.max_palavras_frase:
            ocs.append(Ocorrencia(
                regra_id="sp_frase_longa",
                categoria=FRASE_LONGA,
                severidade=SUGESTAO,
                trecho=_trecho_frase(sent),
                inicio=sent.start_char,
                fim=sent.end_char,
                explicacao=f"Frase com {n} palavras (limite configurado: "
                           f"{cfg.max_palavras_frase}). Períodos longos elevam a "
                           f"carga de memória de trabalho do leitor.",
                sugestao="Quebre em duas ou três frases; uma ideia central por período.",
                camada="spacy",
                contexto=_trecho_frase(sent, 110),
            ))
    return ocs


def _r_queismo(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    ocs = []
    for sent in doc.sents:
        ques = [t for t in sent if t.lower_ == "que"]
        if len(ques) >= cfg.min_que_por_frase:
            ocs.append(Ocorrencia(
                regra_id="sp_queismo",
                categoria=QUEISMO,
                severidade=SUGESTAO,
                trecho=_trecho_frase(sent),
                inicio=sent.start_char,
                fim=sent.end_char,
                explicacao=f"{len(ques)} ocorrências de 'que' na mesma frase: "
                           f"encadeamento de subordinadas que dilui o foco.",
                sugestao="Converta orações relativas em frases independentes ou "
                         "em sintagmas nominais.",
                camada="spacy",
                contexto=_trecho_frase(sent, 110),
            ))
    return ocs


def _r_adverbios_mente(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    ocs = []
    for sent in doc.sents:
        if modo == "completo":
            advs = [t for t in sent
                    if t.pos_ == "ADV" and t.lower_.endswith("mente")]
        else:
            advs = [t for t in sent
                    if t.lower_.endswith("mente") and len(t.lower_) > 7
                    and t.lower_ != "somente"]
        if len(advs) >= cfg.min_adverbios_mente:
            lista = ", ".join(t.text for t in advs)
            ocs.append(Ocorrencia(
                regra_id="sp_adverbios_mente",
                categoria=ADVERBIO_MENTE,
                severidade=SUGESTAO,
                trecho=lista,
                inicio=advs[0].idx,
                fim=advs[-1].idx + len(advs[-1].text),
                explicacao=f"{len(advs)} advérbios em -mente na mesma frase "
                           f"({lista}): ritmo arrastado e modificação vaga.",
                sugestao="Troque por verbo mais preciso ('correu rapidamente' → "
                         "'disparou') ou mantenha só o advérbio essencial.",
                camada="spacy",
                contexto=_trecho_frase(sent, 110),
            ))
    return ocs


def _r_voz_passiva(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    """ser + particípio. No modo completo a morfologia corta falsos positivos."""
    ocs = []
    for sent in doc.sents:
        tokens = list(sent)
        for i, tok in enumerate(tokens):
            if tok.lower_ not in _FORMAS_SER:
                continue
            for j in range(i + 1, min(i + 4, len(tokens))):
                alvo = tokens[j]
                if alvo.is_punct:
                    break
                if alvo.is_alpha and _eh_participio(alvo, modo):
                    trecho = doc.text[tok.idx: alvo.idx + len(alvo.text)]
                    ocs.append(Ocorrencia(
                        regra_id="sp_voz_passiva",
                        categoria=VOZ_PASSIVA,
                        severidade=INFORMATIVO,
                        trecho=trecho,
                        inicio=tok.idx,
                        fim=alvo.idx + len(alvo.text),
                        explicacao="Construção passiva ('ser + particípio'): "
                                   "legítima quando o agente não importa; em "
                                   "excesso, esconde quem faz o quê.",
                        sugestao="Se o agente importa, ative a frase: "
                                 "'a diretoria aprovou' em vez de 'foi aprovado'.",
                        camada="spacy",
                        contexto=_trecho_frase(sent, 110),
                    ))
                    break
    return ocs


def _r_nominalizacao(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    """Verbo-suporte + nome deverbal: 'realizar a implementação' → 'implementar'."""
    ocs = []
    tokens = [t for t in doc if not t.is_space]
    for i, tok in enumerate(tokens):
        eh_suporte = tok.lower_.startswith(_VERBOS_SUPORTE) or tok.lower_ in _FORMAS_FAZER
        if not eh_suporte:
            continue
        for j in range(i + 1, min(i + 4, len(tokens))):
            alvo = tokens[j]
            if alvo.is_punct:
                break
            if alvo.lower_.endswith(_SUFIXOS_NOMINALIZACAO):
                if modo == "completo" and alvo.pos_ not in {"NOUN", "PROPN"}:
                    break
                trecho = doc.text[tok.idx: alvo.idx + len(alvo.text)]
                ocs.append(Ocorrencia(
                    regra_id="sp_nominalizacao",
                    categoria=NOMINALIZACAO,
                    severidade=SUGESTAO,
                    trecho=trecho,
                    inicio=tok.idx,
                    fim=alvo.idx + len(alvo.text),
                    explicacao="Verbo-suporte + substantivo deverbal "
                               "('realizar a implementação'): a ação vira nome e "
                               "a frase ganha peso burocrático.",
                    sugestao="Use o verbo pleno: 'implementar', 'verificar', 'analisar'.",
                    camada="spacy",
                    contexto=_recorte_doc(doc, tok.idx, alvo.idx + len(alvo.text)),
                ))
                break
    return ocs


def _r_adjetivacao(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    """Exige POS — desativada no modo reduzido."""
    ocs = []
    for sent in doc.sents:
        adjs = [t for t in sent if t.pos_ == "ADJ"]
        if len(adjs) >= cfg.min_adjetivos_frase:
            lista = ", ".join(t.text for t in adjs)
            ocs.append(Ocorrencia(
                regra_id="sp_adjetivacao",
                categoria=ADJETIVACAO,
                severidade=SUGESTAO,
                trecho=lista,
                inicio=sent.start_char,
                fim=sent.end_char,
                explicacao=f"{len(adjs)} adjetivos na mesma frase ({lista}): "
                           f"qualificação em excesso enfraquece cada qualificação.",
                sugestao="Escolha o adjetivo que sustenta a frase e corte os outros; "
                         "prefira mostrar a qualidade com fato ou dado.",
                camada="spacy",
                contexto=_trecho_frase(sent, 110),
            ))
    return ocs


def _r_repeticao(doc: Doc, cfg, modo: str) -> list[Ocorrencia]:
    """Mesmo item lexical de conteúdo repetido em janela curta."""
    ocs = []
    posicoes: dict[str, list] = {}
    for tok in doc:
        if not tok.is_alpha or len(tok.lower_) < 5:
            continue
        chave = _lema(tok)
        if chave in _STOPWORDS_REPETICAO or tok.is_stop:
            continue
        posicoes.setdefault(chave, []).append(tok)

    for chave, toks in posicoes.items():
        if len(toks) < cfg.min_repeticoes:
            continue
        for k in range(len(toks) - cfg.min_repeticoes + 1):
            grupo = toks[k: k + cfg.min_repeticoes]
            if grupo[-1].i - grupo[0].i <= cfg.janela_repeticao:
                alvo = grupo[-1]
                ocs.append(Ocorrencia(
                    regra_id="sp_repeticao",
                    categoria=REPETICAO,
                    severidade=SUGESTAO,
                    trecho=alvo.text,
                    inicio=alvo.idx,
                    fim=alvo.idx + len(alvo.text),
                    explicacao=f"'{chave}' aparece {len(toks)}x em janela curta "
                               f"(≤ {cfg.janela_repeticao} tokens): eco lexical.",
                    sugestao="Use sinônimo, pronome ou reestruture para eliminar "
                             "a repetição — quando ela não for ênfase deliberada.",
                    camada="spacy",
                    contexto=_recorte_doc(doc, alvo.idx, alvo.idx + len(alvo.text)),
                ))
                break  # uma sinalização por item lexical basta
    return ocs


def _recorte_doc(doc: Doc, inicio: int, fim: int, margem: int = 45) -> str:
    a = max(0, inicio - margem)
    b = min(len(doc.text), fim + margem)
    pre = "…" if a > 0 else ""
    pos = "…" if b < len(doc.text) else ""
    return pre + doc.text[a:b].replace("\n", " ") + pos


# Registro: (função, exige_pos)
_REGISTRO = [
    (_r_frase_longa, False),
    (_r_queismo, False),
    (_r_adverbios_mente, False),
    (_r_voz_passiva, False),
    (_r_nominalizacao, False),
    (_r_repeticao, False),
    (_r_adjetivacao, True),
]


def aplicar_regras_spacy(doc: Doc, cfg, modo: str) -> tuple[list[Ocorrencia], list[str]]:
    """Aplica as regras compatíveis com o modo do pipeline.

    Devolve (ocorrências, regras_inativas) — o motor reporta com clareza
    o que NÃO foi analisado, em vez de fingir cobertura total.
    """
    ocorrencias: list[Ocorrencia] = []
    inativas: list[str] = []
    for funcao, exige_pos in _REGISTRO:
        if exige_pos and modo != "completo":
            inativas.append(funcao.__name__.lstrip("_"))
            continue
        ocorrencias.extend(funcao(doc, cfg, modo))
    return ocorrencias, inativas
