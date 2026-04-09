echo "Instalando todas dependências e pacotes..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib apache2 libapache2-mod-wsgi-py3

echo "Iniciando o PostgreSQL..."
sudo service postgresql start || sudo systemctl start postgresql

echo "Configurando Ambiente Python..."
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements


echo "Configurando Apache2..."
sudo a2enmod proxy
sudo a2enmod proxy_http

sudo cp gescol.conf /etc/apache2/sites-available/
sudo a2ensite gescol.conf
sudo a2dissite 000-default.conf

sudo systemctl reload apache2 || sudo systemctl reload apache2


echo "Configurações de ambiente finalizadas."

echo ""
read -p "Deseja rodar o script de migrações iniciais e configuração de banco de dados (initial_run.sh)? [s/N]: " run_initial
if [[ "$run_initial" =~ ^[Ss]$ ]]; then
    bash ./initial_run.sh
else
    echo "Pulando configuração inicial do banco. Você pode rodar manualmente depois com: bash initial_run.sh ou make init"
fi

echo ""
echo "Para rodar a aplicação execute: make run"

