const state = {
  users: [],
};

const userName = (id) => state.users.find((user) => user.id === id)?.name ?? `User ${id}`;
const money = (value) => `€${Number(value).toFixed(2)}`;

function formatApiError(detail) {
  if (detail == null) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : JSON.stringify(item)))
      .join("; ");
  }
  if (typeof detail === "object") return JSON.stringify(detail);
  return String(detail);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(formatApiError(error.detail) || "Request failed");
  }

  return response.json();
}

async function init() {
  state.users = await api("/api/users");
  renderUsers();
  await refresh();
}

function renderUsers() {
  const currentId = document.querySelector("#currentUser")?.value;
  const paidId = document.querySelector("#paidBy")?.value;
  const selects = [document.querySelector("#currentUser"), document.querySelector("#paidBy")];
  for (const select of selects) {
    select.innerHTML = state.users.map((user) => `<option value="${user.id}">${user.name}</option>`).join("");
  }
  if (currentId) document.querySelector("#currentUser").value = currentId;
  if (paidId) document.querySelector("#paidBy").value = paidId;

  document.querySelector("#splitBetween").innerHTML = state.users
    .map(
      (user) => `
        <label class="form-check">
          <input class="form-check-input split-user" type="checkbox" value="${user.id}" checked>
          <span class="form-check-label">${user.name}</span>
        </label>
      `
    )
    .join("");
}

function setSyncStatus(message) {
  const el = document.querySelector("#syncStatus");
  if (el) el.textContent = message;
}

async function refresh() {
  setSyncStatus("Updating…");
  try {
    const [ledger, expenses, bills] = await Promise.all([
      api("/api/ledger"),
      api("/api/expenses"),
      api("/api/recurring-bills"),
    ]);

    renderLedger(ledger);
    renderExpenses(expenses);
    renderBills(bills);
    setSyncStatus(`Updated ${new Date().toLocaleTimeString()}`);
  } catch (error) {
    setSyncStatus("");
    throw error;
  }
}

function renderLedger(items) {
  const root = document.querySelector("#ledger");
  if (!items.length) {
    root.innerHTML = `<div class="text-muted">No debts. Balanced.</div>`;
    return;
  }

  root.innerHTML = items
    .map(
      (item) => `
        <div class="list-group-item d-flex justify-content-between align-items-center">
          <span>${item.from_user_name} owes ${item.to_user_name}</span>
          <span class="money">${money(item.amount)}</span>
        </div>
      `
    )
    .join("");
}

function renderExpenses(items) {
  const root = document.querySelector("#expenses");
  if (!items.length) {
    root.innerHTML = `<div class="text-muted">No expenses yet.</div>`;
    return;
  }

  root.innerHTML = `
    <table class="table align-middle">
      <thead>
        <tr>
          <th>Title</th>
          <th>Paid by</th>
          <th>Split</th>
          <th class="text-end">Amount</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map(
            (expense) => `
              <tr>
                <td>${expense.title}<div class="small text-muted">${expense.category}</div></td>
                <td>${userName(expense.paid_by_user_id)}</td>
                <td>${expense.split_between_user_ids.map(userName).join(", ")}</td>
                <td class="text-end money">${money(expense.amount)}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderBills(items) {
  const root = document.querySelector("#bills");
  if (!items.length) {
    root.innerHTML = `<div class="text-muted">No recurring bills yet.</div>`;
    return;
  }

  root.innerHTML = `
    <table class="table align-middle">
      <thead>
        <tr>
          <th>Title</th>
          <th>Due</th>
          <th class="text-end">Amount</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map(
            (bill) => `
              <tr>
                <td>${bill.title}<div class="small text-muted">${bill.category}</div></td>
                <td>${bill.due_date}</td>
                <td class="text-end money">${money(bill.amount)}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

document.querySelector("#expenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const splitIds = [...document.querySelectorAll(".split-user:checked")].map((input) => Number(input.value));
  if (!splitIds.length) {
    alert("Select at least one person to split with.");
    return;
  }

  const paidBy = Number(document.querySelector("#paidBy").value);
  if (!splitIds.includes(paidBy)) {
    alert("Include the payer in the split (check their box).");
    return;
  }

  const submitBtn = event.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  try {
    await api("/api/expenses", {
      method: "POST",
      body: JSON.stringify({
        title: document.querySelector("#title").value,
        amount: document.querySelector("#amount").value,
        category: document.querySelector("#category").value,
        paid_by_user_id: paidBy,
        split_between_user_ids: splitIds,
      }),
    });

    event.target.reset();
    document.querySelectorAll(".split-user").forEach((input) => {
      input.checked = true;
    });
    await refresh();
  } catch (error) {
    alert(error.message);
  } finally {
    submitBtn.disabled = false;
  }
});

document.querySelector("#billForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const submitBtn = event.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  try {
    await api("/api/recurring-bills", {
      method: "POST",
      body: JSON.stringify({
        title: document.querySelector("#billTitle").value,
        amount: document.querySelector("#billAmount").value,
        category: document.querySelector("#billCategory").value,
        due_date: document.querySelector("#billDueDate").value,
        paid_by_user_id: null,
      }),
    });

    event.target.reset();
    await refresh();
  } catch (error) {
    alert(error.message);
  } finally {
    submitBtn.disabled = false;
  }
});

document.querySelector("#currentUser")?.addEventListener("change", (event) => {
  const id = event.target.value;
  const paidBy = document.querySelector("#paidBy");
  if (paidBy && id) paidBy.value = id;
});

init().catch((error) => {
  console.error(error);
  alert(error.message);
});
