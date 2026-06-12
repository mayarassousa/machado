---
title: Machado
emoji: 🪓
colorFrom: purple
colorTo: pink
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: Revisor estilístico explicável para PT-BR.
tags:
  - gradio
  - nlp
  - portuguese
  - text-analysis
  - explainable-ai
---
# Machado

Motor de revisão estilística para o português brasileiro. Duas camadas — regex
para padrões de superfície, spaCy para padrões morfossintáticos — e uma saída
explicável: cada sinalização carrega a regra que a produziu, o porquê e a
sugestão de correção.

O nome é uma homenagem a Machado de Assis e, ao mesmo tempo, uma descrição da
tarefa: cortar o que sobra.

## A ideia

Boa parte dos vícios de escrita — gerundismo, pleonasmo, clichê, queísmo,
nominalização — tem forma suficientemente estável para ser capturada por
padrão de superfície. Para esse tipo de desvio, uma regra bem escrita resolve,
com vantagens práticas que um modelo grande não oferece nessa classe de
problema:

- **precisão controlável**: cada regra é testável isoladamente, com casos positivos e negativos (a suíte deste projeto tem 36 testes);
- **custo computacional baixo**: nada de inferência de modelo; o motor inteiro roda em milissegundos em CPU;
- **explicabilidade por construção**: a saída é um diagnóstico, mostra a regra, posição, justificativa, sugestão;
- **manutenção previsível**: corrigir um falso positivo é editar uma regra, não retreinar um modelo.

O Machado é, como o próprio nome sugere, uma ferramenta simples. Não substitui
um modelo de linguagem: só atua onde a regra alcança. O resto, como saber se
uma voz passiva funciona naquele parágrafo ou se uma repetição é ênfase ou
descuido, depende de contexto, e fica para outra ferramenta.

## Arquitetura

```
texto
  │
  ├── Camada 1 · regex (regras_regex.py)
  │     padrões de superfície declarados como dados:
  │     gerundismo, pleonasmos, clichês, palavras vazias,
  │     marcadores de texto gerado por IA
  │
  ├── Camada 2 · spaCy (regras_spacy.py)
  │     padrões que exigem estrutura: voz passiva, nominalização,
  │     frases longas, queísmo, repetição lexical, advérbios em
  │     -mente, adjetivação excessiva
  │
  └── Motor (motor.py)
        ordena, calcula estatísticas e emite:
        relatório legível  ·  JSON estruturado por ocorrência
```

O projeto se organiza em torno de algumas escolhas.

As regras da primeira camada são tratadas como dados. Cada uma é uma entrada
com identificador, padrão, categoria, severidade, explicação e sugestão. Para
adicionar uma nova dica de estilo, basta acrescentar mais um item à lista; o
motor que aplica as regras não muda. Quando o padrão sozinho não basta — por
exemplo, um travessão em linha de diálogo é legítimo, mas o mesmo travessão no
meio de um parágrafo costuma ser cacoete — a regra pode incluir uma função de
filtro que decide se o casamento conta ou não.

A segunda camada usa spaCy e cada regra declara de que partes do pipeline ela
precisa. Se o modelo treinado de português estiver instalado, todas as regras
funcionam, e as que dependem de classe gramatical ou morfologia ficam mais
precisas. Se não estiver, o motor cai num pipeline mínimo (só tokenizador e
segmentador de frases), as regras que ainda funcionam continuam ativas, e o
relatório lista no início quais ficaram desligadas. A ideia é não esconder do
usuário o que não foi analisado.

A terceira escolha é privilegiar precisão. Uma ferramenta que aponta erros
onde não há tende a perder credibilidade rápido, então os limiares são
conservadores e podem ser ajustados e várias regras carregam exceções para os
falsos positivos mais comuns. A severidade também separa três coisas que
costumam ser confundidas: o que é desvio da norma, o que é uma escolha que
costuma enfraquecer o texto e o que é legítimo, mas pode incomodar quando
aparece em excesso.

## O que ele detecta hoje

Doze categorias, escolhidas por sobreposição com o repertório clássico de
desvios da escrita profissional em PT-BR: gerundismo; pleonasmos viciosos;
clichês e muletas; palavras vazias de corporativês; voz passiva; nominalização
com verbo-suporte; frases longas; queísmo; acúmulo de advérbios em *-mente*;
adjetivação excessiva; repetição lexical em janela curta; e **marcadores de
texto gerado por IA**.

### Os marcadores de IA

A última categoria trata texto gerado por LLM como **variedade linguística com
traços descritíveis**: o travessão parentético à moda anglófona, as estruturas
contrastivas formulaicas ("não é apenas X, é Y"), o metadiscurso de
preenchimento, as aberturas de ambientação, as colocações de relevância vazia
e os vestígios de chat que sobrevivem ao copiar-e-colar.

Cada uma dessas regras, sozinha, é fraca como evidência. "É importante
ressaltar que" aparece em texto humano também, e o travessão parentético é uma
escolha legítima de quem usa por estilo. O que conta é a densidade: quando
vários desses traços aparecem juntos e em frequência alta, o texto começa a
soar como saída de modelo.

O motor soma as ocorrências da categoria, divide pelo total de palavras e
multiplica por mil. O resultado é o índice de sotaque de IA, e o nome importa,
porque é fácil entender errado o que ele mede.

Esse índice não é um detector de IA. Não tenta classificar o texto como humano
ou máquina — esse tipo de ferramenta existe, funciona de forma diferente e tem
limitações sérias. O que o índice mede é outra coisa: o quanto o texto tem de
cacoete de modelo de linguagem. Texto humano pode pontuar alto se a pessoa
escrever com muito metadiscurso e muita abertura genérica; nesse caso, o
índice está certo, e o texto merece revisão. Texto gerado e bem editado pode
pontuar baixo, porque os cacoetes foram removidos; nesse caso, também está
certo. O índice mede sotaque, não autoria.

O uso prático é como ponto de partida para humanizar texto. Antes de
reescrever um rascunho para soar mais natural, é útil saber o que está fazendo
ele soar artificial e em que pontos. O índice dá esse mapa.

## Demo

O arquivo `app.py` publica o motor como aplicação web (Gradio), no formato
que o Hugging Face Spaces executa direto do repositório. A interface destaca
os desvios pontuais no próprio texto, lista as observações por frase, mostra
a tabela completa de ocorrências e a saída JSON. No Spaces, o modelo
`pt_core_news_sm` é instalado junto com as dependências, então a demo
pública roda com todas as regras ativas.

## Instalação e uso

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm   # opcional, ativa as regras de POS

python demo.py                              # analisa os cinco textos de exemplos/
python app.py                               # interface web (Gradio) em http://localhost:7860
python -m machado "Vou estar enviando o relatório que foi escrito há dias atrás."
python -m machado --json "..."              # saída estruturada
pytest -q                                   # 36 testes
```

A pasta `exemplos/` traz cinco textos de perfis diferentes — um comunicado
corporativo carregado, um texto com cara de saída de LLM, um trecho acadêmico,
uma nota jornalística e um texto enxuto. O demo analisa todos e imprime uma
tabela comparativa; é uma boa forma de ver o que cada métrica captura. O
acadêmico, por exemplo, acumula desvios mas tem sotaque de IA zero, e o texto
gerado tem o maior índice da amostra: as duas medidas dizem coisas diferentes.

Como biblioteca:

```python
from machado import MotorEstilo, ConfigMotor

motor = MotorEstilo(ConfigMotor(max_palavras_frase=25))
resultado = motor.analisar(texto)

resultado.ocorrencias[0].categoria    # "gerundismo"
resultado.estatisticas["indice_sotaque_ia_por_1000_palavras"]
motor.para_json(resultado)            # pronto para uma API ou um editor
```

Cada ocorrência no JSON traz: `regra_id`, `categoria`, `severidade`, `trecho`,
`inicio`/`fim` (offsets de caractere, prontos para sublinhar num editor),
`explicacao`, `sugestao`, `camada` e `contexto`.

## Limites — e onde entra o aprendizado de máquina

Regras detectam **forma**; não detectam **adequação**. Os limites são
conhecidos e assumidos:

- A voz passiva é sinalizada como informação porque é legítima quando o agente não importa — decidir *quando* ela enfraquece o texto exige contexto discursivo, não padrão.
- Repetição pode ser anáfora retórica deliberada; o motor sinaliza o eco, não a intenção.
- O índice de sotaque de IA mede densidade de cacoetes, não autoria.
- Regras não geram a reescrita; apontam o problema e a direção.

É nesses pontos que um modelo entra com vantagem: arbitrar os casos ambíguos
(passiva ruim ou passiva funcional?), ordenar sugestões e fazer a reescrita
propriamente dita, agora guiada pelo diagnóstico, que transforma "escreva
melhor" em instrução verificável ("tire o gerundismo na posição 60–80; quebre
o período de 49 palavras").

## Estrutura do projeto

```
machado/
├── machado/
│   ├── tipos.py          # Ocorrencia, Resultado, severidades, categorias
│   ├── regras_regex.py   # Camada 1 — base declarativa de regras
│   ├── regras_spacy.py   # Camada 2 — regras morfossintáticas
│   ├── motor.py          # orquestração, estatísticas, relatório, JSON
│   ├── __init__.py
│   └── __main__.py       # CLI
├── exemplos/             # cinco textos de perfis diferentes
├── app.py                # interface web (Gradio / Hugging Face Spaces)
├── demo.py               # tabela comparativa + relatório completo
├── tests/                # 36 testes (regras e perfis dos exemplos)
└── requirements.txt
```

## Licença

MIT.
