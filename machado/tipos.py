"""Tipos centrais do Machado.

Toda detecção do motor vira uma `Ocorrencia`: um objeto auditável que
carrega não só *onde* o problema está, mas *qual regra* o detectou,
*por que* ele é um problema e *o que fazer* a respeito. A saída
explicável é decisão de arquitetura, não detalhe de apresentação.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# Níveis de severidade -------------------------------------------------------
# ATENCAO     -> desvio consolidado da norma ou vício forte (gerundismo, pleonasmo)
# SUGESTAO    -> escolha estilística que costuma enfraquecer o texto
# INFORMATIVO -> traço legítimo em dose baixa; o problema é a densidade
ATENCAO = "atencao"
SUGESTAO = "sugestao"
INFORMATIVO = "informativo"

ROTULOS_SEVERIDADE = {
    ATENCAO: "ATENÇÃO",
    SUGESTAO: "SUGESTÃO",
    INFORMATIVO: "INFO",
}

# Categorias de desvio --------------------------------------------------------
GERUNDISMO = "gerundismo"
PLEONASMO = "pleonasmo"
CLICHE = "cliche"
PALAVRA_VAZIA = "palavra_vazia"
MARCADOR_IA = "marcador_ia"
VOZ_PASSIVA = "voz_passiva"
ADVERBIO_MENTE = "adverbios_em_mente"
ADJETIVACAO = "adjetivacao_excessiva"
NOMINALIZACAO = "nominalizacao"
FRASE_LONGA = "frase_longa"
QUEISMO = "queismo"
REPETICAO = "repeticao_lexical"

ROTULOS_CATEGORIA = {
    GERUNDISMO: "Gerundismo",
    PLEONASMO: "Pleonasmo vicioso",
    CLICHE: "Clichês e frases feitas",
    PALAVRA_VAZIA: "Palavras vazias / corporativês",
    MARCADOR_IA: "Marcadores de texto gerado por IA",
    VOZ_PASSIVA: "Voz passiva",
    ADVERBIO_MENTE: "Acúmulo de advérbios em -mente",
    ADJETIVACAO: "Adjetivação excessiva",
    NOMINALIZACAO: "Nominalização (substantivos rastejantes)",
    FRASE_LONGA: "Frase muito longa",
    QUEISMO: "Queísmo (acúmulo de 'que')",
    REPETICAO: "Repetição lexical",
}


@dataclass
class Ocorrencia:
    """Uma detecção pontual, com lastro na regra que a produziu."""

    regra_id: str            # identificador estável da regra (ex.: "rx_gerundismo_ir")
    categoria: str           # uma das constantes de categoria acima
    severidade: str          # atencao | sugestao | informativo
    trecho: str              # o segmento de texto sinalizado
    inicio: int              # offset de caractere no texto original
    fim: int                 # offset final (exclusivo)
    explicacao: str          # por que isto foi sinalizado
    sugestao: str            # o que fazer a respeito
    camada: str              # "regex" | "spacy"
    contexto: str = ""       # frase (ou recorte) em que o trecho aparece

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Resultado:
    """Resultado completo de uma análise: ocorrências + estatísticas."""

    texto: str
    ocorrencias: list[Ocorrencia]
    estatisticas: dict[str, Any] = field(default_factory=dict)
    modo_pipeline: str = "completo"   # "completo" (modelo treinado) | "reduzido" (blank)
    regras_inativas: list[str] = field(default_factory=list)

    def como_dict(self) -> dict[str, Any]:
        return {
            "modo_pipeline": self.modo_pipeline,
            "regras_inativas": self.regras_inativas,
            "estatisticas": self.estatisticas,
            "ocorrencias": [o.como_dict() for o in self.ocorrencias],
        }

    def por_categoria(self) -> dict[str, list[Ocorrencia]]:
        grupos: dict[str, list[Ocorrencia]] = {}
        for o in self.ocorrencias:
            grupos.setdefault(o.categoria, []).append(o)
        return grupos
