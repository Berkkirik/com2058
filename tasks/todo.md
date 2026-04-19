# COM2058 Project — Multi-Tenant Project Management SaaS ("TaskNest")

## Context

Ankara University COM2058 dönem projesi. Ödev: relational DB üzerine real-world bir uygulama tasarlamak ve geliştirmek; ER modeling, relational schema, query operations konularını göstermek (PDF: `docs/COM2058_Project.pdf`).

Kullanıcı **solo** çalışıyor. Domain seçimi: **Multi-tenant N:N rich SaaS**. Stack: **Python + FastAPI + Jinja2 + HTMX** (mevcut MySQL 8 + Docker setup'ı üzerine).

**Ürün: "TaskNest"** — küçük takımlar için multi-tenant proje yönetim SaaS (Linear/Asana mini). Workspace = tenant. Bu domain, dersin müfredatındaki tüm kavramları doğal şekilde barındırır.

---

## Ders Coverage Haritası (KRİTİK)

`lecture_presentations/Elmasri_6e_Ch*.ppt` içeriklerinden çıkarılan ders sırası ve ödevdeki karşılığı:

| Ch | Konu | Projede Nerede Gösterilecek |
|----|------|------------------------------|
| 01 | Database & DBMS basics | Report intro |
| 02 | DBMS architecture (3-schema, client/server) | Report architecture section |
| 03 | Relational data model + integrity constraints (PK/FK/CASCADE/NOT NULL/UNIQUE/CHECK) | Schema DDL'de explicit hepsi |
| 04 | Basic SQL (CREATE/SELECT/INSERT/UPDATE/DELETE, joins, WHERE) | App'in tüm CRUD query'leri |
| 05 | More SQL (aggregate, GROUP BY/HAVING, VIEW, TRIGGER, ASSERTION, ALTER) | `init/02_views.sql`, `init/03_triggers.sql`, ASSERTION report'ta |
| 06 | Relational algebra (σ, π, ⋈, ÷, ∪, ∩, −) | Report'ta 5-7 query için RA notasyonu |
| 07 | ER model: entity, weak entity, identifying relationship, recursive, binary/ternary, cardinality, participation | ER diagram'ın gövdesi |
| 08 | EER: specialization/generalization, disjoint/overlap, total/partial, attribute-defined subclass, category (union), aggregation | `attachments` specialization, `time_logs` aggregation, ER diagram'a explicit eklenecek |
| 09 | ER→relational mapping algoritması | Report'ta adım adım mapping anlatımı |
| 15 | Normalization: FD, 1NF→BCNF, 4NF (MVD), 5NF (JD), dependency preservation, lossless join | Report'ta her tablo için FD listesi + BCNF kanıtı; bir karşı örnek (denormalized) walk-through |
| 21 | Transaction processing, ACID, serializability, schedule recoverability | App'te explicit `BEGIN/COMMIT` + report'ta isolation level analizi |
| 22 | Concurrency control (locking, deadlock, 2PL) | `SELECT ... FOR UPDATE` demo; report'ta MySQL InnoDB locking |
| 23 | Recovery (deferred update, ARIES, checkpoint, backup) | `mysqldump` backup/restore demo + report'ta MySQL binlog/redo log notu |

**Sonuç:** Müfredat geniş; proje bunlar için yeterli "yüzey alanı" sunmalı. Plan buna göre güncellendi.

---

## Teslim Tarihleri

| Phase | İçerik | Tarih | Bugünden |
|-------|--------|-------|----------|
| 1 | Data Requirements (10%) | 26.04.2026 | **7 gün** |
| 2 | ER Diagram (20%) | 26.04.2026 | **7 gün** |
| 3 | Implementation + Demo (60%) | 24.05.2026 | 35 gün |
| 4 | Report 10-15 sayfa (10%) | 24.05.2026 | 35 gün |

İlk hafta Phase 1+2 (en kritik: ER diagram doğru olmadan implementation çürür). Sonraki 4 hafta implementation + report paralel.

---

## Domain: TaskNest — Genişletilmiş Şema

### Entity List (15 tablo + 3 EER specialization sub-table)

| # | Entity | Tip | Kullanılan Konsept (Ch) |
|---|--------|-----|-------------------------|
| 1 | `users` | Strong entity | Ch07 |
| 2 | `workspaces` | Strong entity, **composite attribute** (address: street/city/country/postal) | Ch07 |
| 3 | `workspace_members` | **Associative (M:N + role attribute)** | Ch07 |
| 4 | `projects` | Strong entity | Ch07 |
| 5 | `project_members` | **Associative (M:N + role)** | Ch07 |
| 6 | `tasks` | Strong + **recursive (parent_task_id)** | Ch07 |
| 7 | `task_dependencies` | **Recursive M:N** (task ↔ task as DAG, "blocks" relationship) | Ch07 |
| 8 | `task_assignees` | **Associative (M:N)** | Ch07 |
| 9 | `tags` | Strong (workspace-scoped) | Ch07 |
| 10 | `task_tags` | **Associative (M:N)** — multi-valued attribute → relation | Ch07 + Ch15 (1NF) |
| 11 | `comments` | **Weak entity** (PK: task_id + comment_no), identifying relationship to tasks | Ch07 |
| 12 | `attachments` | **EER Specialization superclass** (disjoint, total) | Ch08 |
| 12a | `attachment_image` | Subclass — width, height, mime_type | Ch08 |
| 12b | `attachment_file` | Subclass — file_size, mime_type, storage_path | Ch08 |
| 12c | `attachment_link` | Subclass — url, preview_text | Ch08 |
| 13 | `time_logs` | **Ternary relationship** (User × Task × Date) — log_date partial key, hours_logged | Ch07 (ternary), Ch08 (aggregation candidate) |
| 14 | `activity_log` | Audit (Strong, but conceptually aggregates events from multiple sources) | Ch08 (aggregation in ER), Ch21 (transaction trigger) |
| 15 | `notifications` | Strong (user_id FK, type enum, read_at) | Ch04 demo |

### EER Konseptleri — Explicit Yerleşim

1. **Specialization (disjoint, total):** `attachments` → 3 alt sınıf. Discriminator: `attachment_type` enum. Sub-tablolar PK = parent attachment_id (FK). Bu mapping Ch09'un "Option 8B - Multiple relations, superclass and subclasses" yöntemini gösterir.
2. **Generalization (bottom-up):** Report'ta `attachment_image/file/link` → `attachments` süreci anlatılacak.
3. **Aggregation:** `(workspace_member, project)` ilişkisi `project_team` olarak aggregate edilir (kavramsal); `time_logs` semantik olarak `(user assigned-to task)` aggregate'ine bağlı log'tur.
4. **Category / Union (opsiyonel, report'ta gösterilecek):** `mention` ER'de `MentionTarget` ⊃ User ∪ Tag (User ya da Tag mention edilebilir) — implementasyonda iki nullable FK ile çözülecek; report'ta "category" alternatifi tartışılacak.

### Relational Constraints (Ch03 — Schema'da explicit göstereceğimiz tipler)

- **Domain constraints**: ENUM('owner','admin','member','guest'), CHECK (hours_logged BETWEEN 0 AND 24)
- **Key constraints**: PRIMARY KEY her tabloda
- **Entity integrity**: NOT NULL on PK
- **Referential integrity**: ON DELETE CASCADE / SET NULL / RESTRICT — her FK'da bilinçli seçim
- **CHECK constraints**: tarih ilişkileri (started_at <= completed_at), pozitif sayılar
- **UNIQUE constraints**: email, workspace.slug, (workspace_id, slug) project'te
- **CREATE ASSERTION** (MySQL desteklemez ama report'ta gösterilecek): "her workspace'in en az bir owner'ı olmalı"

### Normalization Demo (Ch15)

Phase 1 doc'unda her tablo için:
- Functional dependencies listesi
- Candidate key(s)
- Hangi NF'de olduğu kanıtı (3NF veya BCNF hedef)
- BONUS: bir denormalized antipattern (örn. tasks tablosuna `assignees CSV` koymak) → 1NF ihlali → çözüm `task_assignees` tablosu. Bu tek örnek bile Ch15 anlayışını sergiler.

---

## Adım Adım Plan (10 adım)

Kullanıcı **adım adım** ilerlemek istiyor. Her adım bağımsız doğrulanır.

### Adım 1 — Phase 1: Data Requirements Doc (1-2 gün)

**Çıktı:** `docs/phase1_data_requirements.md`

İçerik:
1. **Sistem amacı + scope** (1 paragraf)
2. **Aktör listesi**: Owner, Admin, Member, Guest, Bot/Service Account
3. **Functional requirements** (FR-1 .. FR-N, ~25 madde)
4. **Data requirements**: her entity için açıklama + öznitelikler + business rules (örn. "bir task'a en az bir assignee olmalı")
5. **Constraints / assumptions**: multi-tenancy, soft delete, audit, tarih formatı, locale
6. **FD listesi + normalization analizi** (Ch15 alignment)

**Doğrulama:** Doc kullanıcı tarafından okunup onaylanır.

### Adım 2 — Phase 2: ER + EER Diagram (2-3 gün)

**Çıktılar:**
- `docs/phase2_er_diagram.drawio` (kaynak)
- `docs/phase2_er_diagram.png` (sunum export)
- `docs/phase2_er_explanation.md` (her diyagram elemanını numaralı açıklama — sunum notu)

**Notation:** Elmasri kitap stili **Chen notation** (kitabın Ch07-08'i bunu kullanıyor). Crow's foot opsiyonel ek diyagram olabilir.

**Diagram'da explicit gösterilecek:**
- Entity dikdörtgenleri (zayıf entity için **çift çerçeve**)
- İlişki eşkenar dörtgenleri (identifying relationship için **çift dörtgen**)
- Cardinality (1, M, N) her ilişkide
- Participation (zorunlu = çift çizgi, opsiyonel = tek çizgi)
- Composite attribute (oval altında alt-oval'lar — workspace.address)
- Multi-valued attribute (önce çift oval, sonra → "1NF için relation'a çevrildi" notu)
- Recursive relationship (tasks → tasks "subtask of"; tasks → tasks "blocks")
- Ternary relationship (User × Task × Date için time_logs)
- **EER**: attachments specialization (disjoint, total) — ⊂ sembolü, "d" disjoint discriminator, çift çizgi total
- **EER**: aggregation kutu (opsiyonel, report'ta açıklanacak)

**Doğrulama:** Diagram'da tüm 15 entity + 4 EER unsuru görünür ve okunabilir.

### Adım 3 — Relational Schema → SQL DDL (1 gün)

**Çıktı:** `init/01_schema.sql` — mevcut `lab4.sql` ve `tv_rankings.sql` style ile uyumlu. Mevcut MySQL Docker container `docker-entrypoint-initdb.d` mekanizmasıyla otomatik yükler. `init/lab4.sql` ve `init/tv_rankings.sql` olduğu gibi kalır.

DDL'de gösterilecekler:
- Tüm constraint tipleri (Ch03)
- ER→Relational mapping yorumları (Ch09 algoritmasına atıf, "Step 1-7" yorum satırları)
- Index'ler (öğretici amaçlı, EXPLAIN ile gösterileceği için)

**Doğrulama:**
```bash
docker compose down -v && docker compose up -d
docker exec com2058 mysql -uberkkirik -p25812633 com2058 -e "SHOW TABLES;"
docker exec com2058 mysql -uberkkirik -p25812633 com2058 -e "SHOW CREATE TABLE tasks\G"
```
15+ tablo görünmeli; FK constraint'ler `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` ile doğrulanır.

### Adım 4 — Views, Triggers, Seed Data (1-2 gün)

**Çıktılar:**
- `init/02_views.sql` — 5-7 view: `v_project_progress`, `v_user_workload`, `v_workspace_activity`, `v_overdue_tasks`, `v_top_tags`, `v_team_velocity`
- `init/03_triggers.sql` — 3 trigger:
  - `trg_task_status_change` → activity_log'a satır ekler (Ch05)
  - `trg_comment_no_assign` → comments'a yeni satır eklenirken `comment_no` auto-increment (weak entity partial key) (Ch07)
  - `trg_time_log_validate` → 24 saatten fazla log'u engeller (CHECK alternatifi)
- `init/04_seed.sql` — gerçekçi veri (3 workspace, 15 user, 10 proje, ~80 task, ~200 comment, ~50 time_log, 30 attachment her 3 tipten)

**Doğrulama:** Her view manuel sorgulanır; trigger task INSERT/UPDATE'te activity_log'a satır eklendiği test edilir.

### Adım 5 — FastAPI Scaffold (1 gün)

**Çıktı:** `app/` klasörü
```
app/
  main.py            # FastAPI app + lifespan + router include
  db.py              # asyncmy connection pool
  config.py          # Pydantic Settings (env vars)
  deps.py            # current_user, current_workspace dependencies
  routers/
    auth.py
    workspaces.py
    projects.py
    tasks.py
    analytics.py
  queries/           # raw SQL files
    workspaces.sql
    projects.sql
    tasks.sql
    users.sql
    analytics.sql
  templates/
    base.html        # HTMX + Tailwind CDN
    partials/
    pages/
  static/
    style.css
requirements.txt
Dockerfile
```

`docker-compose.yml` güncellenir: `app` servisi eklenir (port 8000).

**Önemli karar — ORM YOK:** `asyncmy` ile raw SQL parametrik. Bu, ders konseptlerinin görünürlüğü için kritik. Query'ler `app/queries/*.sql` altında dosya olarak tutulur (lab2 query exercises stili ile uyumlu).

**Doğrulama:** `docker compose up app` → `GET /health` 200 döner; DB bağlantısı (`SELECT 1`) loglanır.

### Adım 6 — Auth + Multi-Tenant Middleware (1 gün)

- Email + password (bcrypt hash) ile cookie session (`itsdangerous`)
- `current_workspace` dependency: URL slug'dan çözer (`/w/{slug}/...`)
- Her DB query'de workspace_id WHERE filtresi (tenant izolasyonu)

**Doğrulama:** İki workspace seed edilip cross-tenant erişimin 403 döndüğü manuel test edilir.

### Adım 7 — Core CRUD Sayfaları (4-5 gün)

HTMX server-rendered partial swap. Sayfa setleri:
- Workspace dashboard (üye + proje listesi)
- Project board (task listesi, status filtre, sürükle-bırak yerine status dropdown)
- Task detail (subtask, dependency, comment, assignee, tag, attachment, time log)
- User profile (workspaces I'm in)

**Doğrulama:** E2E akış (browser): register → workspace oluştur → 2. user davet → proje aç → task ekle → assign et → comment yap → tag ekle → attachment yükle → subtask oluştur → time log gir.

### Adım 8 — Analytics + Transaction Demo (1-2 gün)

Analytics sayfası DB view'larını UI'a bağlar. Her panel altında "Show SQL" linki ile ham query gösterilir (sunum altın madeni).

**Transaction demo (Ch21):** "Move task to another project" işlemi explicit `BEGIN; UPDATE tasks; INSERT activity_log; UPDATE project_progress; COMMIT;` ile yapılır. Failure path'i (ROLLBACK) test edilir.

**Concurrency demo (Ch22, opsiyonel):** "Claim task" (atomic assign) için `SELECT ... FOR UPDATE` kullanılır. Report'ta deadlock senaryosu anlatılır.

### Adım 9 — Phase 4: Report (10-15 sayfa, 3-4 gün)

**Çıktı:** `docs/phase4_report.pdf`

İskelet (her bölüm dersteki bir Ch'a atıf yapacak):
1. **Introduction & motivation** (1 sayfa) → Ch01
2. **System architecture** (1 sayfa, 3-schema diagram) → Ch02
3. **Data requirements summary** (1 sayfa) → Phase 1 özeti
4. **ER & EER diagram + design rationale** (2-3 sayfa) → Ch07-08
5. **ER→Relational mapping** (Ch09 algoritması adım adım, 7 step) (2 sayfa)
6. **Schema constraints + normalization** (her tablo BCNF kanıtı + 1 denormalized counter-example) (1-2 sayfa) → Ch03 + Ch15
7. **Sample queries** (5-7 query: SQL + RA notasyonu + EXPLAIN çıktısı) (2-3 sayfa) → Ch04-06
8. **Triggers, views, transactions** (1 sayfa) → Ch05, Ch21
9. **Application screenshots + tech stack** (1-2 sayfa)
10. **Concurrency & recovery notes** (½ sayfa, kısa) → Ch22-23
11. **Conclusion + future work** (½ sayfa)

Markdown → Pandoc → PDF.

### Adım 10 — Sunum + Demo Hazırlığı (1-2 gün)

- 12-15 slayt deck (Ch7 ER + Ch8 EER + canlı demo + analytics + transaction demo)
- Demo akışı prova
- Backup screenshot'lar
- Q&A için anticipated questions list (ER kararları, neden raw SQL, neden multi-tenant)

---

## Kritik Dosyalar

| Yol | Durum | İçerik |
|-----|-------|--------|
| `docs/COM2058_Project.pdf` | mevcut | Ödev metni |
| `docs/phase1_data_requirements.md` | yeni | Phase 1 teslim |
| `docs/phase2_er_diagram.drawio` + `.png` + `_explanation.md` | yeni | Phase 2 teslim |
| `init/01_schema.sql` | yeni | DDL |
| `init/02_views.sql` | yeni | Analytics views |
| `init/03_triggers.sql` | yeni | Triggers |
| `init/04_seed.sql` | yeni | Demo data |
| `app/` (yapısı yukarıda) | yeni | FastAPI uygulaması |
| `docker-compose.yml` | güncellenecek | `app` servisi eklenecek |
| `docs/phase4_report.md` + `.pdf` | yeni | Final rapor |

Mevcut korunacaklar: `init/lab4.sql`, `init/tv_rankings.sql`, `lecture_presentations/`, `.gitignore`, `.env`.

---

## Stack Seçimleri (kesinleşmiş)

- **DB:** MySQL 8.0 (mevcut Docker)
- **Backend:** Python 3.11+, FastAPI, uvicorn (asgi)
- **DB Driver:** `asyncmy` — raw SQL, parametrik
- **Validation:** Pydantic v2
- **Templates:** Jinja2 + HTMX (CDN) + Tailwind CSS (CDN, build step yok)
- **Auth:** `itsdangerous` cookie session + `bcrypt`
- **Migration:** Yok — `init/*.sql` re-runnable script'ler (eğitim odaklı, `down -v && up`)
- **Containerization:** `docker-compose.yml` `app` servisi eklenecek

---

## Verification Plan (Per-Step)

```bash
# Adım 3 (schema) sonrası
docker compose down -v && docker compose up -d
docker exec com2058 mysql -uberkkirik -p25812633 com2058 -e "SHOW TABLES;"
docker exec com2058 mysql -uberkkirik -p25812633 com2058 -e "
  SELECT TABLE_NAME, COUNT(*) AS fk_count FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
  WHERE TABLE_SCHEMA='com2058' AND REFERENCED_TABLE_NAME IS NOT NULL
  GROUP BY TABLE_NAME;
"

# Adım 4 (views/triggers) sonrası
docker exec com2058 mysql -uberkkirik -p25812633 com2058 -e "
  SHOW TRIGGERS;
  SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA='com2058';
  SELECT * FROM v_project_progress LIMIT 5;
"

# Adım 5+ (app) sonrası
docker compose up -d
curl http://localhost:8000/health

# Adım 7 (CRUD) — manuel browser E2E
# register → workspace → project → task → comment → tag → attachment → subtask → time log

# Adım 8 (transaction) — Python REPL veya pytest
# 1. transaction commit ok
# 2. transaction rollback (force exception) → state unchanged

# Final (Adım 10)
mysqldump -u root -p com2058 > backup.sql  # Ch23 demo
```

---

## Riskler & Karar Noktaları

| # | Risk | Karar |
|---|------|-------|
| 1 | ORM mı raw SQL mi? | **Raw SQL** — ders konseptleri görünür, report'ta query verme kolay |
| 2 | Auth scope? | Basit cookie session — JWT/OAuth scope'a gereksiz |
| 3 | Multi-tenancy modeli? | Shared schema, shared DB — workspace_id WHERE her query'de |
| 4 | EER specialization gerçekten implement mi yoksa sadece diyagramda mı? | **Implement edilecek** (3 sub-table) — Ch08 puanı için |
| 5 | Ternary relationship gerekli mi? | **Evet** — Ch07 explicit konsept; `time_logs` doğal |
| 6 | Concurrency demo (FOR UPDATE) gerekli mi? | Opsiyonel — 35 günde yetişiyorsa Adım 8'e dahil |
| 7 | Sunum dilini ne yapacağız? | Türkçe (kullanıcı belirleyecek) |
| 8 | ER notation: Chen vs Crow's foot? | Chen birincil (kitap stili), Crow's foot opsiyonel ek |

---

## Sonraki Adım

Plan onaylanırsa: **Adım 1 — Phase 1 Doc** ile başlıyoruz. Önce kullanıcıya sorulacak son detaylar:
- Ürün adı "TaskNest" sana uyuyor mu?
- ER diagram aracı: draw.io (offline desktop) mı, dbdiagram.io (web, DBML) mı?
- Sunum dili Türkçe mi İngilizce mi?

Sonra `docs/phase1_data_requirements.md` yazılır.
