"""Uso via linha de comando:

    python -m machado "Vou estar enviando o relatório."
    cat texto.txt | python -m machado
    python -m machado --json "texto..."
"""

import sys

from .motor import MotorEstilo


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--json"]
    como_json = "--json" in sys.argv

    texto = " ".join(args) if args else sys.stdin.read()
    if not texto.strip():
        print("Uso: python -m machado [--json] \"texto\"  (ou via stdin)")
        sys.exit(1)

    motor = MotorEstilo()
    resultado = motor.analisar(texto)
    print(motor.para_json(resultado) if como_json else motor.relatorio(resultado))


if __name__ == "__main__":
    main()
