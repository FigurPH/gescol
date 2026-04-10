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

## 🏁 Condições de Corrida e Concorrência

Uma das proteções mais importantes do GesCol é a prevenção de duplas atribuições para o mesmo coletor. No entanto, o teste de estresse `test_race_condition_concurrent_checkouts` pode ser instável em alguns ambientes devido ao comportamento do driver `aiosqlite` em conjunto com o modo `WAL`:

1.  **Proteção Garantida**: A restrição de integridade (`UniqueIndex`) no banco de dados garante que NUNCA ocorram duplas atribuições, independentemente da instabilidade do teste.
2.  **Erro `greenlet_spawn`**: Em condições de raríssima concorrência extrema no `pytest`, o driver pode lançar um erro de `greenlet`. Isso é um artefato do ambiente de teste (envolvimento de múltiplas sessões assíncronas no mesmo processo) e não reflete um bug no ambiente de produção.
3.  **Resultado Esperado**: O teste é considerado bem-sucedido se pelo menos uma requisição for gravada corretamente e as tentativas de conflito sejam bloqueadas pelo banco.

## 📈 Boas Práticas ao Adicionar Testes

1. **Use as Fixtures**: Sempre utilize `client` e `seed_data` para garantir que o ambiente esteja populado corretamente.
2. **Logs de Teste**: Utilize o prefixo `[TEST]` em logs informativos para facilitar o debug via `--s`.
3. **Async**: Como o sistema é assíncrono, todos os novos testes devem ser decorados com `@pytest.mark.asyncio`.
