"""Machado — motor de revisão estilística para o português brasileiro.

Duas camadas (regex + SpaCy), saída explicável, regras como dados.
O nome homenageia Machado de Assis e descreve a função: cortar excesso.
"""

from .motor import MotorEstilo, ConfigMotor
from .tipos import Ocorrencia, Resultado

__version__ = "0.1.0"
__all__ = ["MotorEstilo", "ConfigMotor", "Ocorrencia", "Resultado", "__version__"]
