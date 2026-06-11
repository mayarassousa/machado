"""Motor do Machado: orquestra as duas camadas e produz a saída explicável.

Fluxo: texto → [Camada 1: regex] + [Camada 2: SpaCy] → ocorrências
ordenadas + estatísticas → relatório legível ou JSON estruturado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .tipos import (
    Ocorrencia, Resultado,
    ROTULOS_CATEGORIA, ROTULOS_SEVERIDADE,
    MARCADOR_IA, ATENCAO, SUGESTAO, INFORMATIVO,
)
from .regras_regex import aplicar_regras_regex
from .regras_spacy import carregar_nlp, aplicar_regras_spacy, MODELO_PADRAO


@dataclass
class ConfigMotor:
    """Limiares das regras estruturais. Tudo que é arbitrário é configurável."""
    max_palavras_frase: int = 30
    min_que_por_frase: int = 4
    min_adverbios_mente: int = 2
    min_adjetivos_frase: int = 4
    min_repeticoes: int = 3
    janela_repeticao: int = 60   # em tokens
    modelo: str = MODELO_PADRAO


class MotorEstilo:
    """API principal.

    >>> motor = MotorEstilo()
    >>> resultado = motor.analisar("Vou estar enviando o relatório.")
    >>> resultado.ocorrencias[0].categoria
    'gerundismo'
    """

    def __init__(self, config: ConfigMotor | None = None):
        self.config = config or ConfigMotor()
        self.nlp, self.modo = carregar_nlp(self.config.modelo)

    # ------------------------------------------------------------------ #

    def analisar(self, texto: str) -> Resultado:
        doc = self.nlp(texto)

        ocorrencias = aplicar_regras_regex(texto)
        ocs_spacy, inativas = aplicar_regras_spacy(doc, self.config, self.modo)
        ocorrencias.extend(ocs_spacy)
        ocorrencias.sort(key=lambda o: (o.inicio, o.fim))

        estatisticas = self._estatisticas(doc, ocorrencias)
        return Resultado(
            texto=texto,
            ocorrencias=ocorrencias,
            estatisticas=estatisticas,
            modo_pipeline=self.modo,
            regras_inativas=inativas,
        )

    # ------------------------------------------------------------------ #

    def _estatisticas(self, doc, ocorrencias: list[Ocorrencia]) -> dict:
        palavras = [t for t in doc if t.is_alpha]
        n_palavras = len(palavras) or 1
        frases = list(doc.sents)
        n_frases = len(frases) or 1

        por_categoria: dict[str, int] = {}
        por_severidade: dict[str, int] = {ATENCAO: 0, SUGESTAO: 0, INFORMATIVO: 0}
        for o in ocorrencias:
            por_categoria[o.categoria] = por_categoria.get(o.categoria, 0) + 1
            por_severidade[o.severidade] = por_severidade.get(o.severidade, 0) + 1

        n_ia = por_categoria.get(MARCADOR_IA, 0)
        return {
            "palavras": n_palavras,
            "frases": n_frases,
            "media_palavras_por_frase": round(n_palavras / n_frases, 1),
            "total_ocorrencias": len(ocorrencias),
            "ocorrencias_por_1000_palavras": round(len(ocorrencias) / n_palavras * 1000, 1),
            "por_severidade": por_severidade,
            "por_categoria": por_categoria,
            # Densidade de cacoetes associados a texto gerado. NÃO é um
            # detector de IA: é um medidor de sotaque. Texto humano pode
            # pontuar alto (e mereceria revisão do mesmo jeito); texto
            # gerado e bem editado pontua baixo — que é o objetivo.
            "indice_sotaque_ia_por_1000_palavras": round(n_ia / n_palavras * 1000, 1),
        }

    # ------------------------------------------------------------------ #

    def relatorio(self, resultado: Resultado) -> str:
        """Relatório legível para terminal — a versão humana do JSON."""
        e = resultado.estatisticas
        linhas: list[str] = []
        add = linhas.append

        add("=" * 72)
        add("MACHADO — análise estilística (PT-BR)")
        add(f"pipeline: {resultado.modo_pipeline}"
            + (f"  |  regras inativas: {', '.join(resultado.regras_inativas)}"
               if resultado.regras_inativas else ""))
        add("=" * 72)
        add(f"{e['palavras']} palavras | {e['frases']} frases | "
            f"média de {e['media_palavras_por_frase']} palavras/frase")
        add(f"{e['total_ocorrencias']} ocorrências "
            f"({e['ocorrencias_por_1000_palavras']}/1000 palavras) — "
            f"atenção: {e['por_severidade'][ATENCAO]}, "
            f"sugestão: {e['por_severidade'][SUGESTAO]}, "
            f"info: {e['por_severidade'][INFORMATIVO]}")
        add(f"índice de sotaque de IA: "
            f"{e['indice_sotaque_ia_por_1000_palavras']}/1000 palavras")
        add("")

        if not resultado.ocorrencias:
            add("Nenhum desvio detectado pelas regras ativas.")
            return "\n".join(linhas)

        for categoria, grupo in resultado.por_categoria().items():
            add(f"--- {ROTULOS_CATEGORIA.get(categoria, categoria)} "
                f"({len(grupo)}) " + "-" * 20)
            for o in grupo:
                add(f"  [{ROTULOS_SEVERIDADE[o.severidade]}] “{o.trecho}”")
                add(f"      contexto : {o.contexto}")
                add(f"      por quê  : {o.explicacao}")
                add(f"      sugestão : {o.sugestao}")
                add(f"      regra    : {o.regra_id} (camada {o.camada}, "
                    f"posição {o.inicio}–{o.fim})")
            add("")
        return "\n".join(linhas)

    def para_json(self, resultado: Resultado, indentado: bool = True) -> str:
        return json.dumps(
            resultado.como_dict(),
            ensure_ascii=False,
            indent=2 if indentado else None,
        )
