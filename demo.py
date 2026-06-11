"""Demonstração do Machado.

Dois textos de mesmo assunto: o primeiro escrito como sai de muita
ferramenta de geração (ou de muito comunicado corporativo); o segundo,
como Graciliano mandaria escrever. A diferença entre os dois relatórios
é o argumento do projeto.

Uso:  python demo.py
"""

import json

from machado import MotorEstilo

TEXTO_CARREGADO = """No cenário atual, é importante ressaltar que a nossa \
equipe vai estar realizando a implementação da nova solução tecnológica \
inovadora, robusta e disruptiva nos próximos dias. A decisão foi tomada pela \
diretoria há alguns meses atrás, e o projeto — que representa um divisor de \
águas para a empresa — não é apenas uma atualização, é uma transformação. \
Vale destacar que o sistema desempenha um papel fundamental na otimização \
dos processos que sustentam a operação, que, segundo a equipe que conduziu \
a análise que foi realizada no trimestre passado, vai estar gerando \
resultados que certamente serão percebidos rapidamente e amplamente pelos \
clientes que utilizam a plataforma diariamente. Antes de mais nada, \
precisamos planejar com antecedência a realização da migração do \
atendimento, pois a equipe de atendimento informou que o atendimento atual \
apresenta falhas através do canal digital."""

TEXTO_ENXUTO = """A diretoria aprovou o novo sistema em março. A equipe \
implanta a primeira etapa nesta semana e mede os resultados no fim do mês. \
Se algo falhar, voltamos ao plano anterior. O suporte responde os chamados \
em até quatro horas."""


def main() -> None:
    motor = MotorEstilo()

    print("\n############ TEXTO 1 — carregado de desvios ############\n")
    resultado_1 = motor.analisar(TEXTO_CARREGADO)
    print(motor.relatorio(resultado_1))

    print("\n############ TEXTO 2 — enxuto ############\n")
    resultado_2 = motor.analisar(TEXTO_ENXUTO)
    print(motor.relatorio(resultado_2))

    # Saída estruturada: é isto que uma API/editor consumiria.
    with open("machado_resultado.json", "w", encoding="utf-8") as f:
        f.write(motor.para_json(resultado_1))
    print("\nJSON estruturado do Texto 1 salvo em machado_resultado.json")

    # Comparativo final
    e1, e2 = resultado_1.estatisticas, resultado_2.estatisticas
    print("\nComparativo (ocorrências por 1000 palavras):")
    print(f"  Texto 1: {e1['ocorrencias_por_1000_palavras']:>6}  "
          f"| sotaque de IA: {e1['indice_sotaque_ia_por_1000_palavras']}")
    print(f"  Texto 2: {e2['ocorrencias_por_1000_palavras']:>6}  "
          f"| sotaque de IA: {e2['indice_sotaque_ia_por_1000_palavras']}")


if __name__ == "__main__":
    main()
