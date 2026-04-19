# COM2058 Project — Phase 1: Data Requirements

**Project:** TaskNest — Multi-Tenant Project Management SaaS
**Course:** COM2058 Database Management Systems, Ankara University
**Author:** Berk Kırık
**Date:** 2026-04-19
**Phase 1 Weight:** 10% — Due: 2026-04-26

---

## 1. System Purpose & Scope

TaskNest is a multi-tenant Software-as-a-Service (SaaS) platform that allows multiple organizations (workspaces) to independently manage their projects, tasks, and team collaboration on shared infrastructure with strict data isolation. Each workspace is a logical tenant: members of one workspace cannot see, query, or modify data belonging to another workspace, even though all data lives in a single MySQL database instance.

The system supports the typical workflows of a small-to-medium engineering team:
- Creating workspaces and inviting team members with different roles
- Organizing work into projects, sprints (iterations), and tasks
- Breaking tasks into subtasks and modeling task-to-task dependencies
- Assigning multiple team members to a task with different responsibilities
- Discussing work via threaded comments on tasks
- Attaching files, images, and external links to tasks
- Logging time spent on tasks for billing and reporting
- Tagging tasks for cross-cutting categorization
- Auditing every state-changing action via an immutable activity log
- Mentioning users, tags, and projects from within comments

The scope is **deliberately limited** to functionality that exercises a wide range of relational database concepts (entities, relationships, weak entities, recursive relationships, ternary relationships, EER specialization/category/aggregation, normalization, transactions, concurrency) rather than competing with mature commercial offerings. Out-of-scope items are listed in §6.

---

## 2. Actors

| Actor | Description |
|-------|-------------|
| **Owner** | A workspace member with full control: can manage members, billing, projects, and delete the workspace. Exactly one Owner is required per workspace at all times (assertion). |
| **Admin** | Can manage projects and members, but cannot delete the workspace or change billing. |
| **Member** | Standard user — can be added to projects, create and update tasks, comment, and log time within projects they belong to. |
| **Guest** | A limited external collaborator (e.g., a client) granted read-only access to specific projects. |
| **Bot / Service Account** | A non-human account used for integrations (e.g., a CI bot that creates tasks from build failures). Authenticates with an API key rather than a password. |
| **Internal User** | A subtype: a person directly employed by the workspace organization, with employee number and hire date. |
| **External User** | A subtype: a freelancer or contractor with company name and hourly rate. |

A single user may simultaneously play multiple roles in different workspaces (e.g., Owner of "Acme Corp" and Member of "OpenStreet OSS"). Likewise, the **Internal User** and **Bot** subtypes can overlap (a single person may register a bot they own — overlapping specialization), and the **Guest** kind has no subclass row at all (partial participation in the specialization). These are formalized in §4.

---

## 3. Functional Requirements

### Account & Authentication
- **FR-1** A user can register with email and password.
- **FR-2** A user can log in via email and password and receive a session cookie.
- **FR-3** A user can log out, invalidating the session.
- **FR-4** Bot accounts authenticate via an API key (not password).

### Workspace Management
- **FR-5** Any registered user can create a new workspace; the creator becomes the Owner.
- **FR-6** A workspace has a globally unique slug, a display name, and a structured address (street, city, country, postal code) — the address is a composite attribute.
- **FR-7** An Owner or Admin can add or remove members and change member roles.
- **FR-8** A workspace must have at least one Owner at all times (system-level assertion).

### Project & Sprint Management
- **FR-9** An Admin or Owner can create a project within a workspace.
- **FR-10** A project's slug is unique within its workspace (composite uniqueness).
- **FR-11** A project can be split into sprints with a start and end date. A task may optionally belong to a sprint.
- **FR-12** Project members are drawn from workspace members — a non-member of a workspace cannot be added to its projects (referential constraint at the schema level).

### Task Management
- **FR-13** A task belongs to exactly one project (total participation).
- **FR-14** A task can have a parent task, forming a subtask hierarchy (recursive relationship).
- **FR-15** A task can declare zero or more "blocked-by" dependencies on other tasks within the same workspace (M:N recursive relationship; the resulting graph must be acyclic, enforced by application logic).
- **FR-16** A task can have zero or more assignees (M:N with users).
- **FR-17** A task can have zero or more tags (M:N; tag set is workspace-scoped).
- **FR-18** A task has a status drawn from a workspace-configurable list (e.g., "Backlog", "In Progress", "Review", "Done"); the status set is per-workspace, not a fixed enum.

### Comments
- **FR-19** A user can write comments on a task. Comments are weak entities: they have no identity outside the parent task. A comment is identified by the (task_id, comment_no) pair, where comment_no is auto-incremented within the task.
- **FR-20** A comment may have a parent comment (recursive self-FK), enabling threaded discussions.
- **FR-21** A comment may mention zero or more users, tags, or projects (category / union type — see §4).

### Attachments
- **FR-22** A task can have zero or more attachments.
- **FR-23** An attachment is one of three disjoint kinds: an Image (with width, height, MIME type), a File (with size, MIME type, storage path), or a Link (with URL and preview text). The kind is fixed at creation time and cannot change.
- **FR-24** An Image attachment additionally inherits the File attributes (size, MIME, storage path) — i.e., every image is also a file (lattice / multiple-inheritance specialization).

### Time Tracking
- **FR-25** A user assigned to a task can log hours worked on that task on a given calendar date. The combination (user, task, date) is unique. The system must reject negative or above-24-hour entries (CHECK constraint).

### Activity Log & Mentions
- **FR-26** Every state-changing action (task created/updated, comment posted, status changed, assignment added/removed, etc.) is recorded in an immutable activity log with actor, timestamp, entity type, and entity id (polymorphic association).
- **FR-27** A comment may mention any combination of users, tags, or projects. Each mention links the comment to exactly one of those three kinds (union/category type with discriminator + exactly-one-FK constraint).

### Reporting & Analytics
- **FR-28** The system provides aggregated views: project progress (% of tasks completed), per-user workload (active task count and hours logged this week), and overdue tasks per project.
- **FR-29** The user can browse the activity log filtered by workspace, actor, or entity type.

---

## 4. Data Requirements — Entity Descriptions

This section describes each entity, its attributes, and the business rules that constrain it. Cardinality and participation constraints are summarized in §5; the formal ER/EER diagram is delivered in Phase 2.

### 4.1 `users` (with EER specialization)

`users` is the **superclass** of an EER specialization on the discriminator attribute `kind ∈ {internal, external, bot, guest}`. The specialization is **predicate-defined**, **overlapping** (a user can simultaneously be `internal` and `bot`, e.g., an employee who registers a bot account), and **partial** (a `guest` user has no subclass row).

**Superclass attributes:** `user_id` (PK), `email` (UNIQUE), `password_hash` (NULL for bots), `display_name`, `kind`, `created_at`.

**Subclass `internal_users`:** `user_id` (PK, FK to users), `employee_no`, `hired_at`, `manager_user_id` (nullable self-FK — recursive relationship within internal employees).

**Subclass `external_users`:** `user_id` (PK, FK to users), `company_name`, `hourly_rate`, `currency`.

**Subclass `bot_users`:** `user_id` (PK, FK to users), `api_key_hash`, `owner_user_id` (FK to users — a person who owns the bot).

**Business rules:**
- A user with `kind='guest'` has no row in any of the three subclass tables.
- A user with `kind='internal'` has exactly one row in `internal_users`.
- A bot's owner must be a non-bot user.

### 4.2 `workspaces`

A workspace represents a tenant organization. Has a **composite attribute** `address(street, city, country, postal_code)` modeled as separate columns on the same table.

**Attributes:** `workspace_id` (PK), `slug` (UNIQUE, URL-safe), `name`, `address_street`, `address_city`, `address_country`, `address_postal_code`, `created_at`.

**Business rules:**
- Slug must be 3-32 characters, lowercase alphanumerics and hyphens only (CHECK constraint).
- Every workspace must have ≥ 1 Owner (asserted via application logic; in MySQL, CREATE ASSERTION is unsupported and discussed in the Phase 4 report).

### 4.3 `workspace_members` (associative)

Resolves the M:N relationship between users and workspaces. The role attribute on the relationship is modeled as a column.

**Attributes:** `wm_id` (surrogate PK), `workspace_id` (FK), `user_id` (FK), `role` ∈ {owner, admin, member, guest}, `joined_at`. UNIQUE constraint on `(workspace_id, user_id)`.

**Business rules:**
- A user can be a member of multiple workspaces but only once per workspace.
- The `wm_id` surrogate is used as the FK target by `project_members` to enforce that project membership requires workspace membership.

### 4.4 `projects`

**Attributes:** `project_id` (PK), `workspace_id` (FK), `slug`, `name`, `description`, `created_by` (FK to users), `created_at`, `archived_at` (nullable). UNIQUE on `(workspace_id, slug)` and additionally on `(workspace_id, project_id)` — the latter is required for the composite FK from `tasks` (see §4.8 and the Multi-Tenant Denormalization note in the project plan).

**Business rules:**
- Slug uniqueness is per-workspace, not global.

### 4.5 `project_members` (associative)

Resolves M:N between projects and workspace members.

**Attributes:** `pm_id` (PK), `project_id` (FK), `wm_id` (FK to `workspace_members`, **not directly to users**), `role` ∈ {lead, contributor, reviewer}, `added_at`. UNIQUE on `(project_id, wm_id)`.

**Business rule:** Because the FK targets `workspace_members.wm_id`, the schema enforces that a user can only join a project of a workspace they are already a member of.

### 4.6 `task_statuses`

**Attributes:** `status_id` (PK), `workspace_id` (FK), `name`, `display_order`, `is_terminal` (BOOL — e.g., "Done" is terminal). UNIQUE on `(workspace_id, name)`.

**Business rule:** Each workspace defines its own status workflow. Default seed: "Backlog", "In Progress", "Review", "Done".

### 4.7 `sprints`

**Attributes:** `sprint_id` (PK), `project_id` (FK), `name`, `started_at` (DATE), `ended_at` (DATE), `goal` (TEXT). CHECK `started_at <= ended_at`.

**Business rule:** Sprints belong to a project (1:N). A task may belong to at most one sprint (nullable FK on tasks).

### 4.8 `tasks`

The central operational entity. Combines several constructs at once: recursive parent-child (subtasks), composite FK to projects (for tenant-safe denormalization), and several M:N participations (assignees, tags, dependencies).

**Attributes:** `task_id` (PK), `workspace_id` (NOT NULL — denormalized for tenant filtering), `project_id` (NOT NULL), `sprint_id` (nullable FK), `parent_task_id` (nullable self-FK — recursive), `status_id` (FK to `task_statuses`), `title`, `description`, `priority` ∈ {low, normal, high, urgent}, `created_by` (FK), `assigned_at` (nullable), `due_date` (nullable), `completed_at` (nullable), `created_at`, `updated_at`.

**Composite FK:** `(workspace_id, project_id)` REFERENCES `projects(workspace_id, project_id)` — guarantees that `task.workspace_id` always matches its project's workspace; eliminates an entire class of multi-tenant data integrity bugs.

**Business rules:**
- A task's status must belong to the same workspace (cross-table tenant check, enforced via composite FK on status).
- A task's parent task must be in the same project.
- `completed_at IS NOT NULL` ⇔ status is terminal (application invariant).

### 4.9 `task_dependencies`

Recursive M:N: a task can be blocked by zero or more other tasks; a task can block zero or more other tasks.

**Attributes:** `from_task_id` (FK to tasks), `to_task_id` (FK to tasks), `created_at`. PK `(from_task_id, to_task_id)`. CHECK `from_task_id <> to_task_id`.

**Business rule:** The dependency graph must be acyclic (enforced in application — Phase 4 discusses why this is hard to enforce in pure SQL).

### 4.10 `task_assignees`

M:N between tasks and users. The fact that a user is assigned is what's modeled; the role of the assignee on the task is captured by the `role` column.

**Attributes:** `task_id` (FK), `user_id` (FK), `role` ∈ {implementer, reviewer, tester}, `assigned_at`. PK `(task_id, user_id, role)`.

**Business rules:**
- The same user may be assigned to the same task in multiple roles (e.g., implementer and reviewer simultaneously).
- The user must be a member of the project (application-enforced).

### 4.11 `tags` and `task_tags`

`tags` are workspace-scoped labels.
**`tags` attributes:** `tag_id` (PK), `workspace_id` (FK), `name`, `color`. UNIQUE `(workspace_id, name)`.

`task_tags` is the resolution of the M:N relationship.
**`task_tags` attributes:** `task_id` (FK), `tag_id` (FK). PK `(task_id, tag_id)`.

The pair `(task_assignees, task_tags)` is a deliberate **4NF demonstration**: assignees and tags are independent multivalued facts about a task, so they MUST live in separate tables (combining them would create a multivalued dependency violation).

### 4.12 `comments` (weak entity, recursive)

Comments are a **weak entity** owned by tasks. A comment has no identity outside the parent task.

**Attributes:** `task_id` (FK, partial of PK), `comment_no` (partial key, auto-numbered within task), `parent_comment_id` (nullable, recursive self-FK for threading), `author_user_id` (FK to users, NOT NULL), `body` (TEXT), `created_at`, `edited_at`. **PK `(task_id, comment_no)`.**

The relationship between `tasks` and `comments` is an **identifying relationship** (double diamond in ER notation, double rectangle for the weak entity).

**Business rule:** `comment_no` is assigned by a trigger that reads `MAX(comment_no) + 1` within the parent task with `FOR UPDATE` locking to prevent concurrent duplicate-key races.

### 4.13 `attachments` (EER specialization superclass + lattice)

The `attachments` table is the superclass of a **disjoint, total** specialization on `attachment_type ∈ {image, file, link}`.

**Superclass attributes:** `attachment_id` (PK), `task_id` (FK), `uploaded_by` (FK to users), `attachment_type` (discriminator), `original_name`, `uploaded_at`. UNIQUE `(attachment_id, attachment_type)` to enable the disjointness-enforcing composite FK on subclasses.

**Subclass `attachment_file`:** `attachment_id` (PK), `attachment_type` (CHECK = 'file' OR 'image'), `file_size`, `mime_type`, `storage_path`. Composite FK `(attachment_id, attachment_type)` REFERENCES `attachments`.

**Subclass `attachment_image`:** `attachment_id` (PK), `attachment_type` (CHECK = 'image'), `width`, `height`. Composite FK `(attachment_id, attachment_type)` REFERENCES `attachment_file` — every image is also a file. **This is a 2-level lattice / multiple-inheritance specialization** (image inherits from both `attachment_file` and `attachments` transitively).

**Subclass `attachment_link`:** `attachment_id` (PK), `attachment_type` (CHECK = 'link'), `url`, `preview_text`. Composite FK to `attachments`.

**Business rules:**
- Disjointness is enforced at the database level via the composite-FK trick: a row in `attachment_image` cannot be re-pointed to a `link` superclass row because the `attachment_type` column is constrained.
- Total participation: every superclass row must have a corresponding subclass row of the matching type (enforced by application logic / trigger; explicitly discussed in the Phase 4 report).

### 4.14 `time_logs` (ternary relationship)

Models the ternary relationship "user logs N hours on task T on date D".

**Attributes:** `user_id` (FK), `task_id` (FK), `log_date` (DATE), `hours_logged` (DECIMAL(4,2)), `note` (nullable). PK `(user_id, task_id, log_date)`. CHECK `hours_logged > 0 AND hours_logged <= 24` and `log_date <= CURRENT_DATE`.

**Business rule:** A user can only log time on a task they are currently assigned to — see §7 for the alternative aggregation modeling discussion.

### 4.15 `mentions` (EER category / union type)

A mention links a comment to **exactly one** of three different entity types: a user, a tag, or a project. Because users, tags, and projects have **different keys** and are not naturally subsumed by a common superclass, this is modeled as an **EER category** (union type).

**Attributes:** `mention_id` (PK), `comment_task_id` + `comment_no` (composite FK to comments), `target_type` ∈ {user, tag, project}, `target_user_id` (nullable FK), `target_tag_id` (nullable FK), `target_project_id` (nullable FK).

**Business rule (CHECK constraint):** Exactly one of `target_user_id`, `target_tag_id`, `target_project_id` is non-NULL, matching the value of `target_type`.

### 4.16 `activity_log` (polymorphic audit)

Append-only audit log capturing every state-changing event. Uses a polymorphic association — `entity_type` + `entity_id` together identify the affected entity.

**Attributes:** `event_id` (PK, auto-increment), `workspace_id` (FK — for tenant filtering), `actor_user_id` (FK), `entity_type` ∈ {task, comment, project, member, status}, `entity_id` (BIGINT — no FK because it points to different tables depending on entity_type), `action` ∈ {created, updated, deleted, status_changed, assigned, unassigned, commented}, `payload_json` (JSON — the diff or relevant context), `occurred_at` (DATETIME).

**Business rule:** Rows in `activity_log` are inserted automatically by triggers on the source tables and never updated or deleted by application logic. The polymorphic association is a deliberate denormalization that trades referential integrity for append-only audit simplicity — this trade-off is explicitly analyzed in the Phase 4 report (Ch15 normalization discussion).

---

## 5. Cardinality & Participation Summary

A more formal version with all relationships will be in the Phase 2 ER diagram. Highlights:

| Relationship | Card. | Participation (left, right) |
|--------------|-------|------------------------------|
| user — workspace_member — workspace | M:N | (partial, total — via assertion) |
| workspace_member — project_member — project | M:N | (partial, partial) |
| project — tasks | 1:N | (partial, **total**) |
| task — subtask (parent_task_id) | 1:N recursive | (partial, partial) |
| task — task_dependencies — task | M:N recursive | (partial, partial) |
| task — task_assignees — user | M:N | (partial, partial) |
| task — task_tags — tag | M:N | (partial, partial) |
| task — comments | 1:N **identifying** (weak) | (partial, **total**) |
| comment — comment (parent) | 1:N recursive | (partial, partial) |
| task — attachments | 1:N | (partial, **total**) |
| attachments → {image, file, link} | EER specialization (disjoint, total) | total |
| attachment_file → attachment_image | EER lattice (image is also a file) | total |
| user × task × date — time_logs (ternary) | M:N:N | (partial, partial, partial) |
| comment — mentions — {user ∪ tag ∪ project} | EER category | (partial, partial) |
| any state-changing entity → activity_log | polymorphic 1:N | (partial, partial) |

---

## 6. Constraints, Assumptions & Out-of-Scope

### 6.1 Cross-Cutting Constraints
- **Multi-tenancy:** Every query that touches data must filter by `workspace_id`. The application enforces this via a centralized `tenant_query()` helper; the database additionally enforces tenant consistency between related rows via composite foreign keys (e.g., `tasks(workspace_id, project_id)` REFERENCES `projects(workspace_id, project_id)`).
- **Soft delete:** Workspaces, projects, and tasks support `archived_at` rather than physical DELETE; physical deletion is reserved for GDPR-style user erasure and bot deprovisioning.
- **Time zones:** All timestamps are stored in UTC. Display conversion happens in the application layer.
- **Character set:** UTF-8 (utf8mb4) throughout, with case-insensitive collation for emails.

### 6.2 Assumptions
- A single MySQL 8.0 instance hosts all tenants — schema isolation is logical, not physical.
- The application layer enforces business invariants that cannot be expressed in MySQL (e.g., "every workspace has ≥ 1 owner", DAG acyclicity for task dependencies, "time_logs requires active assignment"). These are documented as `CREATE ASSERTION`-style constraints in the Phase 4 report even though MySQL does not enforce assertions natively.
- File uploads store metadata only in this implementation; physical file storage uses a placeholder `storage_path` value (academic project scope).

### 6.3 Out-of-Scope (for this academic project)
- Real file storage (S3, local disk multipart upload)
- Email/push notifications
- Billing, subscription, or payment workflows
- OAuth / SSO / two-factor authentication
- Real-time collaboration (websockets, presence)
- Search beyond simple `LIKE` and a FULLTEXT demo
- Mobile or native clients
- Webhooks, integrations, or public API beyond the application's own use
- Internationalization beyond UTF-8
- High-availability replication, sharding, or backup automation (manual `mysqldump` / binlog PITR is demonstrated in the Phase 4 report)
- A scheduled `notifications` table — explicitly cut from scope to keep the entity count focused on academically meaningful concepts.

### 6.4 Deferred to Phase 4 Report
- Functional dependency analysis for every table
- 1NF → 2NF → 3NF → BCNF walkthrough on a designated table (`task_assignees`)
- 4NF MVD justification for the `task_tags` / `task_assignees` separation
- Discussion of the controlled 3NF violation (denormalized `workspace_id`)
- Relational algebra equivalents for 12 representative SQL queries (including a DIVISION query)
- Two-session transaction isolation demo
- Binlog point-in-time recovery walkthrough

---

*End of Phase 1 Data Requirements.*
