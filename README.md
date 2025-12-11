# Library API Advanced

Uma implementação de API nível "Pleno" demonstrando arquitetura de backend moderna e melhores práticas com FastAPI.

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

### 4. Iniciar o Servidor
```bash
uvicorn app.main:app --reload
```

### 5. Documentação da API
Acesse `http://localhost:8000/docs` para ver o Swagger UI interativo.

## Testes

Para rodar a suíte de testes:
```bash
pytest
```
