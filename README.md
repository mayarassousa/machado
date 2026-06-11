# Machado

Motor de revisão estilística para o português brasileiro. Duas camadas — regex
para padrões de superfície, SpaCy para padrões morfossintáticos — e uma saída
explicável: cada sinalização carrega a regra que a produziu, o porquê e a
sugestão de correção.

O nome segue a tradição da casa: se a assistente se chama Clarice, o módulo
que corta excesso só podia se chamar Machado.

## Por que regras, e não (só) um LLM

Um detector de gerundismo não precisa de 7 bilhões de parâmetros. Precisa de
uma expressão regular correta e de uma explicação linguística honesta. Para a
classe de desvios que tem **forma estável** — gerundismo, pleonasmo, clichê,
queísmo, nominalização —, regras linguísticas bem escritas entregam:

- **precisão controlável**: cada regra é testável isoladamente, com casos
  positivos e negativos (a suíte deste projeto tem 25 testes);
- **custo marginal próximo de zero**: nada de inferência por token; o motor
  inteiro roda em milissegundos em CPU;
- **explicabilidade por construção**: a saída não é uma probabilidade, é um
  diagnóstico — regra, posição, justificativa, sugestão;
- **manutenção previsível**: corrigir um falso positivo é editar uma regra,
  não retreinar um modelo.

O LLM entra onde a regra não alcança (ver "Limites", abaixo). A divisão de
trabalho é a mesma que torna um produto de revisão sustentável em escala:
camada determinística barata na frente, modelo caro apenas onde há ambiguidade
real para resolver.

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

Três decisões sustentam o desenho:

**1. Regra é dado, não código.** Cada regra da Camada 1 é uma entrada
declarativa (`RegraRegex`) com id estável, padrão, categoria, severidade,
explicação e sugestão. Adicionar a 13ª, a 50ª ou a 120ª dica de estilo não
toca no motor — toca na base de regras. Para os casos em que regex puro não
expressa a restrição (ex.: travessão em linha de diálogo é legítimo;
travessão intercalado no meio do parágrafo é cacoete), a regra aceita um
**filtro contextual** opcional: continua declarativa, ganha veto.

**2. Capability-aware por padrão.** As regras da Camada 2 declaram o que
exigem do pipeline. Com o modelo treinado (`pt_core_news_sm`), tudo ativa,
com POS e morfologia refinando as heurísticas; com um `spacy.blank("pt")`,
as regras lexicais e estruturais seguem funcionando e o relatório **declara
o que ficou de fora** em vez de fingir cobertura total. Em produção, isso
permite uma primeira passada barata em escala e o pipeline caro só onde é
necessário.

**3. Precisão acima de cobertura.** Um revisor que grita falso positivo é
desinstalado na primeira semana. Por isso os limiares são conservadores e
configuráveis (`ConfigMotor`), os padrões carregam anti-falsos-positivos
explícitos (adjetivos em *-ido* que não são particípios; "ao mesmo tempo"
que não é "o mesmo" pronominal) e a severidade distingue erro de norma
(ATENÇÃO), escolha que enfraquece o texto (SUGESTÃO) e traço legítimo cujo
problema é a dose (INFO).

## O que ele detecta hoje

Doze categorias, escolhidas por sobreposição com o repertório clássico de
desvios da escrita profissional em PT-BR: gerundismo; pleonasmos viciosos
("há anos atrás", "subir para cima", "conclusão final"); clichês e muletas
("antes de mais nada", "através de" como meio, "o mesmo" pronominal);
palavras vazias de corporativês; voz passiva; nominalização com verbo-suporte
("realizar a implementação" → "implementar"); frases longas; queísmo;
acúmulo de advérbios em *-mente*; adjetivação excessiva; repetição lexical
em janela curta; e **marcadores de texto gerado por IA**.

### A categoria diferencial: marcadores de IA

A última categoria trata texto gerado por LLM como **variedade linguística
com traços descritíveis**: o travessão parentético à moda anglófona, as
estruturas contrastivas formulaicas ("não é apenas X, é Y"), o metadiscurso
de preenchimento ("é importante ressaltar que"), as aberturas de ambientação
("no cenário atual"), as colocações de relevância vazia ("desempenha um
papel fundamental") e os vestígios de chat que sobrevivem ao copiar-e-colar.

O motor agrega isso num **índice de sotaque de IA** (ocorrências por mil
palavras). A moldura é deliberadamente honesta: **não é um detector de IA**.
Texto humano pode pontuar alto — e mereceria revisão do mesmo jeito; texto
gerado e bem editado pontua baixo — que é exatamente o objetivo de quem usa
uma ferramenta de humanização. O índice mede cacoete, não autoria. É a
fundação técnica de um recurso de "humanizar": antes de reescrever, saber
*o que* soa a máquina e *onde*.

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
