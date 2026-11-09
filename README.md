# Library Studio

API REST e interface web de referência para gestão de acervo bibliográfico: CRUD de livros, busca com filtros, indicadores do acervo e preenchimento de metadados por ISBN.

[![Demo ao vivo](https://img.shields.io/badge/Demo-ao_vivo-00f2fe?style=for-the-badge&logo=vercel&logoColor=000000)](https://library-api-advanced.vercel.app)
[![Case no portfólio](https://img.shields.io/badge/Case-Portf%C3%B3lio-000000?style=for-the-badge&logo=googlechrome&logoColor=white)](https://www.matheussiqueira.dev/pt-BR/projects/library-api-advanced)
[![Código](https://img.shields.io/badge/C%C3%B3digo-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/matheussiqueira-dev/library-api-advanced)

Além do CRUD, o projeto integra a OpenLibrary (com cache e rate limit), separa as camadas em rotas, serviço e repositório e roda como uma Function Python na Vercel.

## 🚀 Tecnologias Core

- **Backend**: FastAPI (Python 3.12) com validação de entrada e saída via Pydantic v2.
- **Banco de Dados**: SQLite com **SQLAlchemy 2.0 (Async)** e `aiosqlite`.
- **Arquitetura**:
  - **Repositório** (`app/repositories/`): acesso a dados, com um repositório base genérico para o CRUD.
  - **Serviço** (`app/services/`): regras de negócio e integração com a OpenLibrary.
  - **Injeção de dependências** do FastAPI para sessão de banco e serviço (substituídas nos testes).
- **Migrações**: Alembic, com a migração inicial em `alembic/versions/` e um teste que compara `upgrade head` com os modelos.
- **Frontend**: HTML server-rendered (Jinja2), JavaScript sem framework, CSS próprio e ícones Lucide.
- **Integrações**: OpenLibrary API para busca automática de metadados via ISBN (com cache em memória).
- **Observabilidade**: Logs com nível configurável e middleware que adiciona `X-Request-Id` e `X-Process-Time`.

## ✨ Funcionalidades Principais

- **Cadastro de livros**: título, autor, descrição, capa, ano, ISBN (com dígito verificador), idioma, páginas e status (disponível, emprestado, reservado, manutenção).
- **Busca de metadados por ISBN** na OpenLibrary, com cache em memória e rate limit próprio.
- **Busca com filtros** por texto (título/autor), autor, ano ou intervalo de anos, com paginação.
- **Indicadores do acervo** na interface: total de livros, ano mais recente e livros com ISBN (calculados no navegador a partir da página carregada).
- **Interface escura e responsiva**, com estados de carregamento e mensagens de retorno.
- **Documentação da API** em `/docs` (Swagger UI) e `/redoc`.

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
├── requirements.txt    # Dependências de runtime (instaladas pela Function)
└── requirements-dev.txt # Runtime + ferramentas de teste
```

## 🛠️ Instalação e Uso

### 1. Preparação do Ambiente
```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements-dev.txt  # só o runtime: pip install -r requirements.txt
```

### 2. Configuração do Banco
Por padrão (`DB_AUTO_CREATE=true`) o app cria as tabelas ao iniciar. Para gerenciar o schema por migrações, desligue a criação automática e aplique o histórico do Alembic:
```bash
DB_AUTO_CREATE=false alembic upgrade head
```

### 3. Execução
```bash
uvicorn app.main:app --reload
```

### 4. Testes e cobertura
Os testes usam um SQLite temporário e uma OpenLibrary simulada: não tocam o `library.db` local nem acessam a rede. O CI exige 90% de cobertura de `app/`.
```bash
pytest --cov=app --cov-fail-under=90
```

### 5. Lint, formatação e tipos
Configuração em `ruff.toml` e `mypy.ini` (a mesma que o CI usa).
```bash
ruff check .
ruff format --check .
mypy app
```

### 6. Auditoria de dependências
```bash
pip install pip-audit==2.10.1
pip-audit -r requirements.txt
```

O workflow de CI roda esses passos sob demanda (Actions → "CI - Build & Test" → Run workflow).

### 7. Acessos
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

## 🛡️ Práticas aplicadas

- **Repositório base** (`app/repositories/base.py`) com o CRUD genérico reaproveitado pelo repositório de livros.
- **Camadas separadas**: rotas não acessam o banco diretamente; regras ficam no serviço.
- **Validação de entrada** com Pydantic e limites testados em `tests/test_security.py`.
- **I/O assíncrono** no banco (SQLAlchemy async + aiosqlite) e na OpenLibrary (httpx). Desempenho ainda não medido; ver `docs/EVOLUTION.md`.
- **Feedback na interface** com toasts e estados de carregamento.

---

### Desenvolvido por Matheus Siqueira

**Analista de Dados & BI | Power BI • SQL • Python • DAX | ETL, Modelagem de Dados, KPIs e Automação**

Conecte-se e acesse meus projetos:

[![Portfólio](https://img.shields.io/badge/Portf%C3%B3lio-matheussiqueira.dev-000000?style=for-the-badge&logo=googlechrome&logoColor=white)](https://www.matheussiqueira.dev)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Matheus_Siqueira-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/matheussiqueira-dev)
[![GitHub](https://img.shields.io/badge/GitHub-matheussiqueira--dev-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/matheussiqueira-dev)
[![E-mail](https://img.shields.io/badge/E--mail-hellomatheusdev%40gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:hellomatheusdev@gmail.com)
