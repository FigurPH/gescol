#!/bin/bash
# start_wsl.sh
# Inicia os serviços localmente no WSL

echo "Garantindo que PostgreSQL e Apache estão rodando..."
sudo service postgresql start
sudo service apache2 start

echo "Iniciando Uvicorn..."
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH=$PWD

# Carrega variáveis do .env para o escopo do Gunicorn
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Inicia com Gunicorn orquestrando múltiplos workers do Uvicorn e enviando p/ log
nohup gunicorn src.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 127.0.0.1:8000 > logs/uvicorn.log 2>&1 &
echo "Uvicorn está rodando em background (logs salvos em uvicorn.log)"