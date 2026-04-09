<div align="center">
  <h1>📦 GesCol - Gestor de Coletores</h1>
  <p><i>Sistema robusto de gerenciamento de coletores de dados e colaboradores, otimizado para operações de larga escala (Magalu Style).</i></p>
  
  ![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python) 
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=for-the-badge&logo=fastapi) 
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async-336791?style=for-the-badge&logo=postgresql)
  ![Gunicorn](https://img.shields.io/badge/Gunicorn-Multicore-green?style=for-the-badge&logo=gunicorn)
  ![License](https://img.shields.io/badge/License-GPLv3-red?style=for-the-badge)
</div>

---

## 📌 Visão Geral
O **GesCol** é uma solução completa para o rastreamento e gestão de equipamentos logísticos (coletores Zebra, scanners, etc) em Centros de Distribuição. 

### Principais Funcionalidades:
- 🔐 **Controle de Acesso**: Hierarquia por nível de usuário e restrição geográfica por Filial/CD.
- 📊 **Dashboard Analítica**: Visão em tempo real das atribuições ativas.
- ⚡ **HTMX Ready**: Interface web fluida com atualizações dinâmicas sem recarga de página.
- 🤖 **API First (v1)**: Endpoints REST prontos para integração com apps mobile e dispositivos industriais.
- 🛡️ **Hardenizado**: Proteção contra Bruteforce (SlowAPI) e Cookies seguros (HTTPOnly).

## ⚙️ Pré-requisitos
- **OS**: Linux (Debian, Ubuntu) ou WSL2.
- **Python**: 3.10 ou superior.
- **Infra**: PostgreSQL e Apache2.

## 🚀 Instalação e Setup Rápido

O GesCol agora possui um fluxo de instalação simplificado e seguro para novas máquinas.

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd gescol
```

### 2. Configuração de Sistema (Requer Sudo)
Este comando instala todas as dependências do SO, configura o ambiente Python (`venv`) e prepara o Apache.
```bash
make setup
```

### 3. Inicialização do Banco de Dados
Ao final do `make setup`, o sistema perguntará se deseja rodar o `initial_run.sh`. Você também pode executá-lo manualmente:
```bash
make init
```
> [!TIP]
> O script `make init` é interativo. Ele criará o banco de dados, configurará o acesso e aplicará todas as migrações automaticamente, além de atualizar seu `.env`.

## 🛠️ Execução e Operação

O sistema utiliza **Gunicorn** com workers **Uvicorn** para garantir alta performance e resiliência multicore.

| Comando | Descrição |
|---------|-----------|
| `make run` | Inicia o servidor e os serviços em background |
| `make stop` | Encerra todos os processos da aplicação |
| `make restart` | Reinicia Apache e PostgreSQL |
| `make logs` | Acompanha os logs de erro em tempo real |
| `make db` | Acessa o console interativo do PostgreSQL |

## 📁 Documentação Adicional
Para detalhes técnicos avançados, consulte a pasta `docs/`:
- [Ficha Técnica](docs/1-ficha-tecnica.md)
- [Stack de Software](docs/2-stack-software.md)
- [Níveis de Acesso e Segurança](docs/3-niveis-de-acesso.md)

---
**Desenvolvimento**: Mantenedores do GesCol
