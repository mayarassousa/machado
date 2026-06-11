#!/bin/bash

# Script para fazer push para GitHub em 3 etapas
# Uso: ./PUSH_GITHUB.sh seu_usuario_github

if [ -z "$1" ]; then
    echo "Uso: ./PUSH_GITHUB.sh seu_usuario_github"
    echo ""
    echo "Exemplo:"
    echo "  ./PUSH_GITHUB.sh mayara-sousa"
    exit 1
fi

USUARIO=$1
REPO="machado"

echo "=== Preparando para push para GitHub ==="
echo "Usuário: $USUARIO"
echo "Repositório: $REPO"
echo ""
echo "PASSO 1: Confirme que você criou o repositório em GitHub:"
echo "  https://github.com/new"
echo "  Nome: $REPO"
echo "  Público: SIM"
echo "  README: NÃO (você já tem)"
echo ""
read -p "Pronto? [s/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    exit 1
fi

echo ""
echo "PASSO 2: Adicionando origem remota..."
git remote add origin git@github.com:$USUARIO/$REPO.git
git branch -M main

echo ""
echo "PASSO 3: Fazendo push (pode pedir senha/token)..."
git push -u origin main

echo ""
echo "✓ Pronto! Seu repositório está em:"
echo "  https://github.com/$USUARIO/$REPO"
echo ""
echo "Compartilhe este link com o Felipe Iszlaji."
