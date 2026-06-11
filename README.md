# Machado

Um revisor de estilo para o português brasileiro. Ele lê um texto e aponta os
lugares onde a escrita trava — gerundismo, pleonasmo, clichê, voz passiva,
frase longa demais — explicando o que encontrou e por quê. Duas camadas fazem
o trabalho: expressões regulares para os padrões de superfície e spaCy para o
que depende de análise gramatical.

O nome é uma homenagem a Machado de Assis e, ao mesmo tempo, uma descrição da
tarefa: cortar o que sobra.

## A ideia

Boa parte dos vícios de escrita tem forma fixa. "Vou estar enviando" é
gerundismo em qualquer contexto; "há anos atrás" é redundante sempre; "no
cenário atual" abre parágrafo sem dizer nada, apareça onde aparecer. Para esse
tipo de desvio, uma regra bem escrita resolve — e resolve melhor do que um
modelo grande, por motivos práticos:

- dá para testar cada regra isoladamente, com exemplos do que ela deve e do
  que ela não deve pegar (o projeto tem 25 testes nesse espírito);
- o custo é quase nulo: nada de inferência, roda em milissegundos na CPU;
- a saída é um diagnóstico, não uma probabilidade — você sabe qual regra
  disparou, onde, e o que ela sugere;
- corrigir um falso positivo é editar uma linha, não retreinar nada.

Nada disso substitui um modelo de linguagem; o que faz é delimitar o que ele
precisa fazer. Onde existe ambiguidade de verdade — e existe —, o lugar é dele.
Para o resto, regra basta.

## Como funciona

```
texto
  │
  ├── Camada 1 · regex (regras_regex.py)
  │     padrões de superfície declarados como dados:
  │     gerundismo, pleonasmos, clichês, palavras vazias,
  │     marcadores de texto gerado por IA
  │
  ├── Camada 2 · spaCy (regras_spacy.py)
  │     o que precisa de estrutura: voz passiva, nominalização,
  │     frases longas, queísmo, repetição lexical, advérbios em
  │     -mente, adjetivação excessiva
  │
  └── Motor (motor.py)
        ordena, calcula estatísticas e devolve:
        relatório legível  ·  JSON estruturado por ocorrência
```

Três decisões organizam o código.

**Regra é dado.** Cada regra da primeira camada é uma entrada declarativa: um
identificador, o padrão, a categoria, a severidade, a explicação e a sugestão.
Acrescentar a décima terceira ou a centésima dica de estilo não mexe no motor —
mexe na lista de regras. Quando o padrão sozinho não dá conta (um travessão de
diálogo é legítimo; um travessão no meio do parágrafo, à moda inglesa, é
cacoete), a regra aceita um filtro de contexto. Continua declarativa, mas ganha
o veto que a expressão regular não expressa.

**O motor sabe do que é capaz.** A segunda camada depende do spaCy, e cada
regra dela declara o que precisa do pipeline. Com o modelo treinado de
português, tudo funciona, com classe gramatical e morfologia afinando as
heurísticas. Sem o modelo — só com o tokenizador e o segmentador de frases —,
as regras lexicais e estruturais continuam de pé, e o relatório avisa o que
ficou de fora em vez de fingir que analisou. Na prática, isso permite uma
primeira passada barata em muito texto e o pipeline pesado só onde ele importa.

**Precisão antes de cobertura.** Um revisor que acusa o que não é erro perde a
confiança de quem usa. Por isso os limiares são conservadores e configuráveis,
os padrões carregam defesas contra os falsos positivos clássicos (adjetivos em
*-ido* que não são particípios; "ao mesmo tempo", que não é o "o mesmo"
burocrático), e a severidade separa três coisas diferentes: o que é desvio de
norma, o que é escolha que enfraquece o texto e o que é legítimo mas vira
problema na dose.

## O que ele detecta

Doze categorias: gerundismo; pleonasmo ("há anos atrás", "subir para cima",
"conclusão final"); clichês e muletas ("antes de mais nada", "através de" como
meio, "o mesmo" pronominal); palavras de corporativês; voz passiva;
nominalização ("realizar a implementação" no lugar de "implementar"); frase
longa; queísmo; acúmulo de advérbios em *-mente*; excesso de adjetivos;
repetição de palavra em espaço curto; e marcadores de texto gerado por IA.

### Os marcadores de IA

A última categoria trata a escrita de modelos de linguagem como o que ela é:
uma variedade com traços reconhecíveis. O travessão parentético à moda inglesa,
as estruturas de contraste em fôrma ("não é apenas X, é Y"), o metadiscurso de
enchimento ("é importante ressaltar que"), as aberturas genéricas ("no cenário
atual"), as colocações de relevância vazia ("desempenha um papel fundamental"),
os restos de conversa que escapam no copia-e-cola.

O motor junta tudo isso num índice — ocorrências por mil palavras. E aqui vale
a ressalva, que é parte do desenho e não rodapé: isto não é um detector de IA.
É um medidor de sotaque. Texto escrito por gente pode pontuar alto, e mereceria
revisão do mesmo jeito; texto gerado e bem editado pontua baixo, que é
justamente o objetivo de quem reescreve para soar humano. O índice mede o
cacoete, não a autoria. Como ponto de partida para humanizar um texto, serve:
antes de reescrever, dá para saber o que soa a máquina e onde.

## Uso

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm   # opcional; ativa as regras que usam classe gramatical

python demo.py                              # demonstração com dois textos contrastantes
python -m machado "Vou estar enviando o relatório que foi escrito há dias atrás."
python -m machado --json "..."              # saída estruturada
pytest -q                                   # 25 testes
```

Como biblioteca:

```python
from machado import MotorEstilo, ConfigMotor

motor = MotorEstilo(ConfigMotor(max_palavras_frase=25))
resultado = motor.analisar(texto)

resultado.ocorrencias[0].categoria    # "gerundismo"
resultado.estatisticas["indice_sotaque_ia_por_1000_palavras"]
motor.para_json(resultado)
```

Cada ocorrência no JSON traz o identificador da regra, a categoria, a
severidade, o trecho, os offsets de caractere (prontos para sublinhar num
editor), a explicação, a sugestão, a camada e o contexto.

## O que ele não faz

Regras enxergam forma, não adequação. Os limites são conhecidos e assumidos: a
voz passiva entra como informação porque às vezes é a escolha certa — decidir
quando ela atrapalha pede um contexto que o padrão não tem. A repetição pode
ser ênfase deliberada; o motor marca o eco, não a intenção. O índice de sotaque
mede densidade de cacoete, não quem escreveu. E nada disso reescreve o texto:
aponta o problema e a direção.

É justamente nesses pontos que um modelo entra com vantagem — para arbitrar os
casos ambíguos (passiva ruim ou passiva funcional?), ordenar sugestões e fazer
a reescrita propriamente dita, agora guiada pelo diagnóstico. O diagnóstico
transforma "escreva melhor" em instrução verificável: "tire o gerundismo na
posição 60–80; quebre o período de 49 palavras". A camada barata e auditável
vira o controle da camada cara e criativa.

## Estrutura

```
machado/
├── machado/
│   ├── tipos.py          # Ocorrencia, Resultado, severidades, categorias
│   ├── regras_regex.py   # Camada 1 — base declarativa de regras
│   ├── regras_spacy.py   # Camada 2 — regras morfossintáticas
│   ├── motor.py          # orquestração, estatísticas, relatório, JSON
│   ├── __init__.py
│   └── __main__.py       # interface de linha de comando
├── demo.py               # demonstração com textos contrastantes
├── tests/test_machado.py # 25 testes (casos positivos e anti-falso-positivo)
└── requirements.txt
```

## Licença

MIT.
