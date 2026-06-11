# Roteiro de apresentação — 10 minutos

## 1. Abertura (1 min)

Uma frase, sem preâmbulo: "Construí uma miniatura do núcleo de um revisor de
estilo para PT-BR — duas camadas, regex e SpaCy, saída explicável — para
discutir decisões de arquitetura com vocês." Isso responde, em ato, à
pergunta da entrevista sobre regex, Python e SpaCy.

## 2. Demo ao vivo (3 min)

Rodar `python demo.py` na frente dele. O contraste fala sozinho:

- Texto 1 (release corporativo/IA): ~24 ocorrências, 10 categorias,
  índice de sotaque de IA ≈ 52/1000 palavras.
- Texto 2 (enxuto): zero.

Depois, uma frase dele mesmo no CLI:
`python -m machado "Vou estar te enviando o relatório que foi escrito há dias atrás."`
— três camadas de problema numa frase de onze palavras.

## 3. Abrir UMA regra no código (2 min)

Abrir `regras_regex.py` na regra do travessão parentético e mostrar três
coisas em sequência:

1. **Regra é dado**: o catálogo cresce sem tocar no motor.
2. **O filtro contextual**: travessão de diálogo (uso canônico do PT-BR)
   não dispara; só o travessão intercalado à moda anglófona. É o tipo de
   distinção que separa regra linguística de regex ingênuo.
3. **A explicação viaja com a detecção**: o JSON sai pronto para sublinhar
   num editor, com offsets, justificativa e sugestão.

## 4. O diferencial (2 min)

A categoria de marcadores de IA + o índice de sotaque. Moldura honesta:
não é detector de autoria, é medidor de cacoete — e por isso é útil para
um produto de *humanização*: antes de reescrever, o sistema sabe o que soa
a máquina e onde. Conecta com a tese do material sobre o travessão como
marcador estilístico de LLM em PT-BR.

## 5. Limites e a ponte para o LLM (1 min)

Dizer espontaneamente o que regras NÃO fazem (adequação, intenção,
reescrita) e onde o modelo entra: o diagnóstico do motor vira instrução
verificável para a reescrita por LLM. Mostrar que se sabe o limite da
ferramenta vale mais do que a ferramenta.

## 6. Perguntas para fazer a ele (1 min)

- Hoje, qual a divisão real entre regras e modelo no pipeline de vocês —
  e quem escreve as regras?
- Como vocês medem falso positivo das dicas de estilo em produção?
- No LLM próprio: a camada de regras vira dado de treino (sinal de
  preferência) ou continua como pós-processamento?

Perguntas assim demonstram mais conhecimento do que qualquer afirmação.

## Anti-checklist

- Não pedir desculpas pelo escopo ("é só um protótipo..."). É uma miniatura
  deliberada; os limites estão documentados.
- Não prometer que regras resolvem tudo — o argumento é a divisão de
  trabalho, não a suficiência.
- Não chamar o índice de "detector de IA" em nenhuma hipótese.
