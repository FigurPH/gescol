# Variáveis de Ambiente
PYTHON = venv/bin/python
PIP = venv/bin/pip
UVICORN = venv/bin/uvicorn

.PHONY: help setup install run stop restart logs db clean init

help:
	@echo "========================================================================"
	@echo "      GesCol - Sistema de Gerenciamento de Coletores (Magalu Style)     "
	@echo "                     Ambiente Local (Sem Docker)                        "
	@echo "========================================================================"
	@echo "Comandos disponíveis:"
	@echo "  make setup   - Instala dependências do sistema e banco, configura Apache (requer sudo)"
	@echo "  make install - Instala/atualiza apenas as dependências Python no venv"
	@echo "  make run     - Inicia a aplicação (Uvicorn) e os serviços"
	@echo "  make stop    - Para processos do Uvicorn (caso rodando em background)"
	@echo "  make restart - Reinicia os serviços do Apache e PostgreSQL"
	@echo "  make logs    - Acompanha os logs de erro do Apache"
	@echo "  make db      - Acessa o console local do banco de dados (PostgreSQL)"
	@echo "  make init    - Configura banco de dados e executa migrações iniciais"
	@echo "  make test    - Executa a suíte de testes (pytest)"
	@echo "  make test-cov - Executa os testes com relatório de cobertura (coverage)"
	@echo "  make clean   - Remove arquivos temporários do Python (__pycache__)"
	@echo "========================================================================"

setup:
	@echo "Executando setup completo do ambiente (Requer Sudo)..."
	bash ./setup.sh

install:
	@echo "Instalando/atualizando dependências do Python..."
	$(PIP) install -r requirements.txt

test:
	@echo "Executando testes automatizados..."
	$(PYTHON) -m pytest tests/

test-cov:
	@echo "Executando testes com cobertura de código..."
	$(PYTHON) -m pytest --cov=src tests/ --cov-report=term-missing

run:
	@echo "Iniciando serviços e o Uvicorn..."
	bash ./start.sh

stop:
	@echo "Encerrando Uvicorn..."
	sudo service apache2 stop || echo "Apache não está rodando"
	sudo service postgresql stop || echo "PostgreSQL não está rodando"
	pkill -f uvicorn || echo "Nenhuma instância do Uvicorn rodando no momento."

restart:
	@echo "Reiniciando Apache e PostgreSQL..."
	sudo service apache2 restart
	sudo service postgresql restart

logs:
	@echo "Lendo logs de erro do Apache... (Crtl+C para sair)"
	sudo tail -f /var/log/apache2/gescol_error.log

db:
	@echo "Acessando DB..."
	sudo -u postgres psql -d gescol_db

clean:
	@echo "Limpando arquivos de cache..."
	@python3 -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
	@python3 -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	@echo "Limpeza finalizada."

init:
	@echo "Iniciando configuração de banco e migrations..."
	bash ./initial_run.sh