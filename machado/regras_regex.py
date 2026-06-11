"""Camada 1 — Regras de superfície (regex).

Princípio de projeto: **regra é dado, não código.** Cada desvio detectável
por padrão de superfície vive em uma entrada declarativa (`RegraRegex`).
Adicionar uma dica de estilo nova não exige tocar no motor — exige uma
linha nesta base. É assim que um catálogo sai de 12 para 120 regras sem
virar uma bola de lama.

Critério editorial das regras: precisão acima de cobertura. Um revisor
que grita falso positivo é desinstalado na primeira semana.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .tipos import (
    Ocorrencia,
    ATENCAO, SUGESTAO, INFORMATIVO,
    GERUNDISMO, PLEONASMO, CLICHE, PALAVRA_VAZIA, MARCADOR_IA,
)

# Clíticos que podem se interpor entre "estar" e o gerúndio
_CLITICO = r"(?:(?:te|me|se|lhe|lhes|nos|vos|o|a|os|as)\s+)?"


def _fora_de_dialogo(texto: str, m: "re.Match") -> bool:
    """Veto para o travessão parentético: se a linha do casamento começa
    com travessão, trata-se de discurso direto (uso canônico em PT-BR),
    não do travessão intercalado à moda anglófona."""
    inicio_linha = texto.rfind("\n", 0, m.start()) + 1
    return not texto[inicio_linha:m.start()].lstrip().startswith(("—", "–"))


@dataclass(frozen=True)
class RegraRegex:
    id: str
    categoria: str
    severidade: str
    padrao: str
    explicacao: str
    sugestao: str
    flags: int = re.IGNORECASE
    # Veto contextual opcional: recebe (texto, match) e devolve False para
    # descartar o casamento. Mantém a regra declarativa, mas permite
    # restrições que regex puro não expressa (ex.: posição na linha).
    filtro: Optional[Callable[[str, "re.Match"], bool]] = None


REGRAS: list[RegraRegex] = [
    # ------------------------------------------------------------------ #
    # GERUNDISMO                                                          #
    # ------------------------------------------------------------------ #
    RegraRegex(
        id="rx_gerundismo_ir_estar",
        categoria=GERUNDISMO,
        severidade=ATENCAO,
        padrao=rf"\b(?:vou|vais|vai|vamos|v[ãa]o|irei|ir[áa]s?|iremos|ir[ãa]o)\s+estar\s+{_CLITICO}\w+[aei]ndo\b",
        explicacao="Perífrase 'ir + estar + gerúndio', calco do inglês "
                   "('will be sending') sem função aspectual em português.",
        sugestao="Use o futuro simples ou a perífrase direta: "
                 "'vou enviar' / 'enviarei'.",
    ),
    RegraRegex(
        id="rx_gerundismo_estar_futuro",
        categoria=GERUNDISMO,
        severidade=ATENCAO,
        padrao=rf"\bestar(?:ei|[áa]s|[áa]|emos|[ãa]o)\s+{_CLITICO}\w+[aei]ndo\b",
        explicacao="Futuro de 'estar' + gerúndio para ação pontual "
                   "('estarei transferindo') é gerundismo.",
        sugestao="Prefira o futuro simples: 'transferirei' / 'vou transferir'.",
    ),

    # ------------------------------------------------------------------ #
    # PLEONASMOS VICIOSOS                                                 #
    # ------------------------------------------------------------------ #
    RegraRegex(
        id="rx_pleonasmo_direcional",
        categoria=PLEONASMO,
        severidade=ATENCAO,
        padrao=r"\b(?:s[ou]b\w*\s+para\s+cima|des[cç]\w*\s+para\s+baixo|"
               r"entr\w+\s+para\s+dentro|sa[ií]\w*\s+para\s+fora)\b",
        explicacao="O verbo já contém a direção; o adjunto a repete.",
        sugestao="Corte o complemento direcional: 'subir', 'descer', 'entrar', 'sair'.",
    ),
    RegraRegex(
        id="rx_pleonasmo_ha_atras",
        categoria=PLEONASMO,
        severidade=ATENCAO,
        padrao=r"\bh[áa]\s+(?:\w+\s+){0,2}(?:anos?|m[êe]s(?:es)?|dias?|semanas?|d[ée]cadas?|s[ée]culos?|horas?|minutos?)\s+atr[áa]s\b",
        explicacao="'Há' já indica tempo decorrido; 'atrás' duplica a marcação.",
        sugestao="Use uma das formas: 'há dois anos' OU 'dois anos atrás'.",
    ),
    RegraRegex(
        id="rx_pleonasmo_lexical",
        categoria=PLEONASMO,
        severidade=ATENCAO,
        padrao=r"\b(?:elo\s+de\s+liga[çc][ãa]o|certeza\s+absoluta|conclus[ãa]o\s+final|"
               r"consenso\s+geral|metades\s+iguais|protagonista\s+principal|"
               r"surpresa\s+inesperada|acabamento\s+final|outra\s+alternativa|"
               r"monop[óo]lio\s+exclusivo|encarar\s+de\s+frente|"
               r"planejar\s+(?:antecipadamente|com\s+anteced[êe]ncia)|"
               r"repetir\s+(?:de\s+novo|novamente|outra\s+vez)|ganhar\s+gr[áa]tis)\b",
        explicacao="O modificador repete um traço semântico que o núcleo já carrega "
                   "(toda conclusão é final; toda alternativa é outra).",
        sugestao="Mantenha apenas o núcleo: 'conclusão', 'alternativa', 'consenso'.",
    ),

    # ------------------------------------------------------------------ #
    # CLICHÊS, FRASES FEITAS E MULETAS                                    #
    # ------------------------------------------------------------------ #
    RegraRegex(
        id="rx_cliche_frases_feitas",
        categoria=CLICHE,
        severidade=SUGESTAO,
        padrao=r"\b(?:antes\s+de\s+mais\s+nada|via\s+de\s+regra|no\s+que\s+tange\s+a?|"
               r"a\s+n[íi]vel\s+de|em\s+sede\s+de|dar\s+o\s+pontap[ée]\s+inicial|"
               r"pensar\s+fora\s+da\s+caixa|fazer\s+a\s+diferen[çc]a|"
               r"no\s+final\s+do\s+dia|divisor\s+de\s+[áa]guas|"
               r"de\s+vento\s+em\s+popa|colocar\s+os\s+pingos\s+nos\s+is|"
               r"correr\s+atr[áa]s\s+do\s+preju[íi]zo|a\s+duras\s+penas)\b",
        explicacao="Expressão desgastada pelo uso: ocupa espaço sem acrescentar "
                   "informação nem voz.",
        sugestao="Diga o conteúdo diretamente ('antes de tudo', 'em geral', "
                 "'quanto a') ou corte.",
    ),
    RegraRegex(
        id="rx_cliche_atraves_de",
        categoria=CLICHE,
        severidade=SUGESTAO,
        padrao=r"\batrav[ée]s\s+d(?:e|o|a|os|as|este|esta|esse|essa)\b",
        explicacao="'Através de' indica atravessamento físico ('através da janela'). "
                   "Como conectivo de meio, é muleta.",
        sugestao="Prefira 'por meio de', 'mediante', 'com' — ou reestruture a frase.",
    ),
    RegraRegex(
        id="rx_cliche_o_mesmo_pronominal",
        categoria=CLICHE,
        severidade=SUGESTAO,
        padrao=r"\b(?:d[oa]s?|a[oa]s?|n[oa]s?|pel[oa]s?)\s+mesm[oa]s?\b"
               r"(?!\s+(?:tempo|forma|maneira|modo|jeito|lugar|dia|ano|m[êe]s|momento|instante|hora|per[íi]odo|sentido))",
        explicacao="'O mesmo' usado como pronome ('entregar ao mesmo') é vício "
                   "de linguagem burocrática.",
        sugestao="Retome com pronome pessoal ('a ele', 'dele') ou repita o substantivo.",
    ),

    # ------------------------------------------------------------------ #
    # PALAVRAS VAZIAS / CORPORATIVÊS                                      #
    # ------------------------------------------------------------------ #
    RegraRegex(
        id="rx_vazia_corporatives",
        categoria=PALAVRA_VAZIA,
        severidade=INFORMATIVO,
        padrao=r"\b(?:sinergia\w*|disruptiv\w+|proativ\w+|alavancar\w*|agregar\s+valor)\b",
        explicacao="Vocabulário corporativo de baixo conteúdo informacional: "
                   "sinaliza registro, não significado.",
        sugestao="Substitua pelo efeito concreto: o que melhora, quanto, para quem.",
    ),

    # ------------------------------------------------------------------ #
    # MARCADORES DE TEXTO GERADO POR IA                                   #
    # Cacoetes estatisticamente associados à saída de LLMs em PT-BR.      #
    # Nenhum prova nada sozinho; o que pesa é a densidade (ver índice     #
    # no motor). Por isso a severidade é informativa.                     #
    # ------------------------------------------------------------------ #
    RegraRegex(
        id="rx_ia_travessao_parentetico",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"(?<=\w)\s[—–]\s(?=\w)",
        explicacao="Travessão parentético no meio da frase, à moda anglófona. "
                   "Em PT-BR espontâneo o travessão concentra-se no discurso "
                   "direto; o uso intercalado denso é assinatura típica de texto gerado.",
        sugestao="Troque por vírgulas, parênteses ou dois-pontos — ou assuma o "
                 "travessão como escolha consciente de estilo.",
        flags=0,
        filtro=_fora_de_dialogo,
    ),
    RegraRegex(
        id="rx_ia_nao_e_apenas",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\bn[ãa]o\s+(?:é|s[ãa]o)\s+(?:apenas|s[óo]|somente)\b.{0,80}?[,;—:]\s*(?:é|s[ãa]o|mas|e\s+sim)\b",
        explicacao="Estrutura contrastiva formulaica ('não é apenas X, é Y'), "
                   "uma das construções de ênfase mais frequentes em texto de LLM.",
        sugestao="Afirme diretamente o segundo termo; o contraste raramente "
                 "acrescenta informação.",
    ),
    RegraRegex(
        id="rx_ia_nao_se_trata",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\bn[ãa]o\s+se\s+trata\s+(?:apenas\s+|s[óo]\s+)?de\b.{0,80}?\bmas\s+(?:sim\s+)?de\b",
        explicacao="Variante do contraste formulaico 'não se trata de X, mas de Y'.",
        sugestao="Vá direto ao ponto: diga do que se trata.",
    ),
    RegraRegex(
        id="rx_ia_importante_ressaltar",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\b(?:[ée]\s+(?:importante|fundamental|crucial|essencial)\s+|vale\s+)"
               r"(?:ressaltar|destacar|notar|lembrar|frisar|mencionar|salientar)\s+que\b",
        explicacao="Metadiscurso de preenchimento: anuncia relevância em vez de "
                   "demonstrá-la. Frequência altíssima em texto gerado.",
        sugestao="Corte o anúncio e afirme o conteúdo. Se é importante, o leitor nota.",
    ),
    RegraRegex(
        id="rx_ia_cenario_atual",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\b(?:no\s+(?:cen[áa]rio|contexto|mundo)\s+atual|em\s+um\s+mundo\s+cada\s+vez\s+mais)\b",
        explicacao="Abertura genérica de ambientação, assinatura de introdução "
                   "gerada por LLM.",
        sugestao="Comece pelo fato, pelo dado ou pela cena concreta.",
    ),
    RegraRegex(
        id="rx_ia_papel_fundamental",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\bdesempenh\w+\s+um\s+papel\s+(?:fundamental|crucial|central|importante|chave|vital)\b",
        explicacao="Colocação 'desempenha um papel fundamental': fórmula de "
                   "relevância sem conteúdo, recorrente em saída de LLM.",
        sugestao="Diga qual é o papel: o que o elemento faz, em que medida.",
    ),
    RegraRegex(
        id="rx_ia_navegar_mergulhar",
        categoria=MARCADOR_IA,
        severidade=INFORMATIVO,
        padrao=r"\b(?:naveg\w+\s+(?:por|pel[oa]s?)\s+(?:ess[ea]s?\s+|est[ea]s?\s+|o\s+|a\s+|os\s+|as\s+)?"
               r"(?:cen[áa]rio|mundo|universo|complexidade|desafios?|[áa]guas)|"
               r"mergulh\w+\s+(?:a\s+fundo|no\s+universo|no\s+mundo|nos\s+detalhes|nesse\s+tema|neste\s+tema))\b",
        explicacao="Metáfora náutica/de imersão genérica ('navegar pelo cenário', "
                   "'mergulhar a fundo'), cacoete de LLM em PT-BR.",
        sugestao="Troque a metáfora por um verbo concreto: examinar, comparar, medir.",
    ),
    RegraRegex(
        id="rx_ia_vestigio_chat",
        categoria=MARCADOR_IA,
        severidade=ATENCAO,
        padrao=r"(?:\bespero\s+que\s+(?:isso\s+|isto\s+)?(?:te\s+|lhe\s+)?ajude\b|"
               r"\bcomo\s+(?:um\s+)?modelo\s+de\s+linguagem\b|"
               r"\bao\s+longo\s+dest[ea]\s+(?:artigo|texto)\b|^claro[!,])",
        explicacao="Vestígio de interação de chat ou de molde de redação que "
                   "sobreviveu ao copiar-e-colar.",
        sugestao="Remova: é resíduo do processo de geração, não parte do texto.",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
]


def aplicar_regras_regex(texto: str) -> list[Ocorrencia]:
    """Varre o texto com toda a base declarativa e devolve as ocorrências."""
    ocorrencias: list[Ocorrencia] = []
    for regra in REGRAS:
        for m in re.finditer(regra.padrao, texto, regra.flags):
            if regra.filtro is not None and not regra.filtro(texto, m):
                continue
            ocorrencias.append(
                Ocorrencia(
                    regra_id=regra.id,
                    categoria=regra.categoria,
                    severidade=regra.severidade,
                    trecho=m.group(0).strip(),
                    inicio=m.start(),
                    fim=m.end(),
                    explicacao=regra.explicacao,
                    sugestao=regra.sugestao,
                    camada="regex",
                    contexto=_recorte(texto, m.start(), m.end()),
                )
            )
    return ocorrencias


def _recorte(texto: str, inicio: int, fim: int, margem: int = 45) -> str:
    """Janela de contexto ao redor do trecho, para o relatório."""
    a = max(0, inicio - margem)
    b = min(len(texto), fim + margem)
    pre = "…" if a > 0 else ""
    pos = "…" if b < len(texto) else ""
    return pre + texto[a:b].replace("\n", " ") + pos
