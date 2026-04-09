#!/bin/bash

# Script para configurações iniciais do banco de dados e execução de migrations do GesCol

echo "========================================================================"
echo "          GesCol - Configuração Inicial de Banco de Dados               "
echo "========================================================================"

# Carregar variáveis do .env se existir
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Solicitar informações do usuário
read -p "Nome do Banco de Dados [${GENERAL_DB_NAME:-gescol_db}]: " DB_NAME
DB_NAME=${DB_NAME:-${GENERAL_DB_NAME:-gescol_db}}

read -p "Usuário do Banco de Dados [${GENERAL_DB_USER:-gescol}]: " DB_USER
DB_USER=${DB_USER:-${GENERAL_DB_USER:-gescol}}

if [ -n "$GENERAL_DB_PASS" ]; then
    read -p "Senha do Banco de Dados (deixe em branco para usar a atual): " DB_PASS
    DB_PASS=${DB_PASS:-$GENERAL_DB_PASS}
else
    read -s -p "Senha do Banco de Dados: " DB_PASS
    echo ""
fi

read -p "Host do Banco de Dados [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Porta do Banco de Dados [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

# Construir DATABASE_URL (usando asyncpg conforme o .env original)
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "Atualizando arquivo .env..."

# Função para atualizar ou adicionar variável no .env
update_env() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" .env; then
        # Se a chave já existe, substitui preservando o resto do arquivo
        sed -i "s|^${key}=.*|${key}=${value}|" .env
    else
        # Se não existe, adiciona ao final
        echo "${key}=${value}" >> .env
    fi
}

# Garantir que o .env existe
touch .env

update_env "DATABASE_URL" "$DATABASE_URL"
update_env "GENERAL_DB_NAME" "$DB_NAME"
update_env "GENERAL_DB_USER" "$DB_USER"
update_env "GENERAL_DB_PASS" "$DB_PASS"

echo "Configurando PostgreSQL (Requer sudo)..."

# Criar usuário e banco de dados
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" || echo "Aviso: Usuário ${DB_USER} já existe ou erro ao criar."
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" || echo "Aviso: Banco ${DB_NAME} já existe ou erro ao criar."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" || echo "Aviso: Erro ao conceder privilégios."

echo "Executando migrations iniciais..."

# Verificar se o venv existe e ativar
if [ -d "venv" ]; then
    source venv/bin/activate
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "✅ Migrations executadas com sucesso!"
    else
        echo "❌ Erro ao executar migrations."
        exit 1
    fi
else
    echo "❌ Virtual environment (venv) não encontrado. Execute 'make setup' primeiro."
    exit 1
fi

echo "========================================================================"
echo "          Configuração inicial concluída com sucesso!                   "
echo "========================================================================"
