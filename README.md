# Library Studio Advanced API

Uma implementação de referência de nível Sênior para gestão de acervos bibliográficos, demonstrando arquitetura moderna, padrões de design robustos e uma experiência de usuário (UX) excepcional.

Este projeto transcende um CRUD básico, oferecendo integração com APIs externas, arquitetura em camadas (Repository/Service/API) e uma interface reativa de alto desempenho.

## 🚀 Tecnologias Core

- **Backend**: FastAPI (Python 3.12) - Performance extrema com tipagem estática via Pydantic v2.
- **Banco de Dados**: SQLite com **SQLAlchemy 2.0 (Async)** e `aiosqlite`.
- **Arquitetura**:
  - **Repository Pattern**: Abstração total da camada de dados.
  - **Service Layer**: Centralização das regras de negócio.
  - **Dependency Injection**: Uso intensivo do sistema de dependências do FastAPI.
- **Frontend**: Vanilla JS moderno, CSS customizado com foco em Glassmorphism e Ícones Lucide.
- **Integrações**: OpenLibrary API para busca automática de metadados via ISBN (com cache em memória).
- **Observabilidade**: Logs com nível configurável e middleware que adiciona `X-Request-Id` e `X-Process-Time`.

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

### 4. Testes
Os testes usam um SQLite temporário e uma OpenLibrary simulada: não tocam o `library.db` local nem acessam a rede.
```bash
pytest
```

### 5. Acessos
- **Frontend**: `http://localhost:8000/`
- **Docs (Swagger)**: `http://localhost:8000/docs`

## 🔒 Segurança e limites da demo pública

- **Sem XSS armazenado**: a interface insere dados de livros e mensagens no DOM só via `textContent`, sem `innerHTML` nem scripts inline.
- **Content-Security-Policy** sem `'unsafe-inline'` em `script-src` na interface, além de `nosniff`, `Referrer-Policy`, `Permissions-Policy` e `frame-ancestors 'none'`. `/docs` e `/redoc` têm uma política própria, porque o Swagger UI e o ReDoc dependem de script inline e do jsDelivr.
- **Scripts de terceiros com versão exata**: Lucide `1.48.0` com SRI e ReDoc `2.5.4`.
- **Rotas de escrita protegidas**: `POST`, `PUT` e `DELETE` passam por kill switch (`WRITES_ENABLED`) e rate limit por IP; o `/lookup` tem rate limit próprio e cache.
- **Limites de entrada**: corpo de até 16 KB (413), acervo com teto (`DEMO_MAX_BOOKS`, 409), ISBN validado com dígito verificador (422), `cover_url` só http(s) e ISBN duplicado retornando 409.

O rate limit fica em memória e vale **por instância**. Em produção com várias instâncias (por exemplo, Functions na Vercel), combine-o com uma regra de rate limit no firewall da plataforma.

### Variáveis de ambiente

Veja `.env.example` para os valores padrão.

| Variável | Uso |
|---|---|
| `PROJECT_NAME`, `PROJECT_DESCRIPTION`, `VERSION`, `API_V1_STR` | Metadados e prefixo da API |
| `DATABASE_URL` | URL assíncrona do SQLAlchemy |
| `DB_AUTO_CREATE` | Cria as tabelas na inicialização |
| `DEMO_SEED` | Insere um acervo inicial de livros quando o banco está vazio |
| `LOG_LEVEL` | Nível de log |
| `WRITES_ENABLED` | Kill switch das rotas de escrita |
| `DEMO_MAX_BOOKS` | Número máximo de livros |
| `MAX_REQUEST_BODY_BYTES` | Tamanho máximo do corpo das requisições |
| `RATE_LIMIT_WINDOW_SECONDS` | Janela do rate limit |
| `RATE_LIMIT_WRITES_PER_WINDOW` | Escritas por IP por janela |
| `RATE_LIMIT_LOOKUPS_PER_WINDOW` | Consultas de ISBN por IP por janela |
| `TRUST_PROXY_HEADERS` | Usa `X-Forwarded-For` como IP do cliente (só atrás de proxy confiável) |
| `VERCEL` | Definida pela própria Vercel; ativa os padrões do deploy (ver abaixo) |

## ▲ Deploy na Vercel

Projeto único com o preset **FastAPI** (entrypoint `app/main.py`, Python 3.12 via `.python-version`). O `vercel.json` só tira testes e ferramentas do bundle da Function.

**Persistência atual: ponte temporária.** O filesystem da Vercel é somente leitura, exceto `/tmp`. Quando `VERCEL=1` e nenhuma `DATABASE_URL` foi definida, o app:

- usa SQLite em `/tmp/library.db`, recriado a cada cold start;
- insere um acervo inicial de livros reais (`DEMO_SEED`);
- usa o IP de `X-Forwarded-For`, que a Vercel sobrescreve, para o rate limit (`TRUST_PROXY_HEADERS`).

Limitações: os dados voltam ao acervo inicial periodicamente e podem divergir entre instâncias. A interface mostra esse aviso. Para dados duráveis, defina `DATABASE_URL` com um Postgres gerenciado (por exemplo, Neon pelo Marketplace da Vercel); variáveis explícitas sempre têm precedência.

Recomendado: uma regra de rate limit no Vercel Firewall cobrindo `POST/PUT/DELETE /api/v1/books` e `/api/v1/books/lookup`, já que o limite do app é por instância.

## 🛡️ Boas Práticas Aplicadas

- **DRY (Don't Repeat Yourself)**: Uso de um Base Repository para operações CRUD genéricas.
- **SoC (Separation of Concerns)**: Responsabilidades claras entre cada camada da aplicação.
- **Segurança**: Validação rigorosa de inputs com Pydantic.
- **Performance**: Uso intensivo de operações assíncronas (async/await) para I/O não bloqueante.
- **UX/UI**: Hierarquia visual clara, feedback imediato ao usuário (Toasts) e estados de carregamento.

---

**Autoria: Matheus Siqueira**  
**Website:** [https://www.matheussiqueira.dev/](https://www.matheussiqueira.dev/)
