# COM2058 Project — TaskNest (Final Refined Plan v2)

## Context
Ankara University COM2058 dönem projesi. Solo öğrenci. Multi-tenant project management SaaS "TaskNest". MySQL 8 + FastAPI + Jinja2 + HTMX + asyncmy (raw SQL, no ORM). Müfredat: Elmasri 6e Ch01-09, Ch15, Ch21-23.

**Teslimler:** Phase 1+2 (10%+20%) → 26.04.2026 (7 gün), Phase 3 (60%) + Phase 4 (10%) → 24.05.2026 (35 gün).

---

## Akademik Hedefler — Müfredat → Proje Eşlemesi

| Ch | Konu | Projedeki Karşılık |
|---|---|---|
| 01-02 | DBMS, 3-schema | Report intro (1p) |
| 03 | Integrity constraints | DDL'de PK/FK/CASCADE/SET NULL/RESTRICT/CHECK/UNIQUE/NOT NULL hepsi |
| 04 | Basic SQL | App'in tüm CRUD query'leri |
| 05 | Aggregates, GROUP BY/HAVING, VIEW, TRIGGER, CREATE ASSERTION | `02_views.sql`, `03_triggers.sql`, ASSERTION report'ta |
| 06 | RA: σ π ⋈ ÷ ∪ ∩ − × γ ρ | Report'ta 12 query, **DIVISION dahil** |
| 07 | Entity, weak, identifying, recursive, ternary, cardinality, participation, composite/multivalued/derived | ER diagram'ın gövdesi |
| 08 | EER: specialization (disjoint+total VE overlapping+partial), category (union), aggregation, hierarchy/lattice | 3 farklı specialization tipi + 1 category + 1 aggregation + 1 lattice |
| 09 | ER→Relational mapping (7+EER opsiyonları) | Report'ta adım adım |
| 15 | 1NF→2NF→3NF→BCNF + 4NF (MVD) | Report'ta 1 tablo full walkthrough + 4NF MVD justification |
| 21 | Transactions, ACID, isolation | Two-session demo (dirty/non-repeatable/phantom) |
| 22 | 2PL, locks, deadlock | `SELECT FOR UPDATE` demo + `SHOW ENGINE INNODB STATUS` |
| 23 | Recovery | Binlog point-in-time recovery (15 min walkthrough) |

---

## Final Şema (14 tablo + 4 specialization sub-table)

**Cuts:** notifications (filler), dependency UI (table+seed kalır), tags UI, file upload (metadata only).

| # | Entity | Tip | Konsept |
|---|--------|-----|---------|
| 1 | `users` | **EER overlapping+partial specialization superclass** | Ch08 |
| 1a-c | `internal_users` / `external_users` / `bot_users` | predicate-defined, overlapping, partial subclasses | Ch08 |
| 2 | `workspaces` | composite attribute (address: street/city/country/postal) | Ch07 |
| 3 | `workspace_members` | M:N + role | Ch07 |
| 4 | `projects` | UNIQUE (workspace_id, project_id) | Ch07 |
| 5 | `project_members` | FK → `workspace_members.wm_id` (NOT user_id — tenant safety) | Ch07 |
| 6 | `task_statuses` | workspace-scoped lookup (drop ENUM) | Ch15 lookup table benefit |
| 7 | `sprints` | nullable FK to project | Ch07 (1:N + nullable participation) |
| 8 | `tasks` | recursive `parent_task_id` + composite FK `(workspace_id, project_id)` | Ch07 + Ch15 controlled denorm |
| 9 | `task_dependencies` | M:N recursive (table+seed only, no UI) | Ch07 |
| 10 | `task_assignees` | M:N | Ch07 |
| 11 | `tags` | UNIQUE (workspace_id, name) | Ch07 |
| 12 | `task_tags` | M:N — multivalued attr → relation | Ch07 + Ch15 (1NF) |
| 13 | `comments` | **weak entity** PK (task_id, comment_no), self-FK `parent_comment_id` (threading) | Ch07 (weak + recursive) |
| 14 | `attachments` | **EER disjoint+total specialization superclass** | Ch08 |
| 14a | `attachment_file` | subclass | Ch08 |
| 14b | `attachment_image` | **2-level lattice** (inherits from `attachments` AND `attachment_file`) | Ch08 hierarchy |
| 14c | `attachment_link` | subclass | Ch08 |
| 15 | `time_logs` | ternary (User × Task × Date) — alternatif: aggregation form | Ch07 ternary / Ch08 aggregation |
| 16 | `mentions` | **EER category** (User ∪ Tag ∪ Project) — discriminator + exactly-one-FK CHECK | Ch08 union |
| 17 | `activity_log` | polymorphic (entity_type, entity_id) — report'ta normalization risk | Ch15 trade-off |

### EER Konsept Yerleşimi
- **Specialization 1 (disjoint+total):** `attachments` — Elmasri Ch09 Option 8B (super + sub tables). Composite FK `(attachment_id, attachment_type)` ile DB-level disjointness.
- **Specialization 2 (overlapping+partial, predicate-defined):** `users.kind` ile internal/external/bot.
- **Category (union):** `mentions` — supertypes farklı keylere sahip (User, Tag, Project).
- **Aggregation:** `(user — assigned-to — task)` aggregate; `time_logs` aggregate→Date.
- **Hierarchy/Lattice:** `attachment_image` hem `attachments` hem `attachment_file`'dan inherit (2-level).

### Multi-Tenant Denormalization (Ch15 Trade-off)
`workspace_id` → tasks/comments/attachments/time_logs/activity_log'a denormalize, composite FK ile drift engellenir:
```sql
ALTER TABLE projects ADD UNIQUE KEY (workspace_id, project_id);
ALTER TABLE tasks
  ADD COLUMN workspace_id BIGINT NOT NULL,
  ADD FOREIGN KEY (workspace_id, project_id) REFERENCES projects(workspace_id, project_id);
```
Kontrollü 3NF ihlali — Ch15 trade-off bölümünün gold içeriği.

---

## RA Query Listesi (12 query, hepsi farklı operatör)

| # | Query | RA |
|---|-------|----|
| 1 | Workspace W'deki açık task'lar | σ, π |
| 2 | Task + assignee isimleri | ⋈ equi-join |
| 3 | Atanmamış task'lar | ⟕ left outer + σ IS NULL |
| 4 | Yorumlanmış task'lar | ⋉ semi-join |
| 5 | **Workspace'teki TÜM projelere atanmış kullanıcılar** | **÷ DIVISION** |
| 6 | Workspace A'da olup B'de olmayan kullanıcılar | − difference |
| 7 | Yorum yazmış VEYA atanmış kullanıcılar | ∪ union |
| 8 | Yorum yazmış VE atanmış kullanıcılar | ∩ intersection |
| 9 | Proje başına task sayısı + ort. saat | γ aggregate |
| 10 | Birbirini bloklayan task'lar | ρ rename + θ-join |
| 11 | Tüm (user, role_template) çiftleri | × cartesian |
| 12 | tasks ⋈ projects ⋈ workspaces | ⋈ natural join |

Query #5 (DIVISION) üç şekilde sunulur: SQL `NOT EXISTS … NOT EXISTS`, RA notation, English. A vs B notu farkı genellikle bu query'dir.

---

## Normalization Walkthrough (Ch15)

Report'ta 1 tablo üzerinden **1NF→2NF→3NF→BCNF** explicit FD listesi ile yürünür. Başlangıç: kasten kötü design (assignee_names CSV + role partial dependency).

**4NF (MVD):** `task_tags` ve `task_assignees` neden ayrı — `task_id →→ tag_id | task_id →→ user_id` MVD'si.
**`workspace_id` denormalization:** kontrollü 3NF ihlali tartışması.

5NF/JD skip.

---

## Transaction & Concurrency Demo (Ch21-22)

`docs/phase4_concurrency_demo.md` two-session terminal transcript:
1. Dirty read (READ UNCOMMITTED)
2. Non-repeatable read (READ COMMITTED)
3. Phantom prevention (REPEATABLE READ — InnoDB gap lock)
4. Deadlock (`SHOW ENGINE INNODB STATUS\G`)
5. `SELECT ... FOR UPDATE` atomic claim

`SELECT FOR UPDATE` mandatory.

---

## Recovery (Ch23) — Binlog PITR
Enable binlog → INSERT → mysqldump → INSERT more → DROP DB → restore dump → `mysqlbinlog` replay to timestamp. Half page in report. ARIES sadece cite.

---

## 10 Adım — Zaman Çizelgesi

Solo ~3-4 saat/gün ≈ 17-20 efektif gün. Buffer near zero.

| # | Adım | Gün | Tarih | Notlar |
|---|------|-----|-------|--------|
| 1 | Phase 1 doc (MVP — FD analizi report'a ertelenir) | 1-2 | 19-20 Apr | Sistem amacı, aktör, FR, entity desc, business rules, "Out-of-Scope" |
| 2 | Phase 2 ER+EER diagram (drawio, Chen notation) | 2-3 | 21-23 Apr | 14 entity + 4 spec subtable |
| 3 | DDL `init/01_schema.sql` | 1 | 24 Apr | Tüm constraint tipleri + ER→Relational yorum satırları |
| 4 | Views + Triggers + Seed (3 view, 3 trigger) | 1-2 | 25-26 Apr | **Phase 1+2 deadline 26 Apr** |
| 5 | FastAPI scaffold + asyncmy pool + tenant helper | 1 | 27 Apr | `tenant_query()` helper + 2 cross-tenant pytest test |
| 6 | Auth + multi-tenant middleware | 1 | 28 Apr | bcrypt + cookie session |
| 7 | **Vertical slice (tasks end-to-end)** | 3 | 29 Apr - 1 May | 5 entity + 2 sayfa |
| 7b | Diğer entity sayfaları | 3 | 2-4 May | Vertical slice template'i kopyala |
| 8 | Analytics + transaction demo + concurrency demo | 1-2 | 5-6 May | "Show SQL" linki |
| 9 | **Report 1-6. bölümler (paralel başlar)** | 5 | **7-11 May** | Phase 1+2 doc'larından çoğu hazır |
| 9b | Report 7-11. bölümler | 4 | 12-15 May | |
| 10 | Demo prova + slide + screencast backup | 2 | 16-17 May | 8 dakikalık akış |
| - | Buffer / polish | 7 | 18-24 May | Slippage absorbed |

Kritik kural: Report yazımı 4 May'den önce başlamalı.

---

## Cut List (Ruthless)

1. notifications table
2. Drag-drop task board (status dropdown yeterli)
3. Crow's foot alternatif diagram
4. Tag management UI (seed yeterli, table+M:N kalır)
5. Task dependency UI (table+seed+1 query, no UI)
6. Workspace invite flow (2 workspace pre-seeded)
7. File upload multipart (metadata only, fake storage_path)
8. HTMX her yerde (sadece task list filter + comment add)
9. 5-7 view → 3 view (`v_project_progress`, `v_user_workload`, `v_overdue_tasks`)
10. Pydantic Settings + ayrı bcrypt + ayrı itsdangerous (single auth.py)

---

## Top 3 Hidden Risks + Mitigation

1. **Multi-tenant `workspace_id` filter unutulması = veri sızıntısı.** → Day 1'de `tenant_query()` helper + 2 pytest cross-tenant test.
2. **Weak entity `comments.comment_no` autonumber concurrent insert duplicate-key.** → Trigger içinde `SELECT MAX(comment_no) FOR UPDATE` + explicit transaction. Bonus: report'ta Ch22 örneği olarak kullan.
3. **HTMX form validation rendering 2 gün yutar.** → Bir kez task formu için yap, copy-paste. Macro template.

---

## Phase 1+2 MVP (26 Apr için)

**Phase 1 doc (`docs/phase1_data_requirements.md`):**
- Sistem amacı + scope (½ p)
- Aktörler + 15-20 FR (1 p)
- Entity descriptions + attributes + business rules (3-4 p)
- Constraints/assumptions + Out-of-Scope section (½ p)
- FD/normalization analizi → Phase 4 report'a ertelendi

**Phase 2 ER diagram:**
- 14 entity + 4 spec subtable
- Cardinality + participation EVERY relationship
- Weak entity çift çerçeve (comments)
- Identifying relationship çift dörtgen
- Ternary (time_logs)
- Recursive (tasks self, comments self, task_dependencies)
- 2 specialization (disjoint+total: attachments; overlapping+partial: users)
- Category (mentions ∪ sembolü)
- Aggregation box (user-assigned-to-task)
- Composite attribute (workspace.address)

---

## Vertical Slice Definition (Adım 7 — ilk 3 gün)

**5 entity:** users, workspaces, projects, tasks, comments + auth.
**2 sayfa:** project board, task detail (comment add).
Yeşil olmadan diğer entity'lere geçme.

Yeşil tanımı:
- Register → workspace oluştur → proje oluştur → task ekle → comment ekle akışı browser'da çalışıyor
- Cross-tenant pytest test geçiyor
- Comment trigger activity_log'a satır ekliyor

---

## Demo Flow (8 dakika max)

login → workspace dashboard → project board (filter) → task detail aç → comment ekle → attachment ekle (EER) → time log (ternary) → analytics (3 view + "Show SQL" buton) → 2-session concurrency demo (dirty read).

Backup: Day 33'te 5 dakikalık screencast.

---

## Critical Files

| Path | İçerik |
|------|--------|
| `docs/phase1_data_requirements.md` | Phase 1 MVP teslim |
| `docs/phase2_er_diagram.drawio` + `.png` | Phase 2 teslim |
| `docs/phase2_er_explanation.md` | Diagram element açıklamaları |
| `init/01_schema.sql` | DDL — composite FK, specialization Option 8B, lattice |
| `init/02_views.sql` | 3 view |
| `init/03_triggers.sql` | comment_no autonumber, activity_log auto-insert, time_log validation |
| `init/04_seed.sql` | Seed data |
| `app/deps.py` | tenant_query helper (KRİTİK) |
| `app/queries/*.sql` | Raw SQL files |
| `docs/phase4_report.md` (10-15 p) | ER 4p + mapping 2p + normalization 2p + queries+RA 3p + transactions 1.5p + rest 2.5p |
| `docs/phase4_concurrency_demo.md` | Two-session terminal transcripts |

---

## Adım Adım İlerleme (checklist)

- [ ] **Adım 1:** `docs/phase1_data_requirements.md` (MVP)
- [ ] **Adım 2:** `docs/phase2_er_diagram.drawio` + `.png` + `_explanation.md`
- [ ] **Adım 3:** `init/01_schema.sql`
- [ ] **Adım 4:** `init/02_views.sql` + `init/03_triggers.sql` + `init/04_seed.sql`
- [ ] **Adım 5:** `app/` scaffold + asyncmy pool + tenant_query helper + 2 pytest test
- [ ] **Adım 6:** Auth + multi-tenant middleware
- [ ] **Adım 7:** Vertical slice (tasks end-to-end, 5 entity, 2 sayfa)
- [ ] **Adım 7b:** Diğer entity sayfaları
- [ ] **Adım 8:** Analytics + transaction demo + concurrency demo
- [ ] **Adım 9:** Report bölüm 1-6
- [ ] **Adım 9b:** Report bölüm 7-11
- [ ] **Adım 10:** Demo prova + slide + screencast backup
