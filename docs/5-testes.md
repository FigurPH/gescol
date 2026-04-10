# 🧪 Documentação de Testes

O GesCol utiliza uma suíte de testes automatizados baseada em `pytest` para garantir a integridade das regras de negócio, segurança e estabilidade do sistema.

## 🚀 Como Executar

Os testes podem ser executados via `Makefile`:

```bash
# Executa todos os testes
make test

# Executa os testes com relatório de cobertura (coverage)
make test-cov
```

## 🏗️ Estrutura da Suíte

A suíte está localizada no diretório `tests/` e é composta pelos seguintes arquivos:

- **`conftest.py`**: Configuração global do ambiente de testes. Implementa o isolamento do banco de dados (SQLite em modo WAL), fixtures de dados (seed) e overrides de dependências do FastAPI.
- **`test_auth.py`**: Valida o fluxo de autenticação (login/logout) e o limite de tentativas (Rate Limiting).
- **`test_atribuicoes.py`**: Testa o núcleo do sistema: checkout, checkin, restrições por CD e proteção contra condições de corrida (Race Conditions).
- **`test_cadastros.py`**: Valida os níveis de acesso (Admin vs Operador) e o isolamento de dados geográficos.
- **`test_htmx.py`**: Garante que o sistema responda corretamente a requisições HTMX (fragmentos parciais e headers OOB).

## 🗄️ Banco de Dados de Teste

Para garantir que os testes não afetem os dados de produção:
1. O sistema utiliza um banco SQLite temporário (`tests/test_final_concurrent.db`).
2. O modo **WAL (Write-Ahead Logging)** é habilitado para permitir concorrência assíncrona.
3. As tabelas são limpas automaticamente entre cada caso de teste através da fixture `clean_database`.

## 🏁 Condições de Corrida

Uma das proteções mais importantes do GesCol é a prevenção de duplas atribuições para o mesmo coletor. Isso é validado no teste `test_race_condition_concurrent_checkouts`, que dispara múltiplas requisições simultâneas e garante que apenas uma tenha sucesso, enquanto as outras recebem um erro de conflito.

## 📈 Boas Práticas ao Adicionar Testes

1. **Use as Fixtures**: Sempre utilize `client` e `seed_data` para garantir que o ambiente esteja populado corretamente.
2. **Logs de Teste**: Utilize o prefixo `[TEST]` em logs informativos para facilitar o debug via `--s`.
3. **Async**: Como o sistema é assíncrono, todos os novos testes devem ser decorados com `@pytest.mark.asyncio`.
