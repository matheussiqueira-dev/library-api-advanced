# Library Studio Advanced API

Uma implementação de referência de nível Sênior para gestão de acervos bibliográficos, demonstrando arquitetura moderna, padrões de design robustos e uma experiência de usuário (UX) excepcional.

Este projeto transcende um CRUD básico, oferecendo integração com APIs externas, arquitetura em camadas (Repository/Service/API) e uma interface reativa de alto desempenho.

## 🚀 Tecnologias Core

- **Backend**: FastAPI (Python 3.10+) - Performance extrema com tipagem estática via Pydantic v2.
- **Banco de Dados**: SQLite com **SQLAlchemy 2.0 (Async)** e `aiosqlite`.
- **Arquitetura**:
  - **Repository Pattern**: Abstração total da camada de dados.
  - **Service Layer**: Centralização das regras de negócio.
  - **Dependency Injection**: Uso intensivo do sistema de dependências do FastAPI.
- **Frontend**: Vanilla JS moderno, CSS customizado com foco em Glassmorphism e Ícones Lucide.
- **Integrações**: Google Books / OpenLibrary API para busca automática de metadados via ISBN.
- **Observabilidade**: Sistema de log estruturado e middleware para rastreamento de tempo de resposta.

## ✨ Funcionalidades Principais

- **Gestão de Livros Pro**: Cadastro completo com suporte a descrição, capa, ano e status (Disponível, Emprestado, etc).
- **Lookup Inteligente via ISBN**: Preenchimento automático de metadados consumindo APIs externas.
- **Busca Avançada**: Filtros em tempo real por título, autor, intervalo de anos e paginação dinâmica.
- **Interface Premium**: Design dark-mode sofisticado, animações suaves e layouts responsivos.
- **Dashboard de Estatísticas**: Visão geral do acervo em tempo real.
- **API Auto-documentada**: Swagger UI integrado para testes rápidos.

## 📁 Estrutura do Projeto

```text
library-api-advanced/
├── app/
│   ├── api/            # Camada de Entrada (Controllers/Routes)
│   ├── core/           # Configurações dinâmicas e Conexão de Banco
│   ├── models/         # Definição de Schemas SQLAlchemy (Data)
│   ├── schemas/        # DTOs Pydantic (Validação)
│   ├── repositories/   # Abstração de Banco (Repository Pattern)
│   ├── services/       # Regras de Negócio e Lógica de Integração
│   ├── web/            # Assets do Frontend (HTML, CSS, JS)
│   └── main.py         # Inicialização da Application
├── tests/              # Suíte de Testes Automatizados (Pytest)
├── alembic/            # Gerenciamento de Migrações de Banco
└── requirements.txt    # Gerenciamento de Dependências
```

## 🛠️ Instalação e Uso

### 1. Preparação do Ambiente
```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2. Configuração do Banco
O sistema utiliza criação automática de schema para facilitar o setup inicial.
```bash
# Opcional se desejar rodar migrações manuais
alembic upgrade head
```

### 3. Execução
```bash
uvicorn app.main:app --reload
```

### 4. Acessos
- **Frontend**: `http://localhost:8000/`
- **Docs (Swagger)**: `http://localhost:8000/docs`

## 🛡️ Boas Práticas Aplicadas

- **DRY (Don't Repeat Yourself)**: Uso de um Base Repository para operações CRUD genéricas.
- **SoC (Separation of Concerns)**: Responsabilidades claras entre cada camada da aplicação.
- **Segurança**: Validação rigorosa de inputs com Pydantic.
- **Performance**: Uso intensivo de operações assíncronas (async/await) para I/O não bloqueante.
- **UX/UI**: Hierarquia visual clara, feedback imediato ao usuário (Toasts) e estados de carregamento.

---

**Autoria: Matheus Siqueira**  
**Website:** [https://www.matheussiqueira.dev/](https://www.matheussiqueira.dev/)
