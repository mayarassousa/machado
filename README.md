# Machado

Motor de revisão estilística para o português brasileiro. Duas camadas — regex
para padrões de superfície, SpaCy para padrões morfossintáticos — e uma saída
explicável: cada sinalização carrega a regra que a produziu, o porquê e a
sugestão de correção.

O nome é uma homenagem a Machado de Assis e, ao mesmo tempo, uma descrição da
tarefa: cortar o que sobra.

## A ideia

Boa parte dos vícios de escrita — gerundismo, pleonasmo, clichê, queísmo, nominalização — tem forma fixa. 
Para esse tipo de desvio, uma regra bem escrita resolve, e resolve melhor do que um modelo grande, por motivos práticos:
- **precisão controlável**: cada regra é testável isoladamente, com casos positivos e negativos (a suíte deste projeto tem 25 testes);
- **custo marginal próximo de zero**:  nada de inferência por token; o motor inteiro roda em milissegundos em CPU;
- **explicabilidade por construção**: a saída é um diagnóstico, mostra a regra, posição, justificativa, sugestão;
- **manutenção previsível**: corrigir um falso positivo é editar uma regra, não retreinar um modelo.

O Machado é só, como o próprio nome demostra, uma ferramenta simples, não substitui um modelo de linguagem ele só entra onde a regra alcança.

## Arquitetura

```
texto
  │
  ├── Camada 1 · regex (regras_regex.py)
  │     padrões de superfície declarados como dados:
  │     gerundismo, pleonasmos, clichês, palavras vazias,
  │     marcadores de texto gerado por IA
  │
  ├── Camada 2 · SpaCy (regras_spacy.py)
  │     padrões que exigem estrutura: voz passiva, nominalização,
  │     frases longas, queísmo, repetição lexical, advérbios em
  │     -mente, adjetivação excessiva
  │
  └── Motor (motor.py)
        ordena, calcula estatísticas e emite:
        relatório legível  ·  JSON estruturado por ocorrência
```

O projeto se organiza em torno de algumas escolhas.
As regras da primeira camada são tratadas como dados. 
Cada uma é uma entrada com identificador, padrão, categoria, severidade, explicação e sugestão. 
Para adicionar uma nova dica de estilo, basta acrescentar mais um item à lista; o motor que aplica as regras não muda. 
Quando o padrão sozinho não basta — por exemplo, um travessão em linha de diálogo é legítimo, mas o mesmo travessão no meio de um parágrafo costuma ser cacoete — a regra pode incluir uma função de filtro que decide se o casamento conta ou não.

A segunda camada usa spaCy e cada regra declara de que partes do pipeline ela precisa. Se o modelo treinado de português estiver instalado, todas as regras funcionam, e as que dependem de classe gramatical ou morfologia ficam mais precisas. Se não estiver, o motor cai num pipeline mínimo (só tokenizador e segmentador de frases), as regras que ainda funcionam continuam ativas, e o relatório lista no início quais ficaram desligadas. A ideia é não esconder do usuário o que não foi analisado.

A terceira escolha é privilegiar precisão. Uma ferramenta que aponta erros onde não há tende a perder credibilidade rápido, então os limiares são conservadores e podem ser ajustados e várias regras carregam exceções para os falsos positivos mais comuns. A severidade também separa três coisas que costumam ser confundidas: o que é desvio da norma, o que é uma escolha que costuma enfraquecer o texto e o que é legítimo, mas pode incomodar quando aparece em excesso.

## O que ele detecta hoje

Doze categorias, escolhidas por sobreposição com o repertório clássico de
desvios da escrita profissional em PT-BR: gerundismo; pleonasmos viciosos; clichês e muletas;
palavras vazias de corporativês; voz passiva; nominalização com verbo-suporte; frases longas; queísmo;
acúmulo de advérbios em *-mente*; adjetivação excessiva; repetição lexical em janela curta; e **marcadores de texto gerado por IA**.

### A categoria diferencial: marcadores de IA

A última categoria trata texto gerado por LLM como **variedade linguística
com traços descritíveis**: o travessão parentético à moda anglófona, as
estruturas contrastivas formulaicas ("não é apenas X, é Y"), o metadiscurso
de preenchimento, as aberturas de ambientação, as colocações de relevância vazia e os vestígios de chat que sobrevivem ao copiar-e-colar.

O motor agrega isso num **índice de sotaque de IA** (ocorrências por mil
palavras). 
**não é um detector de IA**.
Texto humano pode pontuar alto e mereceria revisão do mesmo jeito; texto
gerado e bem editado pontua baixo — que é exatamente o objetivo de quem usa
uma ferramenta de humanização.
O índice mede sotaque, não autoria.
O uso prático é como ponto de partida para humanizar texto. 
Antes de reescrever um rascunho para soar mais natural, é útil saber o que está fazendo ele soar artificial e em que pontos. 
O índice dá esse mapa.

## Instalação e uso

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm   # opcional, ativa as regras de POS

python demo.py                              # demonstração com dois textos
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
motor.para_json(resultado)            # pronto para uma API ou um editor
```

Cada ocorrência no JSON traz: `regra_id`, `categoria`, `severidade`,
`trecho`, `inicio`/`fim` (offsets de caractere, prontos para sublinhar num
editor), `explicacao`, `sugestao`, `camada` e `contexto`.

## Limites — e onde entra o aprendizado de máquina

Regras detectam **forma**; não detectam **adequação**. Os limites são
conhecidos e assumidos:

- A voz passiva é sinalizada como informação porque é legítima quando o
  agente não importa — decidir *quando* ela enfraquece o texto exige
  contexto discursivo, não padrão.
- Repetição pode ser anáfora retórica deliberada; o motor sinaliza o eco,
  não a intenção.
- O índice de sotaque de IA mede densidade de cacoetes, não autoria.
- Regras não geram a reescrita; apontam o problema e a direção.

É exatamente nesses pontos que um modelo entra com vantagem: um classificador
de contexto para arbitrar sinalizações ambíguas (passiva ruim vs. passiva
funcional), ranqueamento de sugestões e a reescrita propriamente dita por
LLM — **condicionada pelo diagnóstico do motor**, que transforma "reescreva
melhor" em instruções verificáveis ("elimine o gerundismo em 60–80; quebre
o período de 49 palavras em 352–690"). O motor barato e auditável vira a
camada de controle do modelo caro e criativo: cada um faz o que faz melhor.

## Estrutura do projeto

```
machado/
├── machado/
│   ├── tipos.py          # Ocorrencia, Resultado, severidades, categorias
│   ├── regras_regex.py   # Camada 1 — base declarativa de regras
│   ├── regras_spacy.py   # Camada 2 — regras morfossintáticas capability-aware
│   ├── motor.py          # orquestração, estatísticas, relatório, JSON
│   └── __main__.py       # CLI
├── demo.py               # demonstração com textos contrastantes
├── tests/test_machado.py # 25 testes (casos positivos e anti-falso-positivo)
└── requirements.txt
```
