"""Demonstração do Machado.

Analisa cinco textos de perfis diferentes, guardados em exemplos/:
um comunicado corporativo carregado de desvios, um texto com cara de
saída de modelo de linguagem, um trecho acadêmico, uma nota
jornalística razoável e um texto enxuto. A tabela comparativa mostra
como o perfil de cada um aparece nos números; o relatório completo do
primeiro mostra o diagnóstico em detalhe.

Uso:  python demo.py
"""

from pathlib import Path

from machado import MotorEstilo

PASTA_EXEMPLOS = Path(__file__).parent / "exemplos"

ORDEM = [
    ("corporativo", "comunicado corporativo"),
    ("gerado_ia", "texto com cara de LLM"),
    ("academico", "trecho acadêmico"),
    ("jornalistico", "nota jornalística"),
    ("limpo", "texto enxuto"),
]


def main() -> None:
    motor = MotorEstilo()
    resultados = {}

    for nome, _ in ORDEM:
        texto = (PASTA_EXEMPLOS / f"{nome}.txt").read_text(encoding="utf-8")
        resultados[nome] = motor.analisar(texto)

    # ------------------------------------------------------------- tabela
    print()
    print(f"{'texto':<14} {'palavras':>8} {'ocorr.':>7} {'/1000':>7} "
          f"{'atenção':>8} {'sotaque IA':>11}")
    print("-" * 60)
    for nome, descricao in ORDEM:
        e = resultados[nome].estatisticas
        print(f"{nome:<14} {e['palavras']:>8} {e['total_ocorrencias']:>7} "
              f"{e['ocorrencias_por_1000_palavras']:>7} "
              f"{e['por_severidade']['atencao']:>8} "
              f"{e['indice_sotaque_ia_por_1000_palavras']:>11}")
    print()

    # ------------------------------------- relatório completo de um deles
    print("Relatório completo do texto corporativo:")
    print()
    print(motor.relatorio(resultados["corporativo"]))

    # ----------------------------------------------------- saída em JSON
    caminho_json = Path("machado_resultado.json")
    caminho_json.write_text(
        motor.para_json(resultados["corporativo"]), encoding="utf-8"
    )
    print(f"\nJSON estruturado salvo em {caminho_json}")


if __name__ == "__main__":
    main()
