# Machado — Sumário Executivo

## Para: Felipe Iszlaji, CEO Clarice.ai
## Assunto: Discussão técnica — motor de revisão estilística em PT-BR

---

## O que é

Um motor de revisão estilística para português brasileiro que espelha a arquitetura do núcleo de vocês:

- **Duas camadas**: regex (padrões de superfície) + SpaCy (padrões morfossintáticos)
- **Saída explicável**: cada sinalização é auditável — regra, offsets, justificativa linguística, sugestão
- **Regras como dados**: catálogo declarativo que cresce sem tocar o motor
- **12 categorias** de desvio: gerundismo, pleonasmo, clichê, queísmo, voz passiva, nominalização, frases longas, repetição, advérbios em -mente, adjetivação, palavras vazias, **marcadores de IA**
- **25 testes** cobrindo casos positivos e anti-falsos-positivos
- **Capability-aware**: funciona em modo reduzido (sem modelo) ou completo (com pt_core_news_sm)

## O diferencial

### Categoria: Marcadores de texto gerado por IA

Não é um "detector de IA" — é um medidor de **sotaque linguístico** de saída de LLM:
travessão parentético, estruturas contrastivas formulaicas, metadiscurso de preenchimento,
colocações vazias de relevância, vestígios de chat. Agregados num **índice de sotaque de IA**
(ocorrências por mil palavras).

Serve como fundação técnica de um recurso de "humanização": antes de reescrever,
o sistema sabe o que soa a máquina e onde.

**Conexão**: seu material sobre o travessão como marcador estilístico de LLM em PT-BR
é exatamente a moldura teórica para isto.

## Quick start

```bash
git clone https://github.com/[usuario]/machado.git
cd machado
pip install -r requirements.txt
python demo.py
pytest -q
```

Ou uma sentença teste:
```bash
python -m machado "Vou estar te enviando o relatório que foi escrito há dias atrás."
```

Saída estruturada (JSON):
```bash
python -m machado --json "..."
```

## Arquivos-chave

- **README.md**: arquitetura completa, limites, ponte para LLM
- **APRESENTACAO.md**: roteiro de 10 minutos + 3 perguntas para você fazer a ele
- **GITHUB.md**: instruções de push para GitHub
- **demo.py**: contraste entre texto carregado (24 ocorrências, sotaque 52/1000) e texto enxuto (zero)
- **tests/test_machado.py**: 25 testes, todos passando

## Por que isto importa para a entrevista

1. **Responde a pergunta dele sobre regex/SpaCy em ato**: não é discussão, é código testado.
2. **Mostra divisão de trabalho regras/modelo**: a tese dele (conhecimento linguístico reduz dependência de LLMs caros) em prática.
3. **O diferencial é seu**: marcadores de IA + sotaque — ninguém mais chega com isto.
4. **Propõe continuação técnica**: "Motor barato e auditável como camada de controle. LLM onde há ambiguidade. Reescrita condicionada pelo diagnóstico."

## Perguntas para fazer a ele (se o tempo permitir)

- Hoje, qual a divisão real entre regras e modelo no pipeline de vocês?
- Como medem falso positivo das dicas de estilo em produção?
- No LLM próprio: a camada de regras vira dado de treino (sinal de preferência) ou continua como pós-processamento?

Perguntas assim demonstram compreensão da engenharia real do produto.

---

**Tempo estimado na apresentação**: 10 minutos (demo + código + discussão)  
**Repositório**: https://github.com/[usuario]/machado  
**Status**: todos os testes passam, CI/CD ativo (GitHub Actions)
