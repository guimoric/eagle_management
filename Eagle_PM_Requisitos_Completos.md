# Projeto

## 1) Visão do produto

Um **web app local (on-prem)** para **1 usuário (PO)** gerenciar **time, releases, projetos e atividades**, com **dashboards operacionais** e **exportação** (CSV/XLSX).  
Funciona **100% offline** (sem CDN/sem APIs externas), com **persistência local em um arquivo `.db` (SQLite3)**.

**Como roda (experiência tipo “app”):**
- você abre um **executável**
- ele sobe um **servidor local** (porta automática)
- abre o navegador direto no **Daily Meeting**
- os dados ficam no **arquivo SQLite `.db`** usado pelo app

**Objetivo prático:** ter um “quadro de guerra” rápido pra daily e controle por projeto, sem depender de planilha ou internet.

---

## 2) Escopo

### 2.1 Em escopo

#### Cadastros e gestão

**Members**
- Campos: **Nome**, **Papel**, **Status** (Dropdown: *Ativo* ou *Férias*).

**Releases**
- Campos: **Código da Release**, **Status** (Dropdown: *Planned* [É o status inicial de toda release], *In Progress*[quando atingir o start date, o status deve mudar para IN Progress], *Installed*[quando a installation date for atingida o status deve mudar para installed])),
  **Date of Delivery**, **Start Date**, **Installation Date**,
  **Links** (links cadastrados pelo usuário: atividades relacionadas ao projeto e links do requisito do projeto).

**Projects**
- Campos: **Código PRXXXXXX**, **Título do Projeto**, **PM Responsável**, **EBA Responsável**,
  **Status** (Dropdown: *Pending HLE*, *Pending Approval*, *Approved*, *Planned*, *In Progress*, *E2E*, *Closed*, *Blocked*),
  **E2E Date**, **Target Release** (dropdown com **todas** as releases **não** *Installed*).

**Activities**
- Campos:
**Tipo** (Dropdown: *JIRA* ou *Internal*),
**Título**,
**Subtipo** (Dropdown: *STORY*, *BUG*, *PRODDEF*, *OPY*, *Internal*),
**Ticket Code** (Se houver um código do ticket do jira é preenchido text free),
**Assigned Member** (Dropdown com todos os members cadastrados; opcional),
**Project** (opcional; dropdown com **todos os projetos em aberto**),
**Target Release** (opcional),
**Start Date**,
**End Date** deve ser preenchido com a data da mudança de status para closed,
**Status** (Dropdown: *Planned*, *Open*, *Blocked*, *In Progress*, *Closed*),
**Links** (links cadastrados pelo usuário: atividades como “JIRA Links”).

#### Dashboards

**Daily Meeting**
- Lista **vertical** por **member que não está de férias**, mostrando **todas as activities atribuídas**.
- No final: seção com **activities sem member**.
- Botão para cadastrar uma nova activity (mesmo comportamento do botão “Novo” da tela de Activities).

**Project Control**
- Mostrar **projetos em andamento** e **todas as activities em aberto** por projeto.

#### Export por tela
- Cada tela de cadastro terá:
  - botão **Novo** (item do cadastro)
  - botão **Exportar CSV** (do cadastro)

---

### 2.2 Fora de escopo (por enquanto)
- Multiusuário, login, permissões
- Integração com Jira/Google/Slack/Email
- Importação de dados (além de abrir arquivos exportados)
- Sincronização em nuvem
- Notificações push e agendamento

---

## 3) Usuários e papéis

- **PO (único usuário)**: administra tudo (cadastros, edição, alterações de status, dashboards e exportações).

**Observação (implícita pelo escopo):**
- Não existe login/perfis/permissões. O app é local e operado por uma pessoa.

---

## 4) Restrições e premissas (offline/on-prem)

- **Sem internet**: o sistema deve funcionar totalmente offline, sem chamadas externas.
- **Assets locais**: CSS/JS/fontes devem estar empacotados no app (sem CDN).
- **Persistência local**: um único arquivo **SQLite `.db`**.
- **Execução como app “desktop”**:
  - inicia via **executável**
  - sobe **servidor local** em porta automática
  - abre o navegador direto no **Dashboard Daily Meeting**
- **Ambiente alvo inicial**: foco em **Windows**, mas sem dependências que impeçam rodar em outros SOs.

---

## 5) Requisitos não funcionais (NFR)

**NFR-001 Offline-first real**  
O sistema deve operar 100% offline (nenhuma dependência de internet).

**NFR-002 Performance**  
- Abrir o Dashboard Daily Meeting rapidamente (meta: ~<2s em cenário típico).
- Listagens e filtros devem responder bem com volume “realista” (ex.: milhares de activities).

**NFR-003 Robustez**  
- Validação forte no backend e no frontend.
- Mensagens de erro claras, indicando o campo/problema.
- Não permitir estados inválidos (ex.: release installed como target).

**NFR-004 Persistência simples e confiável**  
- Dados armazenados em **um único arquivo `.db` (SQLite3)**.
- O app deve suportar abrir/criar esse arquivo sem fricção.

**NFR-005 Segurança básica (ambiente local)**  
- Escape/encoding de campos de texto para evitar XSS na UI.
- Sanitização/validação de URLs exibidas como link.

**NFR-006 Acessibilidade e usabilidade**  
- Navegação por teclado.
- Foco correto em modais.
- Labels/aria em inputs e botões.

**NFR-007 Exportação confiável**  
- Exportar **CSV** em todas as telas de cadastro (download local).
- Arquivo gerado deve ser válido e abrir em Excel/Google Sheets (quando houver internet).

**NFR-008 Logs e diagnóstico (mínimo)**  
- Em caso de erro interno, registrar log local (arquivo) para troubleshooting.

---

## 6) Regras de negócio (BR)

**BR-001 Members**
- Member possui **Status**: *Ativo* ou *Férias*.
- Member em **Férias não aparece** no Dashboard **Daily Meeting** (lista vertical).
- Member em Férias **ainda pode existir no cadastro** e **pode permanecer atribuído** em activities (histórico), mas não entra na visão da daily.

**BR-002 Releases**
- Release possui **Status**: *Planned*, *In Progress*, *Installed*.
- **Release com status Installed não pode ser selecionada** como **Target Release** em Projects/Activities (dropdown deve excluir e backend deve bloquear).

**BR-003 Projects**
- **Project Code** deve seguir padrão **PR + dígitos** (ex.: PR01234567) e ser **único**.
- Project possui **Status** (Dropdown):
  - *Pending HLE*, *Pending Approval*, *Approved*, *Planned*, *In Progress*, *E2E*, *Closed*, *Blocked*.
- Campo **Target Release** do Project deve listar apenas releases **não Installed**.

**BR-004 Activities**
- Activity possui:
  - **Tipo**: *JIRA* ou *Internal*
  - **Subtipo**: *STORY*, *BUG*, *PRODDEF*, *OPY*, *Internal*
  - **Status**: *Planned*, *Open*, *Blocked*, *In Progress*, *Closed*
- **Assigned Member é opcional**.
- **Project é opcional**, mas o dropdown deve listar **apenas projetos em aberto** (não Closed).
- **Target Release é opcional**, mas se preenchido **não pode ser Installed**.
- Ao mudar status para **Closed**, registrar automaticamente o momento de fechamento (timestamp) **com a data da mudança de status**.
- O timestamp de fechamento deve existir e ser exibido na tela como **End Date**.

**BR-005 Dashboards**
- **Daily Meeting**:
  - Exibir lista vertical de members **não em férias**.
  - Em cada member: mostrar activities atribuídas com status **diferente de Closed**.
  - No final: seção **activities sem member**.
- **Project Control**:
  - Exibir **projetos em andamento** e suas **activities em aberto**.

**BR-006 Exclusões**
- Exclusão física pode ser evitada: preferir **desativar/arquivar** onde fizer sentido (principalmente para não quebrar histórico).
- Se uma entidade tiver vínculos (ex.: activity ligada a project/release), o sistema deve **bloquear exclusão** e explicar o motivo, ou converter para “arquivar” conforme regra definida na implementação.

## 7) Modelo de dados (alto nível)

> Objetivo: definir entidades e campos mínimos para suportar cadastros, dashboards, filtros e export CSV.

### 7.1 Entidades

#### 7.1.1 Member
- `id` (PK)
- `name` (obrigatório)
- `role` (obrigatório) — **FK** para `index_role`
  - `index_role` (tabela de índice):
    - `code` ('001','002','003')
    - `name` (`BA` | `QA` | `DEV`)
- `status` (obrigatório) — **FK** para `index_user_status`
  - `index_user_status` (tabela de índice):
    - `code` ('001','002')
    - `name` (`ACTIVE` | `VACATION`)
- `created_at`
- `updated_at`

---

#### 7.1.2 Release
- `id` (PK)
- `release_code` (obrigatório, único)
- `status` (obrigatório) — **FK** para `index_release_status`
  - `index_release_status` (tabela de índice):
    - `code` ('001','002','003')
    - `name` (`PLANNED` | `IN_PROGRESS` | `INSTALLED`)
- `delivery_date` (obrigatório)
- `start_date` (obrigatório)
- `installation_date` (obrigatório)
- `created_at`
- `updated_at`

##### ReleaseLink (links da release)
- `id` (PK)
- `release_id` (FK -> Release.id)
- `label` (obrigatório)
- `type` (obrigatório) — **FK** para `index_release_link_type`
  - `index_release_link_type` (tabela de índice):
    - `code` ('001','002','003')
    - `name` (`REQUIREMENT` | `JIRA` | `OTHER`)
- `url` (obrigatório)
- `created_at`
- `updated_at`

---

#### 7.1.3 Project
- `id` (PK)
- `project_code` (obrigatório, único) — padrão `PR` + dígitos
- `title` (obrigatório)
- `pm_responsible` (obrigatório) — texto (nome)
- `eba_responsible` (obrigatório) — texto (nome)
- `status` (obrigatório) — **FK** para `index_project_status`
  - `index_project_status` (tabela de índice):
    - `code` ('001','002','003','004','005','006','007','008')
    - `name` (`PENDING_HLE` | `PENDING_APPROVAL` | `APPROVED` | `PLANNED` | `IN_PROGRESS` | `E2E` | `CLOSED` | `BLOCKED`)
- `e2e_date` (opcional)
- `target_release_id` (FK opcional -> Release.id) — **não pode** apontar para release `INSTALLED`
- `created_at`
- `updated_at`

---

#### 7.1.4 Activity
- `id` (PK)
- `type` (obrigatório) — **FK** para `index_activity_type`
  - `index_activity_type` (tabela de índice):
    - `code` ('001','002')
    - `name` (`JIRA` | `INTERNAL`)
- `subtype` (obrigatório) — **FK** para `index_activity_subtype`
  - `index_activity_subtype` (tabela de índice):
    - `code` ('001','002','003','004','005')
    - `name` (`STORY` | `BUG` | `PRODDEF` | `OPY` | `INTERNAL`)
- `ticket_code` (opcional)
- `title` (obrigatório)
- `assigned_member_id` (FK opcional -> Member.id)
- `project_id` (FK opcional -> Project.id) — dropdown deve listar apenas projects `!= CLOSED`
- `target_release_id` (FK opcional -> Release.id) — **não pode** ser `INSTALLED`
- `start_date` (opcional)
- `status` (obrigatório) — **FK** para `index_activity_status`
  - `index_activity_status` (tabela de índice):
    - `code` ('001','002','003','004','005')
    - `name` (`PLANNED` | `OPEN` | `BLOCKED` | `IN_PROGRESS` | `CLOSED`)
- `end_date` (opcional) — preenchido automaticamente ao virar `CLOSED`
- `created_at`
- `updated_at`

##### ActivityLink (links da activity / “JIRA links”)
- `id` (PK)
- `activity_id` (FK -> Activity.id)
- `label` (obrigatório)
- `url` (obrigatório)
- `created_at`
- `updated_at`

---

### 7.2 Índices recomendados (SQLite)

> Foco: dashboards, filtros e dropdowns (status + FKs). Em SQLite, indexar FKs e colunas de filtro é o que mais dá ganho.

#### Constraints (unicidade)
- `release.release_code` **UNIQUE**
- `project.project_code` **UNIQUE**

#### Member
- `member(role)`  — FK p/ `index_role`
- `member(status)` — FK p/ `index_user_status`

#### Release
- `release(status)` — FK p/ `index_release_status`

#### ReleaseLink
- `release_link(release_id)`
- `release_link(type)` — FK p/ `index_release_link_type`

#### Project
- `project(status)` — FK p/ `index_project_status`
- `project(target_release_id)` — filtros por release / relatórios
- (opcional) `project(pm_responsible)` — se você for filtrar por PM
- (opcional) `project(eba_responsible)` — se você for filtrar por EBA

#### Activity
- `activity(status)` — FK p/ `index_activity_status` (dashboard e listas)
- `activity(type)` — FK p/ `index_activity_type`
- `activity(subtype)` — FK p/ `index_activity_subtype`
- `activity(assigned_member_id)` — Daily Meeting
- `activity(project_id)` — Project Control
- `activity(target_release_id)` — filtros
- (opcional) `activity(start_date)` — se você ordenar/filtrar por data
- (opcional) `activity(end_date)` — se você listar fechadas por período

#### ActivityLink
- `activity_link(activity_id)`

---

## 8) Navegação e padrões de UI

### 8.1 Menu principal (navbar)
- **Dashboards**
  - Daily Meeting
  - Project Control
- **Cadastros**
  - Members
  - Releases
  - Projects
  - Activities

### 8.2 Padrão de tela de cadastro (CRUD)
Cada tela de cadastro deve ter:
- **Tabela/lista** com **paginação**, **ordenação** e **filtros básicos**
- Botões no topo:
  - **Novo** (abre **popup**)
  - **Exportar CSV** (exporta o cadastro inteiro, **respeitando filtros**)
- Ações por item (linha/card):
  - **Editar**
  - **Excluir** (se permitido pelas regras) ou **Arquivar/Desativar** (se adotado no backend)

### 8.3 Padrão de formulário
- Campos obrigatórios com marcação visual
- Validação:
  - Frontend (UX) + Backend (regra final)
- Dropdowns devem carregar:
  - índices (`index_*`)
  - relacionamentos (members, releases, projects em aberto)
- Dropdowns devem ter **busca incremental**:
  - conforme o usuário digita, o dropdown filtra e exibe resultados relacionados à busca

### 8.4 Padrão de links (ReleaseLink / ActivityLink)
- Link sempre exibido como:
  - `label` (clicável)
  - `type` (ex.: REQUIREMENT/JIRA/OTHER) quando aplicável
- Comportamento:
  - **Link externo**: abrir sempre em nova aba/janela
  - **Link interno**: abrir **popup de visualização (view-only)**, **sem edição**
- Validar URL (http/https)

### 8.5 Feedback e erros
- Mensagem de sucesso ao salvar/editar/excluir
- Mensagem de erro explícita quando bloquear ação por regra de negócio (ex.: target release installed)

### 8.6 Padrão para dashboards
- Dashboards atualizam rápido e priorizam leitura:
  - sem excesso de cliques
  - ações rápidas (abrir/editar activity)
- Daily Meeting:
  - lista vertical por member (não férias) + seção “sem member”
  - Botão **Nova atividade** (mesmo utilizado na tela de cadastro de Activities)
- Project Control:
  - agrupado por projeto em andamento, exibindo activities em aberto

### 8.7 Padrão visual e layout (design system mínimo)
- **Layout limpo**: nada amontoado, nada “colado”.
- **Grid e espaçamento**:
  - usar um grid simples (container central + largura máxima)
  - espaçamentos consistentes por escala (ex.: 8px / 12px / 16px / 24px / 32px)
  - padding interno de cards/tabelas/formulários sempre presente (mínimo 16px)
- **Botões e ações**:
  - botões principais sempre no topo à direita (ex.: **Novo**, **Exportar CSV**)
  - ações destrutivas (Excluir) visualmente separadas e com confirmação
  - evitar muitas ações no mesmo bloco (usar menu “...” quando necessário)
- **Tabelas e listas**:
  - cabeçalho fixo e legível
  - linhas com altura mínima confortável
  - colunas alinhadas e sem texto encostado nas bordas
- **Formulários (popup)**:
  - 1 coluna (padrão) e 2 colunas só quando fizer sentido
  - labels acima do campo, help text abaixo
  - botões “Salvar / Cancelar” alinhados e com espaçamento
- **Responsividade**:
  - em telas menores, quebrar tabela em lista/card e manter botões acessíveis
- **Padrão de leitura**:
  - títulos claros, hierarquia (H1/H2), sem poluição visual
  - uso moderado de cores (status com badges discretos)

## 9) Páginas e comportamentos (detalhado)

> Este item descreve **todas as páginas** do sistema, seus **componentes**, **filtros**, **ações** e **regras de comportamento**.

### 9.1 Dashboards

#### 9.1.1 Daily Meeting
**Rota:** `/dashboards/daily-meeting` (home do app)

**Objetivo:** visão diária por pessoa (quem está fazendo o quê).

**Layout:**
- Lista **vertical** de seções, 1 seção por **Member com status ACTIVE** (members em VACATION não aparecem).
- Última seção fixa: **“Unassigned”** (activities sem assigned_member).

**Conteúdo de cada seção (member):**
- Lista de **Activities atribuídas** ao member com **status != CLOSED**
- Cada activity exibida como “card/linha” com:
  - Tipo / Subtipo (badges discretos)
  - Título
  - Ticket Code

**Ações:**
- Botão **Nova Activity** no topo (abre popup de criação igual ao da tela Activities).
- Em cada activity:
  - **Editar** (popup)
  - **Fechar** (muda status para CLOSED e grava End Date automaticamente)
  - **Link** (quando o link for externo, abre em nova aba)

**Regras:**
- Não mostrar members em férias.
- Não mostrar activities fechadas.
- Se um member mudar para férias, ele sai da daily imediatamente (sem apagar dados).

---

#### 9.1.2 Project Control
**Rota:** `/dashboards/project-control`

**Objetivo:** visão por projetos em execução.

**Layout:**
- Lista de **Projects em andamento** (definição: status em `PLANNED`, `IN_PROGRESS`, `E2E`, `BLOCKED`)
- Cada Project aparece como card/accordion com:
  - `project_code` + `title`
  - status (badge)
  - PM / EBA
  - Target Release
  - Contadores: total de activities em aberto, quantas bloqueadas
  - Lista de activities do projeto com **status != CLOSED**

**Ações:**
- Abrir/editar Project (**popup de edição**)
- Botão “Nova Activity” dentro do card do projeto (já vincula `project_id`)

**Regras:**
- Não exibir projects CLOSED.
- Dentro do projeto, não exibir activities CLOSED.

---

### 9.2 Cadastros (CRUD)

> Padrão comum: **tabela com paginação/ordenação/filtros**, botão **Novo** (popup), botão **Exportar CSV** (respeita filtros), e ações **Editar/Excluir**.

#### 9.2.1 Members
**Rota:** `/members`

**Tabela (colunas):**
- Nome
- Papel
- Status (ACTIVE/VACATION)
- Ações (Editar, Excluir/Desativar)

**Filtros:**
- Busca por nome (contains)
- Filtro por papel
- Filtro por status

**Novo/Editar (popup):**
- name (obrigatório)
- role (dropdown index_role)
- status (dropdown index_user_status)

**Regras:**
- Member VACATION não aparece no Daily Meeting.
- Assigned Member em Activity lista todos os members cadastrados (inclusive férias), mas o dashboard filtra quem aparece.

---

#### 9.2.2 Releases
**Rota:** `/releases`

**Tabela (colunas):**
- Release Code
- Status
- Delivery Date
- Start Date
- Installation Date
- Links (contador)
- Ações

**Filtros:**
- Busca por release_code
- Filtro por status

**Novo/Editar (popup):**
- release_code (obrigatório, único)
- status (dropdown index_release_status)
- delivery_date (obrigatório)
- start_date (obrigatório)
- installation_date (obrigatório)
- Links (sub-seção):
  - listar links
  - adicionar link (label, type, url)
  - editar/remover link

**Regras:**
- Se status = INSTALLED:
  - a release **não pode** aparecer em dropdown de Target Release (Projects/Activities)
  - validação no backend deve bloquear se for enviada mesmo assim
  - **informações não podem ser alteradas** (modo read-only no popup e bloqueio no backend)

---

#### 9.2.3 Projects
**Rota:** `/projects`

**Tabela (colunas):**
- Project Code
- Title
- PM Responsible
- EBA Responsible
- Status
- E2E Date
- Target Release
- Ações

**Filtros:**
- Busca por project_code/title
- Filtro por status
- Filtro por target release

**Novo/Editar (popup):**
- project_code (obrigatório, único, padrão PR + dígitos)
- title (obrigatório)
- pm_responsible (obrigatório)
- eba_responsible (obrigatório)
- status (dropdown index_project_status)
- e2e_date (opcional)
- target_release_id (dropdown com releases != INSTALLED)

**Regras:**
- Project com status CLOSED:
  - não aparece no Project Control
  - não aparece no dropdown de Project em Activity (somente “projetos em aberto”)

---

#### 9.2.4 Activities
**Rota:** `/activities`

**Tabela (colunas):**
- Type
- Subtype
- Title
- Assigned Member
- Project
- Target Release
- Start Date
- Status
- End Date
- Links (contador)
- Ações

**Filtros:**
- Busca por title
- Filtro por status (inclui opção “Somente abertas”)
- Filtro por type
- Filtro por subtype
- Filtro por assigned member (inclui “Sem membro”)
- Filtro por project (somente abertos)
- Filtro por target release (não installed)

**Novo/Editar (popup):**
- type (dropdown index_activity_type)
- subtype (dropdown index_activity_subtype)
- title (obrigatório)
- ticket_code (opcional; se existir no modelo)
- assigned_member_id (dropdown members; opcional)
- project_id (dropdown projects != CLOSED; opcional)
- target_release_id (dropdown releases != INSTALLED; opcional)
- start_date (opcional)
- status (dropdown index_activity_status)
- end_date (somente leitura; preenchido quando status vira CLOSED)
- Links (sub-seção):
  - listar links
  - adicionar link (label, url)
  - editar/remover link

**Regras:**
- Ao salvar com status = CLOSED:
  - setar `end_date` automaticamente (data/hora atual)
- Ao salvar com status != CLOSED:
  - se antes estava CLOSED, limpar `end_date`
- Não permitir target_release INSTALLED (UI e backend)
- Project dropdown deve excluir projects CLOSED (UI e backend)

---

### 9.3 Comportamentos comuns (telas/popup)

- **Popup (Novo/Editar)**:
  - abre centralizado, com padding e espaçamento consistente
  - fecha no “Cancelar” e no “X”
  - ao salvar com sucesso: fecha popup e atualiza a tabela/dashboard (sem recarregar a página inteira, se possível)
- **Ordenação padrão sugerida**:
  - Activities: por status (IN_PROGRESS, BLOCKED, OPEN, PLANNED, CLOSED) e depois por start_date
  - Projects: por status e depois por project_code
- **Export CSV**:
  - exporta o que está visível considerando filtros ativos
  - nome do arquivo inclui entidade + timestamp

## 10) Casos de uso (UC)

> Formato: objetivo + fluxo principal + regras/validações.

### 10.1 Members

#### UC-MEM-01 — Cadastrar Member
- **Objetivo:** criar um novo member.
- **Fluxo:**
  1) Usuário acessa **Members**
  2) Clica **Novo** (popup)
  3) Preenche **Nome**, **Papel** (index_role), **Status** (index_user_status)
  4) Salva
  5) Sistema valida, grava e atualiza a tabela
- **Regras/validações:**
  - `name` obrigatório
  - `role` obrigatório (FK index_role)
  - `status` obrigatório (FK index_user_status)

#### UC-MEM-02 — Editar Member
- **Objetivo:** atualizar um member.
- **Fluxo:** Members > Editar (popup) > alterar campos > salvar > atualizar tabela
- **Regras/validações:** mesmas do UC-MEM-01

---

### 10.2 Releases

#### UC-REL-01 — Cadastrar Release
- **Objetivo:** cadastrar uma release.
- **Fluxo:**
  1) Usuário acessa **Releases**
  2) Clica **Novo** (popup)
  3) Preenche: `release_code`, `delivery_date`, `start_date`, `installation_date`
  4) Salva
  5) Sistema define status inicial como **PLANNED** e grava
- **Regras/validações:**
  - `release_code` obrigatório e único
  - `delivery_date`, `start_date`, `installation_date` obrigatórios
  - Status inicial **sempre** `PLANNED` (não editável no momento do cadastro)

#### UC-REL-02 — Editar Release (quando não INSTALLED)
- **Objetivo:** alterar dados de uma release que ainda não está instalada.
- **Fluxo:**
  1) Usuário acessa **Releases**
  2) Clica **Editar** em uma release com status != INSTALLED
  3) Altera campos permitidos (ex.: datas, links)
  4) Salva
  5) Sistema grava e (se necessário) recalcula status baseado nas datas
- **Regras/validações:**
  - Se status atual = `INSTALLED` → bloquear (UC-REL-03)
  - Datas continuam obrigatórias
  - Ao alterar datas, o sistema deve recalcular o status conforme regra de data

#### UC-REL-03 — Bloquear edição de Release INSTALLED (Read-only)
- **Objetivo:** garantir imutabilidade de release instalada.
- **Fluxo:**
  1) Usuário tenta editar uma release `INSTALLED`
  2) Sistema abre popup em **modo view-only** ou bloqueia com mensagem
- **Regras:**
  - Nenhum campo pode ser salvo/alterado
  - Backend bloqueia update mesmo que a UI seja burlada

#### UC-REL-04 — Gerenciar Links da Release
- **Objetivo:** adicionar/editar/remover links de uma release.
- **Fluxo:**
  1) Abrir release (popup)
  2) Seção Links: listar
  3) Adicionar (label, type, url) / Editar / Remover
- **Regras/validações:**
  - `label` obrigatório
  - `type` obrigatório (index_release_link_type)
  - `url` obrigatório e válido (http/https)
  - Release `INSTALLED` → links também ficam **read-only**

#### UC-REL-05 (Sistema) — Atualizar status da Release por data
- **Objetivo:** atualizar automaticamente o status das releases conforme datas.
- **Quando roda:**
  - ao iniciar o app
  - periodicamente (scheduler local) e/ou ao abrir a tela de Releases
- **Regra:**
  - se `now >= start_date` e `now < installation_date` → status = `IN_PROGRESS`
  - se `now >= installation_date` → status = `INSTALLED`
  - caso contrário → status = `PLANNED`
- **Observação:**
  - atualização deve ser idempotente (rodar várias vezes não quebra nada)

---

### 10.3 Projects

#### UC-PROJ-01 — Cadastrar Project
- **Objetivo:** cadastrar um projeto PR.
- **Fluxo:**
  1) Usuário acessa **Projects**
  2) Clica **Novo** (popup)
  3) Preenche: `project_code`, `title`, `pm_responsible`, `eba_responsible`, `status`, `e2e_date` (opcional), `target_release_id` (opcional)
  4) Salva
  5) Sistema grava e atualiza tabela
- **Regras/validações:**
  - `project_code` obrigatório, único, padrão PR + dígitos
  - `title`, `pm_responsible`, `eba_responsible` obrigatórios
  - `status` obrigatório (index_project_status)
  - `target_release_id` (se preenchido) não pode apontar para release `INSTALLED` (UI e backend)

#### UC-PROJ-02 — Editar Project
- **Objetivo:** atualizar campos do projeto.
- **Fluxo:** Projects > Editar (popup) > alterar > salvar > atualizar tabela
- **Regras/validações:** mesmas do UC-PROJ-01

#### UC-PROJ-03 — Encerrar Project (CLOSED)
- **Objetivo:** mover um projeto para status `CLOSED`.
- **Fluxo:**
  1) Usuário edita o projeto e muda status para `CLOSED`
  2) Salva
  3) Sistema grava e remove o projeto do Project Control e dos dropdowns “projetos em aberto”
- **Regras:**
  - Project `CLOSED`:
    - não aparece no Project Control
    - não aparece no dropdown de Project em Activity

---

### 10.4 Activities

#### UC-ACT-01 — Cadastrar Activity
- **Objetivo:** cadastrar uma activity (JIRA ou Internal) com possíveis vínculos e links.
- **Fluxo:**
  1) Usuário acessa **Activities** (ou clica “Nova Activity” no Daily Meeting / Project Control)
  2) Clica **Novo** (popup)
  3) Preenche:
     - `type` (index_activity_type)
     - `subtype` (index_activity_subtype)
     - `title`
     - `ticket_code` (opcional, texto livre)
     - `assigned_member_id` (opcional)
     - `project_id` (opcional; somente projetos em aberto)
     - `target_release_id` (opcional; somente releases != INSTALLED)
     - `start_date` (opcional)
     - `status` (index_activity_status)
  4) Salva
  5) Sistema grava e atualiza a lista/dashboard
- **Regras/validações:**
  - `type`, `subtype`, `title`, `status` obrigatórios
  - `project_id` (se preenchido) deve ser project `!= CLOSED` (UI e backend)
  - `target_release_id` (se preenchido) deve ser release `!= INSTALLED` (UI e backend)
  - Se salvar já como `CLOSED` → preencher `end_date = now`

#### UC-ACT-02 — Editar Activity
- **Objetivo:** editar dados da activity, inclusive status.
- **Fluxo:** Activities/Dashboard > Editar (popup) > alterar > salvar
- **Regras:**
  - aplicar regras de status/end_date (UC-ACT-03)
  - manter validações de project/release

#### UC-ACT-03 — Fechar / Reabrir Activity (end_date automático)
- **Objetivo:** controlar fechamento e reabertura com `end_date` coerente.
- **Fluxo (fechar):**
  1) Usuário muda status para `CLOSED` (pela tabela ou dashboard)
  2) Sistema salva e seta `end_date = now`
- **Fluxo (reabrir):**
  1) Usuário muda status de `CLOSED` para qualquer outro
  2) Sistema salva e limpa `end_date`
- **Regras:**
  - `end_date` é **somente leitura** no popup

#### UC-ACT-04 — Gerenciar Links da Activity (JIRA Links)
- **Objetivo:** adicionar/editar/remover links de uma activity.
- **Fluxo:**
  1) Abrir activity (popup)
  2) Seção Links: listar
  3) Adicionar (label, url) / Editar / Remover
- **Regras/validações:**
  - `label` obrigatório
  - `url` obrigatório e válido (http/https)

---

### 10.5 Dashboards

#### UC-DASH-01 — Operar Daily Meeting
- **Objetivo:** acompanhar execução diária e agir rápido.
- **Fluxo:**
  1) Abrir Daily Meeting
  2) Sistema lista members `ACTIVE` e a seção **Unassigned**
  3) Em cada member: listar activities atribuídas com status != `CLOSED`
  4) Ações rápidas: editar / fechar / abrir link
- **Regras:**
  - members `VACATION` não aparecem
  - activities `CLOSED` não aparecem
  - ação **Link**:
    - se link externo → abrir nova aba
    - se houver múltiplos links, o sistema deve abrir o link “principal” (ex.: primeiro cadastrado) ou abrir um popup view-only para seleção (definir na implementação)

#### UC-DASH-02 — Operar Project Control
- **Objetivo:** acompanhar execução por projeto.
- **Fluxo:**
  1) Abrir Project Control
  2) Sistema lista projects com status: `PLANNED`, `IN_PROGRESS`, `E2E`, `BLOCKED`
  3) Em cada projeto: listar activities com status != `CLOSED`
  4) Criar nova activity já vinculada ao projeto (project_id pré-preenchido)
- **Regras:**
  - projects `CLOSED` não aparecem
  - activities `CLOSED` não aparecem

---

### 10.6 Exportação

#### UC-EXP-01 — Exportar CSV (por cadastro, respeitando filtros)
- **Objetivo:** exportar o cadastro atual em CSV, respeitando filtros e ordenação aplicados.
- **Fluxo:**
  1) Usuário acessa uma tela de cadastro (Members/Releases/Projects/Activities)
  2) Aplica filtros e ordenação
  3) Clica **Exportar CSV**
  4) Sistema gera o arquivo e baixa no computador
- **Regras:**
  - export deve refletir os filtros e a ordenação aplicados
  - nome do arquivo inclui entidade + timestamp

## 11) Critérios de aceite (AC)

> Critérios objetivos para considerar cada parte “pronta”.

### 11.1 Offline / Execução
**AC-001** O app abre e funciona **sem internet** (desconectar rede não quebra telas, nem CSS/JS).  
**AC-002** Ao iniciar pelo executável, o servidor local sobe e o navegador abre direto em **/dashboards/daily-meeting**.  
**AC-003** Os dados persistem em um único arquivo **SQLite `.db`** e continuam após reiniciar o app.

---

### 11.2 Members
**AC-010** É possível criar/editar member com `name`, `role`, `status` (dropdowns com busca).  
**AC-011** Members com status `VACATION` **não aparecem** no Daily Meeting.  
**AC-012** Members `VACATION` continuam disponíveis para seleção em Activity (Assigned Member), e atividades atribuídas a eles permanecem no histórico/lista.

---

### 11.3 Releases (datas + status automático)
**AC-020** Ao criar Release, o status inicial é sempre **PLANNED**.  
**AC-021** Quando `now >= start_date` e `now < installation_date`, o status passa automaticamente para **IN_PROGRESS** (sem ação do usuário).  
**AC-022** Quando `now >= installation_date`, o status passa automaticamente para **INSTALLED** (sem ação do usuário).  
**AC-023** Releases `INSTALLED` **não podem ser editadas** (popup read-only + backend bloqueando update).  
**AC-024** Releases `INSTALLED` **não aparecem** nos dropdowns de Target Release (Projects/Activities).

---

### 11.4 Projects
**AC-030** Project Code é validado (padrão PR + dígitos) e é único.  
**AC-031** Target Release do Project lista somente releases **!= INSTALLED** (UI e backend).  
**AC-032** Projects com status `CLOSED`:
- não aparecem no **Project Control**
- não aparecem no dropdown de Project em Activity

---

### 11.5 Activities
**AC-040** É possível criar/editar Activity com:
- type, subtype, title, status (dropdowns com busca)
- ticket_code (texto livre, opcional)
- assigned member (opcional)
- project (opcional, somente projetos em aberto)
- target release (opcional, somente releases != INSTALLED)
- start_date (opcional)
- end_date (somente leitura)
**AC-041** Ao salvar Activity com status `CLOSED`, o sistema preenche automaticamente `end_date = now`.  
**AC-042** Ao reabrir (mudar de `CLOSED` para qualquer outro status), o sistema limpa `end_date`.  
**AC-043** Activity não permite vincular:
- project `CLOSED` (UI e backend)
- release `INSTALLED` como target release (UI e backend)

---

### 11.6 Links (ReleaseLink / ActivityLink)
**AC-050** É possível adicionar/editar/remover links em Release e Activity com validação de URL (http/https).  
**AC-051** Links externos abrem em **nova aba/janela**.  
**AC-052** Links internos abrem popup **view-only** (sem edição).  
**AC-053** Em Release `INSTALLED`, links ficam **read-only**.

---

### 11.7 Dashboards
**AC-060** Daily Meeting exibe:
- seções verticais por member `ACTIVE`
- seção final **Unassigned**
- somente activities com status **!= CLOSED**
**AC-061** Daily Meeting permite:
- criar nova activity (popup)
- editar activity
- fechar activity (status -> CLOSED e end_date automático)
- abrir link externo via ação “Link”
**AC-062** Project Control exibe:
- projetos com status `PLANNED`, `IN_PROGRESS`, `E2E`, `BLOCKED`
- activities desses projetos com status **!= CLOSED**
**AC-063** Project Control permite criar activity já vinculada ao projeto.

---

### 11.8 Export CSV
**AC-070** Cada tela de cadastro possui botão **Exportar CSV**.  
**AC-071** O CSV exportado respeita os **filtros e a ordenação** aplicados na tela.  
**AC-072** O arquivo baixado abre corretamente no Excel (colunas coerentes, delimitador consistente).  
**AC-073** O nome do arquivo contém entidade + timestamp.

---

### 11.9 UI / Qualidade visual
**AC-080** Nenhuma tela apresenta elementos “colados” ou amontoados: padding e espaçamento consistente (escala fixa).  
**AC-081** Popups têm layout limpo, campos bem espaçados e botões “Salvar/Cancelar” alinhados.  
**AC-082** Dropdowns com busca incremental funcionam (digitar filtra opções sem travar).

## 12) Ideias opcionais (melhorias futuras)

> Tudo aqui é “nice to have”, não obrigatório para o MVP.

### 12.1 UX e velocidade de operação
- **Atalhos de teclado**
  - `N` = nova activity
  - `E` = editar activity selecionada
  - `C` = fechar activity (status -> CLOSED)
  - `/` = focar na busca/filtro da tela
- **“Quick edit” no card**
  - no Daily Meeting, permitir mudar status (Open/In Progress/Blocked) sem abrir popup
- **Modo Focus no Daily Meeting**
  - toggle “Só IN_PROGRESS + BLOCKED”

### 12.2 Qualidade de dados e controle
- **Histórico de mudanças**
  - registrar `changed_at`, `changed_by` (mesmo sendo single-user) e `from_status -> to_status` para Activities e Projects
- **Validações extras de datas**
  - impedir `installation_date < start_date`
  - impedir `delivery_date < start_date` (se fizer sentido no seu processo)

### 12.3 Produtividade offline
- **Backup/Restore do `.db`**
  - botão “Backup” (copia o arquivo .db)
  - botão “Restaurar” (substitui por um backup)
- **Snapshot diário do Daily Meeting**
  - export “Daily Snapshot” (CSV) com timestamp para criar histórico sem aumentar complexidade

### 12.4 Dashboard mais útil
- **Indicadores simples**
  - no Project Control: contagem por status (Open / In Progress / Blocked)
  - “Top blockers” (lista de activities BLOCKED)
- **Filtro global**
  - filtrar tudo por Target Release (uma release selecionada no topo)

### 12.5 Links melhor resolvidos
- **Link principal da Activity**
  - marcar um link como “principal”
  - ação “Link” do Daily Meeting abre sempre o principal
- **Popup de Links (view-only)**
  - se houver múltiplos links, abrir lista view-only para escolher

### 12.6 Empacotamento
- **Auto-update offline**
  - mecanismo simples de substituir executável mantendo `.db`
  - (ou assistente de migração de schema com versão do DB)

## 13) Riscos e mitigação

### 13.1 Riscos técnicos (offline/local)

**R-001 Perda/corrupção do arquivo `.db` (SQLite)**
- **Impacto:** alto (perde histórico e operação).
- **Mitigação:**
  - rotina simples de **backup** do `.db` (manual no MVP; botão no futuro)
  - export CSV frequente (por telas)
  - usar transações nas escritas e garantir fechamento correto do DB

**R-002 Atualização automática de status da Release falhar (scheduler/timezone/relógio do Windows)**
- **Impacto:** médio (status errado, dropdown e regras inconsistentes).
- **Mitigação:**
  - recalcular status ao:
    - iniciar o app
    - abrir a tela de Releases
  - usar horário local do sistema e registrar logs quando houver mudança
  - validação de datas: bloquear installation_date < start_date

**R-003 Regras “Release INSTALLED = read-only” burladas**
- **Impacto:** médio/alto (dados instalados alterados indevidamente).
- **Mitigação:**
  - enforce no backend: updates bloqueados sempre
  - UI em modo view-only para reduzir tentativa/erro

**R-004 Dropdowns com busca incremental ficarem lentos com volume**
- **Impacto:** médio (UX ruim).
- **Mitigação:**
  - paginação do dropdown (ex.: buscar conforme digita)
  - índices nos campos de filtro (status/FKs)
  - debounce na busca (ex.: 200–300ms)

**R-005 “Projetos em aberto” vs “Projetos em andamento” gerar confusão**
- **Impacto:** médio (usuário acha que sumiu algo).
- **Mitigação:**
  - deixar explícito:
    - “Em aberto” = `!= CLOSED` (dropdown)
    - “Em andamento” = `PLANNED/IN_PROGRESS/E2E/BLOCKED` (Project Control)
  - texto de ajuda nas telas e nos filtros

---

### 13.2 Riscos de produto/processo

**R-006 Dados inconsistentes por falta de validação**
- **Impacto:** médio.
- **Mitigação:**
  - validações fortes (formatos PR, URL, datas obrigatórias)
  - mensagens de erro claras
  - impedir selection de releases INSTALLED

**R-007 Falta de definição do comportamento da ação “Link” no Daily Meeting (quando houver múltiplos links)**
- **Impacto:** baixo/médio.
- **Mitigação:**
  - no MVP: abrir o **primeiro link** cadastrado
  - evolução: marcar link “principal” ou abrir popup view-only de seleção

---

### 13.3 Riscos operacionais

**R-008 Porta local ocupada / bloqueada**
- **Impacto:** médio (app não abre).
- **Mitigação:**
  - escolher porta livre automaticamente
  - mostrar URL/porta no launcher/log para acesso manual

**R-009 Logs insuficientes para suporte**
- **Impacto:** baixo/médio.
- **Mitigação:**
  - log local simples (arquivo), registrando erros e mudanças automáticas de status de release

## 14) Referência do baseline atual (escopo “fechado”)

> Este item é o “resumo executivo” do que está aprovado até agora — serve como checkpoint para desenvolvimento e validação.

### 14.1 O que o sistema é
- Web app **local/on-prem** para **1 usuário (PO)**.
- Roda via **executável** que inicia um **servidor local** e abre o navegador no **Daily Meeting**.
- Funciona **100% offline** (sem dependências externas).
- Persistência em **um único arquivo `.db` (SQLite3)**.

### 14.2 Cadastros (entidades e campos)
**Members**
- Nome, Papel (index_role), Status (index_user_status: ACTIVE/VACATION)

**Releases**
- Código, Datas obrigatórias (Delivery/Start/Installation), Status automático (PLANNED/IN_PROGRESS/INSTALLED), Links (label, type, url)

**Projects**
- PR Code, Título, PM Responsável (texto), EBA Responsável (texto),
- Status (index_project_status), E2E Date (opcional), Target Release (somente releases != INSTALLED)

**Activities**
- Type (index_activity_type), Subtype (index_activity_subtype), Título,
- Ticket Code (opcional, texto), Assigned Member (opcional),
- Project (opcional; somente projetos != CLOSED),
- Target Release (opcional; somente releases != INSTALLED),
- Start Date (opcional), Status (index_activity_status), End Date (auto ao fechar),
- Links (label, url)

### 14.3 Dashboards
**Daily Meeting**
- Lista vertical por Member `ACTIVE`
- Seção final **Unassigned**
- Mostra activities com status **!= CLOSED**
- Ações rápidas: Nova Activity, Editar, Fechar, abrir Link externo

**Project Control**
- Mostra Projects com status `PLANNED`, `IN_PROGRESS`, `E2E`, `BLOCKED`
- Dentro, activities com status **!= CLOSED**
- Permite criar activity já vinculada ao projeto

### 14.4 UI/UX padrão
- Menu: Dashboards e Cadastros (Members/Releases/Projects/Activities)
- Telas de cadastro: tabela com paginação/ordenação/filtros + Novo (popup) + Exportar CSV (respeitando filtros)
- Dropdowns com **busca incremental**
- Layout **limpo**, com espaçamentos consistentes (nada colado/amontoado)

### 14.5 Regras críticas (não negociar)
- Release status é **automático por data**
- Release `INSTALLED`:
  - **read-only**
  - não aparece como Target Release
- Project `CLOSED`:
  - não aparece no Project Control
  - não aparece no dropdown de Project em Activity
- Activity:
  - `end_date` auto quando status vira `CLOSED`
  - limpar `end_date` ao reabrir

### 14.6 Export
- Exportação **CSV** em todas as telas de cadastro, respeitando filtros/ordenação.
