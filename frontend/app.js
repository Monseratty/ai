const state = {
  apiBase: normalizeApiBase(localStorage.getItem("aio.apiBase") || "http://127.0.0.1:8000"),
  apiToken: localStorage.getItem("aio.apiToken") || "",
  workflows: [],
  selectedWorkflowId: null,
  selectedSnapshot: null,
  events: [],
  artifacts: [],
  approvals: [],
  live: false,
};

const seed = {
  workflows: [
    {
      id: "seed-workflow-1",
      status: "in_progress",
      user_task: "[Demo] Add audit-safe pull request reporting with reviewer validation",
    },
    {
      id: "seed-workflow-2",
      status: "planned",
      user_task: "[Demo] Refactor sandbox execution policies for typed tool grants",
    },
  ],
  tasks: [
    {
      id: "task-1",
      kind: "coding",
      status: "succeeded",
      title: "[Demo] Code audit-safe PR reporting",
      description: "Demo-only task. Connect to the live API to see tasks generated from your request.",
      dependency_ids: [],
    },
    {
      id: "task-2",
      kind: "testing",
      status: "running",
      title: "[Demo] Test PR reporting workflow",
      description: "Demo-only task. Live workflows use your prompt in task titles and descriptions.",
      dependency_ids: ["task-1"],
    },
    {
      id: "task-3",
      kind: "review",
      status: "blocked",
      title: "[Demo] Reviewer gate",
      description: "Demo-only reviewer check for architecture, security, imports, and coverage.",
      dependency_ids: ["task-2"],
    },
  ],
  events: [
    { id: "e1", event_type: "workflow.created", payload: { source: "console" } },
    { id: "e2", event_type: "workflow.planned", payload: { task_count: 3 } },
    { id: "e3", event_type: "task.approved", payload: { reviewer: "approved" } },
  ],
  approvals: [
    {
      id: "approval-1",
      gate_type: "pull_request",
      status: "pending",
      requested_action: { branch: "codex/audit-safe-pr-reporting" },
      decided_by: null,
    },
  ],
};

const qs = (selector) => document.querySelector(selector);

function normalizeApiBase(value) {
  const trimmed = String(value || "").trim().replace(/\/$/, "");
  if (!trimmed) return "http://127.0.0.1:8000";
  return trimmed
    .replace("http://127.0.1:", "http://127.0.0.1:")
    .replace("https://127.0.1:", "https://127.0.0.1:");
}

function headers() {
  const value = { "content-type": "application/json" };
  if (state.apiToken.trim()) {
    value.Authorization = `Bearer ${state.apiToken.trim()}`;
  }
  return value;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${state.apiBase}${path}`, {
      ...options,
      headers: { ...headers(), ...(options.headers || {}) },
    });
  } catch (error) {
    throw new Error(
      `Cannot reach API at ${state.apiBase}. Check API base is exactly http://127.0.0.1:8000, backend is running, and the UI is opened from http://127.0.0.1:4173.`,
    );
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  return response.json();
}

function toast(message) {
  const node = qs("#toast");
  node.textContent = message;
  node.classList.add("visible");
  window.setTimeout(() => node.classList.remove("visible"), 2600);
}

function pill(status) {
  return `<span class="status-pill ${status}">${status}</span>`;
}

function renderMetrics() {
  const tasks = state.selectedSnapshot?.tasks || seed.tasks;
  qs("#metricWorkflows").textContent = state.workflows.length;
  qs("#metricQueued").textContent = tasks.filter((task) =>
    ["queued", "running", "pending"].includes(task.status),
  ).length;
  qs("#metricBlocked").textContent = tasks.filter((task) =>
    ["blocked", "requires_fixes", "failed"].includes(task.status),
  ).length;
  qs("#metricApprovals").textContent = state.approvals.length;
  qs("#runtimeMode").textContent = state.live ? "Live API" : "Demo seed";
}

function renderWorkflows() {
  const list = qs("#workflowList");
  list.innerHTML = "";
  for (const workflow of state.workflows) {
    const item = document.createElement("article");
    item.className = `workflow-item ${workflow.id === state.selectedWorkflowId ? "selected" : ""}`;
    item.innerHTML = `
      <div class="row">
        <strong>${escapeHtml(workflow.user_task)}</strong>
        ${pill(workflow.status)}
      </div>
      <div class="meta">${workflow.id}</div>
    `;
    item.addEventListener("click", () => selectWorkflow(workflow.id));
    list.appendChild(item);
  }
}

function renderSelectedWorkflow() {
  const snapshot = state.selectedSnapshot;
  const workflow = snapshot?.workflow || state.workflows.find((item) => item.id === state.selectedWorkflowId);
  qs("#selectedWorkflowHint").textContent = workflow
    ? workflow.user_task
    : "Select a workflow to inspect tasks and execution state.";
  qs("#selectedStatus").textContent = workflow?.status || "idle";
  qs("#selectedStatus").className = `status-pill ${workflow?.status || ""}`;

  const board = qs("#taskBoard");
  board.innerHTML = "";
  const tasks = snapshot?.tasks || seed.tasks;
  for (const task of tasks) {
    const node = document.createElement("article");
    node.className = `task-item ${task.status}`;
    node.innerHTML = `
      <div class="row">
        <span class="task-kind">${task.kind}</span>
        ${pill(task.status)}
      </div>
      <strong>${escapeHtml(task.title)}</strong>
      <p>${escapeHtml(task.description)}</p>
      <div class="meta">${state.live ? "generated from your workflow request" : "demo data, not your workflow"}</div>
      <div class="meta">deps: ${task.dependency_ids?.length ? task.dependency_ids.join(", ") : "none"}</div>
      <div class="row">
        <button class="btn" data-action="execute" data-task-id="${task.id}">Execute</button>
        <button class="btn" data-action="retry" data-task-id="${task.id}">Retry</button>
      </div>
    `;
    board.appendChild(node);
  }
}

function renderTimeline() {
  const timeline = qs("#eventTimeline");
  timeline.innerHTML = "";
  for (const event of state.events) {
    const item = document.createElement("article");
    item.className = "timeline-item";
    item.innerHTML = `
      <strong>${escapeHtml(event.event_type)}</strong>
      <pre class="meta">${escapeHtml(JSON.stringify(event.payload || {}, null, 2))}</pre>
    `;
    timeline.appendChild(item);
  }
}

function renderApprovals() {
  const list = qs("#approvalList");
  list.innerHTML = "";
  if (!state.approvals.length) {
    list.innerHTML = `<p>No approval gates for this workflow.</p>`;
    return;
  }
  for (const approval of state.approvals) {
    const item = document.createElement("article");
    item.className = "approval-item";
    item.innerHTML = `
      <div class="row">
        <strong>${escapeHtml(approval.gate_type)}</strong>
        ${pill(approval.status)}
      </div>
      <pre class="meta">${escapeHtml(JSON.stringify(approval.requested_action || {}, null, 2))}</pre>
      <div class="row">
        <button class="btn primary" data-action="approve" data-approval-id="${approval.id}">Approve</button>
        <button class="btn" data-action="reject" data-approval-id="${approval.id}">Reject</button>
      </div>
    `;
    list.appendChild(item);
  }
}

function renderAll() {
  renderMetrics();
  renderWorkflows();
  renderSelectedWorkflow();
  renderTimeline();
  renderApprovals();
}

async function refresh() {
  try {
    state.workflows = await request("/workflows");
    state.live = true;
    if (!state.selectedWorkflowId && state.workflows[0]) {
      state.selectedWorkflowId = state.workflows[0].id;
    }
    if (state.selectedWorkflowId) {
      await loadWorkflowDetails(state.selectedWorkflowId);
    }
    toast("Connected to live API.");
  } catch (error) {
    state.live = false;
    state.workflows = [...seed.workflows];
    state.selectedWorkflowId ||= seed.workflows[0].id;
    state.selectedSnapshot = { workflow: seed.workflows[0], tasks: seed.tasks };
    state.events = [...seed.events];
    state.approvals = [...seed.approvals];
    toast(`Using demo seed. ${error.message}`);
  }
  renderAll();
}

async function loadWorkflowDetails(workflowId) {
  if (!state.live) {
    state.selectedSnapshot = {
      workflow: seed.workflows.find((workflow) => workflow.id === workflowId) || seed.workflows[0],
      tasks: seed.tasks,
    };
    state.events = [...seed.events];
    state.approvals = [...seed.approvals];
    return;
  }
  state.selectedSnapshot = await request(`/workflows/${workflowId}`);
  state.events = await request(`/workflows/${workflowId}/history`);
  state.approvals = await request(`/approvals/workflow/${workflowId}`);
}

async function selectWorkflow(workflowId) {
  state.selectedWorkflowId = workflowId;
  await loadWorkflowDetails(workflowId);
  renderAll();
}

async function createWorkflow(event) {
  event.preventDefault();
  const userTask = qs("#userTask").value.trim();
  if (!userTask) {
    toast("Write a user task first.");
    return;
  }
  try {
    const workflow = await request("/workflows", {
      method: "POST",
      body: JSON.stringify({ user_task: userTask }),
    });
    state.live = true;
    state.selectedWorkflowId = workflow.id;
    qs("#userTask").value = "";
    await refresh();
    toast("Workflow created.");
  } catch (error) {
    toast(`Create failed: ${error.message}`);
  }
}

async function taskAction(event) {
  const button = event.target.closest("button[data-task-id]");
  if (!button || !state.live) return;
  const taskId = button.dataset.taskId;
  const action = button.dataset.action;
  const path =
    action === "retry" ? `/workflows/tasks/${taskId}/retry` : `/workflows/tasks/${taskId}/execute`;
  try {
    await request(path, { method: "POST", body: "{}" });
    await loadWorkflowDetails(state.selectedWorkflowId);
    renderAll();
    toast(`Task ${action} completed.`);
  } catch (error) {
    toast(`Task ${action} failed: ${error.message}`);
  }
}

async function approvalAction(event) {
  const button = event.target.closest("button[data-approval-id]");
  if (!button || !state.live) return;
  const approvalId = button.dataset.approvalId;
  const action = button.dataset.action;
  try {
    await request(`/approvals/${approvalId}/${action}`, {
      method: "POST",
      body: JSON.stringify({ decided_by: "operator-console" }),
    });
    await loadWorkflowDetails(state.selectedWorkflowId);
    renderAll();
    toast(`Approval ${action}d.`);
  } catch (error) {
    toast(`Approval failed: ${error.message}`);
  }
}

async function readPullRequestStatus(event) {
  event.preventDefault();
  const number = qs("#prNumber").value.trim();
  if (!number) {
    toast("Enter a PR number.");
    return;
  }
  try {
    const status = await request(`/pull-requests/${number}`);
    qs("#prStatusOutput").textContent = JSON.stringify(status, null, 2);
  } catch (error) {
    qs("#prStatusOutput").textContent = error.message;
  }
}

async function reportCheckRun(event) {
  event.preventDefault();
  const headSha = qs("#headSha").value.trim();
  if (!headSha) {
    toast("Enter a head SHA.");
    return;
  }
  try {
    const result = await request("/pull-requests/check-runs", {
      method: "POST",
      body: JSON.stringify({
        name: "AI Orchestrator",
        head_sha: headSha,
        status: "completed",
        conclusion: "success",
        summary: qs("#checkSummary").value.trim() || "Workflow completed.",
      }),
    });
    toast(`Check run reported: ${result.provider_id}`);
  } catch (error) {
    toast(`Check run failed: ${error.message}`);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

qs("#apiBase").value = state.apiBase;
localStorage.setItem("aio.apiBase", state.apiBase);
qs("#apiToken").value = state.apiToken;
qs("#connectionForm").addEventListener("submit", (event) => {
  event.preventDefault();
  state.apiBase = normalizeApiBase(qs("#apiBase").value);
  qs("#apiBase").value = state.apiBase;
  state.apiToken = qs("#apiToken").value;
  localStorage.setItem("aio.apiBase", state.apiBase);
  localStorage.setItem("aio.apiToken", state.apiToken);
  refresh();
});
qs("#workflowForm").addEventListener("submit", createWorkflow);
qs("#refreshButton").addEventListener("click", refresh);
qs("#taskBoard").addEventListener("click", taskAction);
qs("#approvalList").addEventListener("click", approvalAction);
qs("#prStatusForm").addEventListener("submit", readPullRequestStatus);
qs("#checkRunForm").addEventListener("submit", reportCheckRun);

refresh();
