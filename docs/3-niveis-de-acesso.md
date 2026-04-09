# Níveis de Acesso e Segurança

O GesCol utiliza controle de acesso hierárquico baseado em níveis (`user_level`) e restrição geográfica por Centros de Distribuição (`is_cd_restricted`).

## 👥 Perfis (Roles)

| Nível (ID) | Perfil | Permissões |
|:---:|---|---|
| `1` | **USER** | Visualização de dashboard e realização de atribuições próprias. |
| `2` | **LEADER** | Visualização expandida de relatórios locais. |
| `9` | **ADMIN** | Gestão de cadastros e usuários dentro do seu CD (Filial). |
| `10` | **SUPERADMIN** | Acesso global ilimitado e gestão de administradores. |

## 🔓 Segurança e Blindagem

- **Cookie Security**: Cookies `HttpOnly` e `SameSite=Lax` para prevenir ataques XSS e CSRF.
- **Rate Limiting**: Limite de 5 requisições por minuto na rota de login via SlowAPI.
- **Zero-Secrets Policy**: Migração de chaves hardcoded para variáveis de ambiente via `.env` gerenciado pelo `initial_run.sh`.
- **Horizontal Multi-tenancy**: Filtros mandatórios de `cd_id` em todas as queries para garantir que dados de uma filial não vazem para outra.
