CREATE TABLE IF NOT EXISTS workflows (
  id uuid PRIMARY KEY,
  user_task text NOT NULL,
  status varchar(64) NOT NULL,
  branch_name varchar(255),
  base_ref varchar(255) NOT NULL DEFAULT 'main',
  max_retries integer NOT NULL DEFAULT 3,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  parent_task_id uuid REFERENCES tasks(id),
  kind varchar(64) NOT NULL,
  title varchar(512) NOT NULL,
  description text NOT NULL,
  status varchar(64) NOT NULL,
  priority integer NOT NULL DEFAULT 100,
  attempt_count integer NOT NULL DEFAULT 0,
  max_attempts integer NOT NULL DEFAULT 3,
  input jsonb NOT NULL,
  output jsonb,
  dependency_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_kind ON tasks(kind);

CREATE TABLE IF NOT EXISTS task_dependencies (
  task_id uuid NOT NULL REFERENCES tasks(id),
  depends_on_task_id uuid NOT NULL REFERENCES tasks(id),
  PRIMARY KEY (task_id, depends_on_task_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  task_id uuid REFERENCES tasks(id),
  kind varchar(64) NOT NULL,
  path text,
  content_hash varchar(128),
  metadata jsonb NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_workflow_id ON artifacts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_task_id ON artifacts(task_id);

CREATE TABLE IF NOT EXISTS agent_runs (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  task_id uuid REFERENCES tasks(id),
  agent_type varchar(64) NOT NULL,
  model varchar(128) NOT NULL,
  status varchar(64) NOT NULL,
  input jsonb NOT NULL,
  output jsonb,
  error text,
  started_at timestamptz NOT NULL,
  finished_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow_id ON agent_runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_task_id ON agent_runs(task_id);

CREATE TABLE IF NOT EXISTS review_results (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  task_id uuid NOT NULL REFERENCES tasks(id),
  decision varchar(64) NOT NULL,
  findings jsonb NOT NULL,
  required_fixes jsonb NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_review_results_workflow_id ON review_results(workflow_id);
CREATE INDEX IF NOT EXISTS idx_review_results_task_id ON review_results(task_id);

CREATE TABLE IF NOT EXISTS memory_records (
  id uuid PRIMARY KEY,
  workflow_id uuid REFERENCES workflows(id),
  scope varchar(64) NOT NULL,
  kind varchar(64) NOT NULL,
  content text NOT NULL,
  embedding_ref text,
  metadata jsonb NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_records_workflow_id ON memory_records(workflow_id);
CREATE INDEX IF NOT EXISTS idx_memory_records_scope ON memory_records(scope);

CREATE TABLE IF NOT EXISTS execution_history (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  task_id uuid REFERENCES tasks(id),
  event_type varchar(128) NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_history_workflow_id ON execution_history(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_task_id ON execution_history(task_id);

CREATE TABLE IF NOT EXISTS approval_gates (
  id uuid PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  gate_type varchar(64) NOT NULL,
  status varchar(64) NOT NULL,
  requested_action jsonb NOT NULL,
  decided_by text,
  decided_at timestamptz,
  created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_approval_gates_workflow_id ON approval_gates(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_gates_status ON approval_gates(status);
