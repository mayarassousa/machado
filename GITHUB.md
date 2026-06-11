# Como enviar o Machado para GitHub

Este guia orienta como criar um repositório no GitHub e fazer o push do projeto.

## 1. Criar o repositório no GitHub

1. Acesse https://github.com/new
2. Preencha:
   - **Repository name**: `machado` (ou o nome que preferir)
   - **Description**: "Motor de revisão estilística para português brasileiro — duas camadas (regex + SpaCy), saída explicável"
   - **Public** (para que o Felipe Iszlaji veja sem problema)
   - **Add a README file**: NÃO marque (você já tem um)
   - **Choose a license**: MIT (já incluso no projeto)
   - **Add .gitignore**: NÃO (já tem)
3. Clique **Create repository**

## 2. Fazer o push (SSH — recomendado)

Na sua máquina, dentro da pasta `machado`:

```bash
git remote add origin git@github.com:SEU_USUARIO/machado.git
git branch -M main
git push -u origin main
```

Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

**Pré-requisito**: chave SSH configurada no GitHub.
Se você nunca fez isso:

```bash
ssh-keygen -t ed25519 -C "seu_email@example.com"
# (pressione Enter em todas as perguntas para usar defaults)
cat ~/.ssh/id_ed25519.pub
# copie o output e adicione em https://github.com/settings/keys → "New SSH key"
```

## 3. Alternativa: fazer o push via HTTPS (mais fácil, menos seguro)

```bash
git remote add origin https://github.com/SEU_USUARIO/machado.git
git branch -M main
git push -u origin main
```

Na primeira vez, o Git pedirá seu token pessoal do GitHub.
Se não tem um token:

1. Vá em https://github.com/settings/tokens
2. Clique "Generate new token (classic)"
3. Marque `repo` (acesso completo a repositórios)
4. Gere e copie o token
5. Cole na caixa de senha quando o git pedirn (Ctrl+V, Enter)

## 4. Enviar para o Felipe

Uma vez o repositório público no GitHub, envie o link direto:

```
https://github.com/SEU_USUARIO/machado
```

Ele pode:
- Clonar: `git clone https://github.com/SEU_USUARIO/machado.git`
- Rodar a demo: `cd machado && python demo.py`
- Rodar os testes: `pytest -q`
- Ver o histórico de commits

## 5. Checklist antes de enviar

Rode isto uma última vez na sua máquina para confirmar que tudo funciona:

```bash
cd machado
pip install -r requirements.txt
python demo.py
pytest -q
```

Se os testes passam e a demo rodou, está pronto para GitHub.

## Bônus: adicionar um badge de status

Depois do primeiro push, o GitHub Actions rodará os testes automaticamente.
Você verá um badge verde/vermelho no README. Isso é profissional e mostra que
você cuida de CI/CD.

Para adicionar o badge manualmente ao README, procure a aba "Actions" do seu
repositório e copie a markdown do status badge.
