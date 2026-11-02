# Plano de Evolução — library-api-advanced

> Documento vivo, revisado semanalmente. Última revisão: 2026-11-02.
> Regra central: nenhuma mudança entra sem estar ligada a um objetivo desta página e sem manter ou melhorar as métricas da seção 2.

## 1. Identidade do projeto

- **Propósito:** "Library Studio": API e interface web de referência para gestão de acervo bibliográfico (CRUD de livros, busca com filtros, estatísticas e preenchimento de metadados por ISBN via OpenLibrary), publicada como demo do portfólio.
- **Tipo:** API REST (FastAPI) com frontend server-rendered (Jinja2 + JavaScript vanilla), em uma Function Python na Vercel.
- **Stack:** Python 3.12 (`.python-version`), FastAPI 0.143.0 (Starlette 1.7.0), Pydantic 2.14.1, pydantic-settings 2.2.1, SQLAlchemy 2.0.27 async + aiosqlite 0.19.0, Alembic 1.13.1, uvicorn 0.27.1, Jinja2 3.1.6, httpx 0.27.0, python-dotenv 1.2.4; dev (`requirements-dev.txt`): pytest 9.0.3 + pytest-asyncio 1.4.1, pytest-cov 7.1.0, ruff 0.17.0 (`ruff.toml`), mypy 2.4.1 (`mypy.ini`, plugin do Pydantic). Frontend com Lucide 1.48.0 (SRI) e ReDoc 2.5.4.
- **Gerenciador de pacotes:** pip com `requirements.txt` (runtime, instalado pela Function) e `requirements-dev.txt` (runtime + testes e lint), sem lock de hashes.
- **Deploy:** Vercel, preset FastAPI (entrypoint `app/main.py`), `vercel.json` só exclui testes e arquivos de desenvolvimento do bundle; produção em https://library-api-advanced.vercel.app. Sem `DATABASE_URL`, usa SQLite efêmero em `/tmp` com seed.
- **Estrutura:**
  - `app/api/v1/` — rotas (`endpoints/books.py`, `router.py`);
  - `app/core/` — config, banco, ISBN, cache, rate limit, headers de segurança, logging;
  - `app/models/`, `app/schemas/`, `app/repositories/`, `app/services/` — camadas de dados, DTOs, repositório e regras (inclui `demo_seed.py`);
  - `app/web/` — `templates/index.html`, `static/app.js`, `static/styles.css`;
  - `tests/` — pytest (`test_books.py`, `test_security.py`, `test_demo_mode.py`, `conftest.py` com SQLite temporário e OpenLibrary simulada);
  - `alembic/` — migrações (sem versões geradas no repositório).
- **Comandos:** install `python -m venv .venv && pip install -r requirements.txt` · dev `uvicorn app.main:app --reload` · lint `ruff check . && ruff format --check .` · typecheck `mypy app` · test `pytest` (instalar `requirements-dev.txt`) · build não se aplica (`python -c "import app.main"` como verificação de import).

## 2. Estado atual (baseline)

| Verificação | Comando | Resultado | Data |
| --- | --- | --- | --- |
| Instalação | `python3.12 -m venv .venv && pip install -r requirements-dev.txt` · runtime isolado `pip install -r requirements.txt && python -c "import app.main"` | PASS (Python 3.12.3) · PASS, sem pytest no runtime | 2026-11-02 |
| Lint | `ruff check .` · `ruff format --check .` | 0 achados · 26 arquivos formatados | 2026-11-02 |
| Typecheck | `mypy app` (`mypy.ini`) | 0 erros em 17 arquivos | 2026-11-02 |
| Testes | `pytest -q -p no:cacheprovider` | 67 passando / 0 falhando | 2026-11-02 |
| Cobertura | `pytest --cov=app --cov-fail-under=90` (gate no CI) | 98% total (590 statements); menor módulo `books.py` 94%. O salto vem também de `concurrency = greenlet`: antes, as linhas depois de cada `await` do SQLAlchemy contavam como não cobertas, então o 86% anterior estava subestimado | 2026-11-02 |
| Build | — | não se aplica (Function Python sem etapa de build) | 2026-11-02 |
| Vulnerabilidades (audit) | `pip-audit -r requirements.txt` · `pip-audit -r requirements-dev.txt` (2.10.1) | runtime: 0 · dev: 0 | 2026-11-02 |
| CI no GitHub | API do GitHub (Actions) | run de `a293739` (2026-10-28) falhou sem executar passos, como os anteriores; outros repositórios voltaram a executar em 2026-11-02; resultado deste ciclo na seção 10 | 2026-11-02 |

Observações:
- 2026-11-02: FastAPI 0.143.0 + Starlette 1.7.0 entraram no PR #5 e pytest 9.0.3 no PR #7, ambos mergeados pelo dono; o audit zerou.
- O PR #1 da padronização (2026-10-10) resolveu XSS armazenado, `.venv310`/`library.db`/`__pycache__` versionados (`git ls-files` limpo: 0 ocorrências), rate limit, kill switch, CSP e limites de entrada. Não entram como pendentes.
- Produção não verificada neste ambiente (saída de rede restrita). Persistência durável (Postgres) não está configurada: a demo reinicia o acervo a cada cold start.
- O histórico ainda carrega cerca de 800 mil linhas de `.venv310` removidas em 2026-10-10 (`.git` com 18 MB); purga exige reescrita de histórico e aprovação.

## 3. Histórico e trajetória

- **Fase 1 — base (2025-12-11):** refatoração para FastAPI + SQLAlchemy async em camadas, testes e CI; commit com `.venv310` inteiro versionado (cerca de 3.900 arquivos).
- **Fase 2 — redesign (2026-01-22 a 2026-02-03):** "senior upgrades", UI glassmorphism, revisão da arquitetura de backend e licença MIT.
- **Fase 3 — padronização (2026-10-10, PR #1):** `.gitignore`, remoção do venv/banco/bytecode do índice, correção de XSS, proteção das rotas de escrita, Python 3.12 no CI, modo demo na Vercel com SQLite efêmero e seed, três correções seguidas de resiliência do seed.
- **Fase 4 — identidade (2026-10-10/11, PRs #2 a #4):** footer e metadados de autoria, renomeação para "Library Studio", remoção de selos e textos "senior".
- **Churn (últimos 50 commits, sem o venv):** `README.md` (8), `app/web/templates/index.html` (7), `app/main.py` (7), `app/web/static/styles.css` (6), `app/core/config.py` (6). O seed de demo exigiu três `fix:` consecutivos, sinal de inicialização frágil.
- **Débitos herdados:** pins de fevereiro de 2026 nunca atualizados, CI só com pytest, README com afirmações de marketing ("performance extrema", "experiência excepcional") sem medição, Alembic sem nenhuma migração versionada.

## 4. Objetivos definidos (critério de parada)

| # | Eixo | Objetivo | Métrica | Baseline | Meta | Prioridade | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O1 | Funcionamento | Produção saudável e CI que barra regressões | `/health` 200 em produção; jobs do CI (pytest, lint, typecheck, audit) | não verificado; CI só pytest | 200; 4 checks verdes por 4 semanas | P0 | ativo |
| O2 | Cobertura de testes | Cobrir repositório e serviço | cobertura de `app/` · menor módulo | 86% · 62% | ≥ 90% · ≥ 80% | P2 | monitorado (meta atingida em 2026-11-02: 98% · 94%) |
| O3 | Segurança | Zerar vulnerabilidades conhecidas | achados do `pip-audit` | 24 | 0 | P0 | monitorado (meta atingida; `pip-audit` no CI) |
| O4 | Performance | Medir latência das rotas principais | p95 de `GET /api/v1/books` e `/lookup` (cache quente) em teste local | não medido | baseline registrado; `GET /books` p95 ≤ 50 ms local | P3 | ativo |
| O5 | Qualidade/Manutenibilidade | Lint e tipos limpos com config versionada | achados ruff · erros mypy | 124 · 11 | 0 · 0 | P1 | monitorado (meta atingida em 2026-11-02; mypy no CI) |
| O6 | Dados | Persistência durável e schema migrado | migrações Alembic versionadas; dados sobrevivem a redeploy | 0 migrações; SQLite efêmero | 1+ migração inicial; livro criado persiste após redeploy (com aprovação de Postgres) | P2 | ativo |

## 5. Guardrails

- Mudança só com objetivo associado (O#) ou item de backlog (B#); refatoração sem ganho mensurável é proibida.
- Nenhuma métrica da seção 2 pode piorar; se piorar, a mudança é revertida.
- Upgrade de versão major, mudança de arquitetura, remoção de funcionalidade e alteração de deploy exigem aprovação do dono (entram em "Decisões pendentes").
- No máximo uma feature nova por semana, de risco baixo, atrás de testes.
- Testes nunca tocam `library.db` local, banco real nem a OpenLibrary real (mock obrigatório).
- Conteúdo do usuário entra no DOM só por `textContent`; nenhum script inline na interface; script externo só com versão exata e SRI.
- Rotas de escrita mantêm kill switch, rate limit e limite de corpo; mudanças nesses limites exigem teste.
- Sem reescrita de histórico (purga do `.venv310`) sem aprovação explícita.

## 6. Backlog priorizado

- P0 = quebra funcionamento/segurança · P1 = risco alto · P2 = qualidade · P3 = melhoria

- [x] **B1 (P0, O3)** (Jinja2 e dotenv em `b04b570`; FastAPI 0.143.0 + Starlette 1.7.0 no PR #5 do dono) Atualizar FastAPI/Starlette para versões sem advisories (Starlette ≥ 1.3.1 implica FastAPI recente; major de fato, com aprovação), Jinja2 ≥ 3.1.6 e python-dotenv ≥ 1.2.2 — `pip-audit -r requirements.txt` com 0 no runtime; 58 testes passando.
- [x] **B2 (P0, O3/O1)** (2026-11-02, `955cd00`) Adicionar `pip-audit` ao CI — job falha em qualquer achado do runtime.
- [x] **B3 (P1, O5)** (2026-10-26, `843d84e`; pytest continua 8.0.0 no dev porque a 9 é major) Separar `requirements-dev.txt` (pytest ≥ 9.0.3, pytest-asyncio, pytest-cov, ruff, mypy) do runtime — bundle da Function sem pytest; `pip install -r requirements.txt` não instala pacotes de teste.
- [x] **B4 (P1, O5)** (2026-10-26, `d96eb36`; `ruff.toml` em vez de `pyproject.toml`, que o projeto não tem; `BookStatus` virou `StrEnum` e os genéricos usam PEP 695, sem mudança de valor gravado ou serializado) Versionar configuração de ruff (`pyproject.toml`) e aplicar `ruff check --fix` + `ruff format` — `ruff check .` e `ruff format --check .` com 0 no CI.
- [x] **B5 (P1, O5)** (2026-11-02, `8fc31a4`; `async_sessionmaker` no lugar de `sessionmaker(class_=AsyncSession)`, plugin do Pydantic para `Settings`) Corrigir os 11 erros de `mypy app` (tipos de retorno do repositório, `order_by` tipado) e rodar no CI — `mypy app` com 0.
- [ ] **B6 (P1, O1)** Smoke de produção registrado — `/health` 200, `/` com HTML, `/docs` carregando, headers CSP/`nosniff`/`Referrer-Policy` presentes; anotado na seção 10.
- [x] **B7 (P2, O2)** (2026-11-02, `16c4eeb`; repositório e serviço ≥ 99%) Testes de repositório e serviço (paginação, filtros de ano, falha da OpenLibrary, cache expirado) — `book_repository.py`, `book_service.py` e `base.py` ≥ 80%; total ≥ 90% com `--cov-fail-under=90` no CI.
- [ ] **B8 (P2, O6)** Gerar a migração Alembic inicial a partir dos modelos e testar `alembic upgrade head` em SQLite temporário — teste de CI aplica a migração e compara com `Base.metadata`.
- [ ] **B9 (P2, O6)** Persistência durável com Postgres gerenciado (com aprovação de serviço externo) — livro criado por POST é lido após redeploy; `DATABASE_URL` só nas env vars da Vercel.
- [ ] **B10 (P2, O5)** Reescrever o README sem afirmações não medidas e com comandos reais (lint, typecheck, cobertura) — cada afirmação aponta para código ou teste.
- [ ] **B11 (P2, O3)** Fixar actions por SHA e adicionar Dependabot (`pip`, `github-actions`) — PRs semanais com CI completo.
- [ ] **B13 (P1, O1)** Restabelecer a execução do CI (job não chega a um runner desde 2026-10-24) — conferir cobrança/minutos do Actions da conta; próximo push com o job executando os passos.
- [x] **B14 (P2, O3)** (PR #7 do dono, `8fc50c9`) pytest 9.0.3 em `requirements-dev.txt` (major, com aprovação) — `pip-audit -r requirements-dev.txt` sem o PYSEC do pytest; 58 testes passando.
- [ ] **B12 (P3, O4)** Medir latência local com `httpx.AsyncClient` em loop e registrar p95 — números na seção 10, sem afirmar desempenho no README sem essa medição.

## 7. Radar técnico

| Data | Item | Fonte | Veredito (adotar / avaliar / descartar) | Motivo |
| --- | --- | --- | --- | --- |
| 2026-11-02 | `concurrency = greenlet` no coverage.py | https://coverage.readthedocs.io/en/latest/config.html | adotado (`16c4eeb`) | SQLAlchemy async roda em greenlets; sem isso a cobertura aparece subestimada. |
| 2026-11-02 | Starlette 1.10.0 e FastAPI 0.162.0 disponíveis | https://fastapi.tiangolo.com/release-notes/ | monitorar | `pip-audit` sem achados nas versões atuais; sem objetivo ativo que peça a subida. |
| 2026-10-26 | FastAPI 0.162.0 aceita `starlette>=0.46.0` | https://fastapi.tiangolo.com/release-notes/ | adotar (com aprovação, B1) | Permite Starlette 1.3.1, que fecha os 14 achados restantes. |
| 2026-10-26 | Starlette 1.0 (marco de API estável, março de 2026) | https://simonwillison.net/2026/mar/22/starlette | avaliar com B1 | Saída da linha 0.x; revisar middlewares e `TemplateResponse` nos testes. |
| 2026-10-26 | Jinja2 3.1.6 e python-dotenv 1.2.4 | https://pypi.org/project/Jinja2/ | adotado (`b04b570`) | Patch/minor sem mudança de API; 58 testes verdes. |
| 2026-10-23 | Starlette 1.x (correções de DoS e path handling) | https://www.starlette.io/release-notes/ | adotar (com aprovação) | 8 IDs abertos na 0.36.3; exige subir FastAPI junto. |
| 2026-10-23 | FastAPI recente com Pydantic 2.1x | https://fastapi.tiangolo.com/release-notes/ | adotar | Necessário para Starlette corrigido; validar `Depends` e respostas de erro nos testes. |
| 2026-10-23 | pytest 9 (correção PYSEC-2026-1845) | https://docs.pytest.org/en/stable/changelog.html | adotar | Dev-only, mas aparece no audit por estar no mesmo `requirements.txt`. |
| 2026-10-23 | Ruff como lint + format | https://docs.astral.sh/ruff/ | adotar | Mesmo padrão dos outros repositórios Python do portfólio. |
| 2026-10-23 | FastAPI na Vercel (preset e limites de Function) | https://vercel.com/docs/frameworks/backend/fastapi | avaliar | Confirmar tamanho de bundle e cold start após o upgrade de dependências. |
| 2026-10-23 | `uv lock` com hashes | https://docs.astral.sh/uv/concepts/projects/sync/ | avaliar | Lock reprodutível; muda o fluxo de instalação, requer aprovação. |

## 8. Ideias de features

| # | Feature | Valor para o usuário/portfólio | Risco | Status (proposta / aprovada / implementada / descartada) |
| --- | --- | --- | --- | --- |
| F1 | Empréstimos (entidade `Loan`, prazo, devolução, atraso) | Regra de negócio real além de CRUD; demonstra transações e estados | médio (schema novo + migração) | proposta |
| F2 | Exportar acervo em CSV | Reuso em planilha; demonstra streaming de resposta | baixo | proposta |
| F3 | Paginação por cursor e ETag em `GET /books` | Demonstra boas práticas de API e cache HTTP | baixo | proposta |
| F4 | Busca textual (FTS5 no SQLite / `tsvector` no Postgres) | Busca por relevância; demonstra índices | médio (depende do banco escolhido) | proposta |
| F5 | Auditoria de alterações (quem/quando, sem PII) | Rastreabilidade; demonstra modelagem de eventos | médio | proposta |

## 9. Decisões pendentes do dono

- Verificar cobrança/minutos do GitHub Actions: o CI dos repositórios privados não está chegando a um runner desde 2026-10-24.
- Persistência: Postgres gerenciado (Neon via Vercel Marketplace) ou manter SQLite efêmero com seed?
- Purgar `.venv310` do histórico (reescrita + force-push) ou manter o histórico como está?
- Escrita pública: manter CRUD aberto com rate limit ou passar a demo para somente leitura com escrita protegida?
- Locale: PT-BR apenas ou PT-BR + EN (inclusive mensagens de erro da API)?

## 10. Registro semanal

| Data | Auditoria | Mudanças (commits) | Métricas | Próximo foco |
| --- | --- | --- | --- | --- |
| 2026-10-23 | Documento inicial e baseline | — | ver seção 2 | B1, B2 (O3) |
| 2026-10-26 | CI sem executar (job não chega ao runner); 24 achados de audit | `b04b570` fix (Jinja2, dotenv), `843d84e` build (requirements-dev), `d96eb36` style (ruff + CI); docs | audit runtime 24 → 14; ruff 124 → 0; formato 17 → 0 arquivos pendentes; testes 58 → 58; cobertura 86% → 86%; mypy 11 → 11 | B13 (CI), aprovação de B1, B5, B2 depois de B1. Nenhuma feature neste ciclo |
| 2026-11-02 | Audit zerado pelos PRs #5 e #7 do dono; cobertura estava subestimada (greenlet); último CI sem executar passos | `8fc31a4` fix (mypy + CI), `16c4eeb` test (camada de dados + gate), `955cd00` ci (pip-audit); docs | testes 58 → 67; cobertura 86% → 98%; mypy 11 → 0; audit runtime 14 → 0; O2, O3 e O5 monitorados | B6 (produção), B8, B11. Nenhuma feature neste ciclo |
