# Stack de Software

Esta documentação descreve toda a pilha tecnológica utilizada no backend, infraestrutura e frontend da aplicação **GesCol**.

## 💻 Linguagens e Frameworks Principais

| Tecnologia | Versão (Aprox) | Justificativa |
|---|---|---|
| **Python** | `3.10+` | Linguagem base com forte ecossistema para sistemas administrativos e dados. |
| **FastAPI** | `0.109.0` | Framework web ASGI assíncrono, permitindo alta performance e tipagem rigorosa. |
| **Jinja2 + HTMX**| `3.1.3` | Interface reativa sem a complexidade de SPAs pesadas (React/Vue). |
| **Gunicorn** | `21.2.0` | Servidor de aplicação WSGI/ASGI para produção bare-metal. |

## 🗄️ Bancos de Dados e Persistência

- **PostgreSQL**: Banco relacional robusto para garantir a integridade dos dados de patrimônio.
- **AsyncIO**: Todas as consultas ao banco são assíncronas, evitando bloqueio do loop de eventos.
- **Tempfile Logistics**: Geração de relatórios pesados utiliza escrita em disco temporário para evitar estouro de memória RAM.

## ☁️ Infraestrutura e Deploy

- **On-Premise Focus**: O sistema é otimizado para rodar em servidores locais Linux sem dependência obrigatória de containers.
- **Apache2 Reverse Proxy**: Atua como a primeira camada de defesa e gerenciamento de certificados SSL/TLS.
- **Hardened Setup**: Scripts de instalação interativos (`initial_run.sh`) que garantem segregação de credenciais e configuração dinâmica do ambiente.
