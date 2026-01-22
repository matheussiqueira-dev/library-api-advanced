# Library API Advanced

Uma implementação de API nível senior demonstrando arquitetura de backend moderna, observabilidade e UX rica.

## Funcionalidades

- **Framework**: FastAPI (Alta performance, fácil aprendizado).
- **Banco de Dados**: SQLite (Assíncrono) usando **SQLAlchemy 2.0** e `aiosqlite`.
- **Migrações**: Gerenciamento de schema do banco com **Alembic**.
- **Arquitetura**:
    - **Design em Camadas**: Rotas -> Serviços -> Modelos.
    - **Injeção de Dependências**: Uso intensivo do `Depends` do FastAPI.
    - **Configuração**: `pydantic-settings` para variáveis de ambiente.
    - **Testes**: `pytest` e `httpx` para testes de integração assíncronos.
- **Segurança de Tipos**: Validação completa com Pydantic v2.
- **CI/CD**: Pipeline de testes automático com GitHub Actions.
- **UI**: Interface inovadora para curadoria do acervo em tempo real.

## Estrutura do Projeto

```text
library-api-advanced/
├── app/
│   ├── api/        # Rotas (Controllers)
│   ├── core/       # Configuração e Setup de DB
│   ├── models/     # Modelos SQLAlchemy
│   ├── schemas/    # Schemas Pydantic (DTOs)
│   ├── services/   # Regras de Negócio
│   └── main.py     # Ponto de Entrada
├── tests/          # Suíte de Testes
├── alembic/        # Migrações de Banco
└── requirements.txt
```

## Como Executar

### 1. Pré-requisitos
- Python 3.10+
- Ambiente Virtual (recomendado)

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Rodar Migrações
Este projeto usa Alembic. Inicialize o banco:
```bash
alembic upgrade head
```
Se preferir criar as tabelas automaticamente, use `DB_AUTO_CREATE=true` (padrao).

### 4. Iniciar o Servidor
```bash
uvicorn app.main:app --reload
```

### 5. Documentação da API
Acesse `http://localhost:8000/docs` para ver o Swagger UI interativo.

### 6. UI
Abra `http://localhost:8000/` para a nova interface visual.

### Busca e filtros (GET /api/v1/books)
- `q`: pesquisa em titulo/autor (min 2 chars)
- `author`: filtra por autor
- `year`, `year_min`, `year_max`
- `sort`: `title`, `author`, `year`, `created_at`
- `order`: `asc`, `desc`

## Testes

Para rodar a suíte de testes:
```bash
pytest
```
