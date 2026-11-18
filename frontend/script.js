/**
 * CampusBorrow — VIT Pune Campus Resource Lending & Tracking Portal
 * Frontend Client Controller
 */

const API_BASE = ""; // Relative path works seamlessly with Flask static serving & Nginx reverse proxy

let authToken = localStorage.getItem("campusborrow_token");
let currentUser = null;
let allResources = [];
let currentCategory = "all";
let searchDebounceTimer = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", async () => {
  setupDefaultDueDate();
  if (authToken) {
    await restoreSession();
  } else {
    showAuthView();
  }
});

function setupDefaultDueDate() {
  const dateInput = document.getElementById("modal-borrow-due-date");
  if (dateInput) {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 3); // 3 days default loan period
    defaultDate.setHours(17, 0, 0, 0); // 5:00 PM
    const localISO = new Date(defaultDate.getTime() - defaultDate.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
    dateInput.value = localISO;
    dateInput.min = new Date().toISOString().slice(0, 16);
  }
}

// -------------------------------------------------------------------
// Session & Auth Handling
// -------------------------------------------------------------------
async function restoreSession() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      showPortalView();
      await loadResources();
      await loadMyBorrows();
      if (currentUser.is_admin) {
        document.getElementById("nav-admin-btn").classList.remove("hidden");
      }
    } else {
      logout();
    }
  } catch (err) {
    console.error("Session restore failed:", err);
    logout();
  }
}

function showAuthView() {
  document.getElementById("auth-container").classList.remove("hidden");
  document.getElementById("portal-container").classList.add("hidden");
  document.getElementById("user-profile-bar").classList.add("hidden");
  document.getElementById("quick-demo-buttons").classList.remove("hidden");
}

function showPortalView() {
  document.getElementById("auth-container").classList.add("hidden");
  document.getElementById("portal-container").classList.remove("hidden");
  document.getElementById("quick-demo-buttons").classList.add("hidden");

  // User profile banner
  const profileBar = document.getElementById("user-profile-bar");
  const roleBadge = document.getElementById("user-role-badge");
  const nameEl = document.getElementById("user-display-name");
  const metaEl = document.getElementById("user-display-meta");

  profileBar.classList.remove("hidden");
  nameEl.textContent = currentUser.username;
  metaEl.textContent = `Roll: ${currentUser.roll_no || 'N/A'} • ${currentUser.department || 'AIDS'}`;

  if (currentUser.is_admin) {
    roleBadge.textContent = "Admin / Lab Coordinator";
    roleBadge.classList.add("admin-badge");
    document.getElementById("nav-admin-btn").classList.remove("hidden");
  } else {
    roleBadge.textContent = "Student";
    roleBadge.classList.remove("admin-badge");
    document.getElementById("nav-admin-btn").classList.add("hidden");
  }
}

function switchAuthTab(tab) {
  const loginPanel = document.getElementById("login-form-panel");
  const registerPanel = document.getElementById("register-form-panel");
  const loginTabBtn = document.getElementById("tab-login-btn");
  const regTabBtn = document.getElementById("tab-register-btn");

  if (tab === "login") {
    loginPanel.classList.remove("hidden");
    registerPanel.classList.add("hidden");
    loginTabBtn.classList.add("active");
    regTabBtn.classList.remove("active");
  } else {
    loginPanel.classList.add("hidden");
    registerPanel.classList.remove("hidden");
    loginTabBtn.classList.remove("active");
    regTabBtn.classList.add("active");
  }
}

function fillDemoCredentials(role) {
  switchAuthTab("login");
  const idInput = document.getElementById("login-identifier");
  const pwInput = document.getElementById("login-password");
  if (role === "student") {
    idInput.value = "student@vit.edu";
    pwInput.value = "Student@123";
    showToast("Filled demo student credentials (student@vit.edu)", "info");
  } else {
    idInput.value = "admin@vit.edu";
    pwInput.value = "Admin@123";
    showToast("Filled demo admin credentials (admin@vit.edu)", "info");
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const identifier = document.getElementById("login-identifier").value.trim();
  const password = document.getElementById("login-password").value;
  const submitBtn = document.getElementById("btn-login");

  submitBtn.disabled = true;
  submitBtn.textContent = "Signing In...";

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: identifier, password })
    });
    const data = await res.json();

    if (res.ok) {
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem("campusborrow_token", authToken);
      showToast(`Welcome back, ${currentUser.username}!`, "success");
      showPortalView();
      await loadResources();
      await loadMyBorrows();
    } else {
      showToast(data.error || "Login failed. Check credentials.", "error");
    }
  } catch (err) {
    showToast("Network error. Backend service unavailable.", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Sign In to CampusBorrow";
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById("reg-username").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const roll_no = document.getElementById("reg-rollno").value.trim();
  const department = document.getElementById("reg-department").value;
  const password = document.getElementById("reg-password").value;
  const submitBtn = document.getElementById("btn-register");

  submitBtn.disabled = true;
  submitBtn.textContent = "Creating Account...";

  try {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, roll_no, department, password })
    });
    const data = await res.json();

    if (res.ok) {
      showToast("Registration successful! Please sign in.", "success");
      switchAuthTab("login");
      document.getElementById("login-identifier").value = email;
      document.getElementById("login-password").value = password;
    } else {
      showToast(data.error || "Registration failed.", "error");
    }
  } catch (err) {
    showToast("Network error during registration.", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Register Account";
  }
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem("campusborrow_token");
  showToast("Logged out successfully.", "info");
  showAuthView();
}

// -------------------------------------------------------------------
// Portal Navigation Tabs
// -------------------------------------------------------------------
function switchPortalTab(tab) {
  document.getElementById("tab-catalog").classList.add("hidden");
  document.getElementById("tab-myborrows").classList.add("hidden");
  document.getElementById("tab-admin").classList.add("hidden");

  document.getElementById("nav-catalog-btn").classList.remove("active");
  document.getElementById("nav-myborrows-btn").classList.remove("active");
  document.getElementById("nav-admin-btn").classList.remove("active");

  if (tab === "catalog") {
    document.getElementById("tab-catalog").classList.remove("hidden");
    document.getElementById("nav-catalog-btn").classList.add("active");
    loadResources();
  } else if (tab === "myborrows") {
    document.getElementById("tab-myborrows").classList.remove("hidden");
    document.getElementById("nav-myborrows-btn").classList.add("active");
    loadMyBorrows();
  } else if (tab === "admin") {
    document.getElementById("tab-admin").classList.remove("hidden");
    document.getElementById("nav-admin-btn").classList.add("active");
    loadAdminData();
  }
}

// -------------------------------------------------------------------
// Campus Resource Catalog
// -------------------------------------------------------------------
function debounceSearch() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    loadResources();
  }, 250);
}

function filterByCategory(cat) {
  currentCategory = cat;
  const pills = document.querySelectorAll("#category-filter-group .filter-pill");
  pills.forEach(p => {
    if (p.textContent.trim().toLowerCase() === (cat === 'all' ? 'all resources' : cat.toLowerCase())) {
      p.classList.add("active");
    } else {
      p.classList.remove("active");
    }
  });
  loadResources();
}

async function loadResources() {
  const grid = document.getElementById("resources-grid");
  const search = document.getElementById("catalog-search-input").value.trim();

  let url = `${API_BASE}/api/resources?category=${encodeURIComponent(currentCategory)}`;
  if (search) {
    url += `&search=${encodeURIComponent(search)}`;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();
    allResources = data.resources || [];
    renderResourcesGrid(allResources);
  } catch (err) {
    grid.innerHTML = `<div class="text-center py-4 text-muted">Failed to load resources from server.</div>`;
  }
}

function renderResourcesGrid(resources) {
  const grid = document.getElementById("resources-grid");
  if (!resources || resources.length === 0) {
    grid.innerHTML = `<div class="text-center py-4 text-muted" style="grid-column: 1 / -1;">No campus resources match your filter criteria.</div>`;
    return;
  }

  grid.innerHTML = resources.map(item => {
    const inStock = item.available_quantity > 0 && item.status === 'available';
    let stockClass = "in-stock";
    let stockLabel = `Available: ${item.available_quantity} / ${item.total_quantity}`;

    if (item.status === 'maintenance') {
      stockClass = "out-of-stock";
      stockLabel = "Under Maintenance";
    } else if (item.available_quantity === 0) {
      stockClass = "out-of-stock";
      stockLabel = "Out of Stock (0 units)";
    } else if (item.available_quantity <= 2) {
      stockClass = "low-stock";
    }

    return `
      <div class="resource-card">
        <div>
          <div class="card-header-row">
            <h3 class="resource-title">${escapeHtml(item.name)}</h3>
            <span class="category-badge">${escapeHtml(item.category)}</span>
          </div>
          <p class="resource-desc">${escapeHtml(item.description || "Academic campus resource equipment.")}</p>
        </div>

        <div>
          <div class="resource-meta">
            <div class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
              <span>${escapeHtml(item.location)}</span>
            </div>
            <div class="stock-indicator">
              <span>Inventory Status</span>
              <span class="stock-pill ${stockClass}">${stockLabel}</span>
            </div>
          </div>

          <button 
            class="btn btn-primary btn-block" 
            ${!inStock ? "disabled" : ""}
            onclick="openBorrowModal(${item.id}, '${escapeHtml(item.name)}', ${item.available_quantity})"
          >
            ${inStock ? "Request Borrow" : "Currently Unavailable"}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// -------------------------------------------------------------------
// Student Borrow Request Modal & Flow
// -------------------------------------------------------------------
function openBorrowModal(id, name, available) {
  document.getElementById("modal-borrow-resource-id").value = id;
  document.getElementById("modal-borrow-resource-name").value = name;
  document.getElementById("modal-borrow-available").value = `${available} units ready`;

  const qtyInput = document.getElementById("modal-borrow-qty");
  qtyInput.value = 1;
  qtyInput.max = available;

  setupDefaultDueDate();
  document.getElementById("modal-request-borrow").classList.remove("hidden");
}

async function handleBorrowSubmit(e) {
  e.preventDefault();
  const resourceId = parseInt(document.getElementById("modal-borrow-resource-id").value);
  const quantity = parseInt(document.getElementById("modal-borrow-qty").value);
  const dueDateVal = document.getElementById("modal-borrow-due-date").value;
  const purpose = document.getElementById("modal-borrow-purpose").value.trim();
  const btn = document.getElementById("btn-submit-borrow");

  if (!dueDateVal) {
    showToast("Please specify an expected return date.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Submitting...";

  try {
    const res = await fetch(`${API_BASE}/api/borrows`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify({
        resource_id: resourceId,
        quantity,
        due_date: new Date(dueDateVal).toISOString(),
        purpose
      })
    });

    const data = await res.json();
    if (res.ok) {
      showToast("Borrow request submitted! Awaiting lab coordinator approval.", "success");
      closeModal("modal-request-borrow");
      await loadResources();
      await loadMyBorrows();
    } else {
      showToast(data.error || "Failed to submit request.", "error");
    }
  } catch (err) {
    showToast("Network error submitting borrow request.", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit Borrow Request";
  }
}

// -------------------------------------------------------------------
// My Borrowings Table
// -------------------------------------------------------------------
async function loadMyBorrows() {
  if (!authToken) return;
  const tbody = document.getElementById("my-borrows-table-body");
  const countBadge = document.getElementById("my-borrows-count-badge");

  try {
    const res = await fetch(`${API_BASE}/api/borrows/my`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const data = await res.json();
    const borrows = data.borrows || [];

    const activeBorrows = borrows.filter(b => ["pending", "approved", "overdue"].includes(b.status));
    countBadge.textContent = activeBorrows.length;

    if (borrows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">You have not submitted any resource borrowing requests yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = borrows.map(b => {
      const statusBadge = getStatusBadgeHtml(b.status);
      const canReturn = ["approved", "overdue"].includes(b.status);

      return `
        <tr>
          <td><strong>#${b.id}</strong></td>
          <td><strong>${escapeHtml(b.resource ? b.resource.name : 'Unknown')}</strong></td>
          <td>
            <span class="category-badge">${escapeHtml(b.resource ? b.resource.category : 'General')}</span>
            <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(b.resource ? b.resource.location : '')}</div>
          </td>
          <td><strong>${b.quantity}</strong></td>
          <td>${escapeHtml(b.purpose || "Academic project")}</td>
          <td>${formatDate(b.due_date)}</td>
          <td>${statusBadge}</td>
          <td>
            ${canReturn ? `
              <button class="btn btn-sm btn-success" onclick="returnItem(${b.id})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                Return Item
              </button>
            ` : `<span class="text-muted">—</span>`}
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">Error loading borrowing records.</td></tr>`;
  }
}

async function returnItem(borrowId) {
  if (!confirm("Confirm returning this borrowed equipment to the campus lab?")) return;

  try {
    const res = await fetch(`${API_BASE}/api/borrows/${borrowId}/return`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Equipment marked as returned. Inventory stock restored!", "success");
      await loadMyBorrows();
      await loadResources();
      if (currentUser && currentUser.is_admin) {
        await loadAdminData();
      }
    } else {
      showToast(data.error || "Failed to mark item returned.", "error");
    }
  } catch (err) {
    showToast("Network error returning item.", "error");
  }
}

// -------------------------------------------------------------------
// Admin Console & Lending Queue
// -------------------------------------------------------------------
async function loadAdminData() {
  if (!authToken || !currentUser || !currentUser.is_admin) return;

  try {
    // 1. Fetch Borrows & Stats
    const borrowsRes = await fetch(`${API_BASE}/api/borrows`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const borrowsData = await borrowsRes.json();
    const stats = borrowsData.stats || {};

    document.getElementById("kpi-total-equipment").textContent = stats.total_stock || 0;
    document.getElementById("kpi-available-stock").textContent = stats.available_stock || 0;
    document.getElementById("kpi-pending-requests").textContent = stats.pending_approvals || 0;
    document.getElementById("kpi-overdue-returns").textContent = stats.overdue_items || 0;

    renderAdminBorrowsQueue(borrowsData.borrows || []);

    // 2. Fetch Resources for Inventory Panel
    const resRes = await fetch(`${API_BASE}/api/resources`);
    const resData = await resRes.json();
    renderAdminInventory(resData.resources || []);
  } catch (err) {
    console.error("Admin data load error:", err);
    showToast("Failed to load admin dashboard data.", "error");
  }
}

function renderAdminBorrowsQueue(borrows) {
  const tbody = document.getElementById("admin-borrows-table-body");
  if (!borrows || borrows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No student borrowing requests found.</td></tr>`;
    return;
  }

  tbody.innerHTML = borrows.map(b => {
    const statusBadge = getStatusBadgeHtml(b.status);
    const isPending = b.status === "pending";
    const canReturn = ["approved", "overdue"].includes(b.status);

    return `
      <tr>
        <td><strong>#${b.id}</strong></td>
        <td>
          <strong>${escapeHtml(b.user ? b.user.username : 'Unknown')}</strong>
          <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(b.user ? b.user.email : '')}</div>
        </td>
        <td>${escapeHtml(b.user ? b.user.roll_no || '—' : '')} / ${escapeHtml(b.user ? b.user.department || 'AIDS' : '')}</td>
        <td><strong>${escapeHtml(b.resource ? b.resource.name : 'Unknown')}</strong></td>
        <td><strong>${b.quantity}</strong></td>
        <td>${escapeHtml(b.purpose || "—")}</td>
        <td>${formatDate(b.due_date)}</td>
        <td>${statusBadge}</td>
        <td>
          <div class="action-group">
            ${isPending ? `
              <button class="btn btn-sm btn-success" onclick="approveBorrow(${b.id})">Approve</button>
              <button class="btn btn-sm btn-outline-danger" onclick="openRejectModal(${b.id})">Reject</button>
            ` : ""}
            ${canReturn ? `
              <button class="btn btn-sm btn-outline" onclick="returnItem(${b.id})">Mark Returned</button>
            ` : ""}
            ${!isPending && !canReturn ? `<span class="text-muted">Completed</span>` : ""}
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function renderAdminInventory(resources) {
  const tbody = document.getElementById("admin-inventory-table-body");
  if (!resources || resources.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No resources in inventory.</td></tr>`;
    return;
  }

  tbody.innerHTML = resources.map(r => {
    return `
      <tr>
        <td>#${r.id}</td>
        <td><strong>${escapeHtml(r.name)}</strong></td>
        <td><span class="category-badge">${escapeHtml(r.category)}</span></td>
        <td>${escapeHtml(r.location)}</td>
        <td>${r.total_quantity}</td>
        <td><strong>${r.available_quantity}</strong></td>
        <td>
          <select class="form-control" style="padding:0.25rem 0.5rem; font-size:0.8rem;" onchange="updateResourceStatus(${r.id}, this.value)">
            <option value="available" ${r.status === 'available' ? 'selected' : ''}>Available</option>
            <option value="maintenance" ${r.status === 'maintenance' ? 'selected' : ''}>Maintenance</option>
            <option value="unavailable" ${r.status === 'unavailable' ? 'selected' : ''}>Unavailable</option>
          </select>
        </td>
        <td>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteResource(${r.id}, '${escapeHtml(r.name)}')">Delete</button>
        </td>
      </tr>
    `;
  }).join("");
}

async function approveBorrow(borrowId) {
  try {
    const res = await fetch(`${API_BASE}/api/borrows/${borrowId}/approve`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Borrow request approved & inventory stock decremented!", "success");
      await loadAdminData();
      await loadResources();
    } else {
      showToast(data.error || "Approval failed.", "error");
    }
  } catch (err) {
    showToast("Network error approving request.", "error");
  }
}

function openRejectModal(borrowId) {
  document.getElementById("modal-reject-borrow-id").value = borrowId;
  document.getElementById("modal-reject-remarks-text").value = "";
  document.getElementById("modal-reject-remarks").classList.remove("hidden");
}

async function handleRejectSubmit(e) {
  e.preventDefault();
  const borrowId = document.getElementById("modal-reject-borrow-id").value;
  const remarks = document.getElementById("modal-reject-remarks-text").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/borrows/${borrowId}/reject`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify({ admin_remarks: remarks })
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Borrow request rejected.", "info");
      closeModal("modal-reject-remarks");
      await loadAdminData();
    } else {
      showToast(data.error || "Failed to reject request.", "error");
    }
  } catch (err) {
    showToast("Network error rejecting request.", "error");
  }
}

function openAddResourceModal() {
  document.getElementById("modal-add-resource").classList.remove("hidden");
}

async function handleAddResourceSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("modal-res-name").value.trim();
  const category = document.getElementById("modal-res-category").value;
  const location = document.getElementById("modal-res-location").value.trim();
  const description = document.getElementById("modal-res-desc").value.trim();
  const total_quantity = parseInt(document.getElementById("modal-res-total").value);
  const status = document.getElementById("modal-res-status").value;

  try {
    const res = await fetch(`${API_BASE}/api/resources`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify({
        name,
        category,
        location,
        description,
        total_quantity,
        available_quantity: total_quantity,
        status
      })
    });
    const data = await res.json();
    if (res.ok) {
      showToast("New campus resource added successfully!", "success");
      closeModal("modal-add-resource");
      await loadAdminData();
      await loadResources();
    } else {
      showToast(data.error || "Failed to add resource.", "error");
    }
  } catch (err) {
    showToast("Network error adding resource.", "error");
  }
}

async function updateResourceStatus(resourceId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/api/resources/${resourceId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast("Resource status updated.", "success");
      await loadAdminData();
      await loadResources();
    } else {
      const data = await res.json();
      showToast(data.error || "Failed to update resource.", "error");
    }
  } catch (err) {
    showToast("Network error updating status.", "error");
  }
}

async function deleteResource(resourceId, name) {
  if (!confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/resources/${resourceId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Resource "${name}" deleted.`, "success");
      await loadAdminData();
      await loadResources();
    } else {
      showToast(data.error || "Failed to delete resource.", "error");
    }
  } catch (err) {
    showToast("Network error deleting resource.", "error");
  }
}

// -------------------------------------------------------------------
// Helper Utilities & Formatting
// -------------------------------------------------------------------
function closeModal(modalId) {
  document.getElementById(modalId).classList.add("hidden");
}

function getStatusBadgeHtml(status) {
  const norm = (status || "").toLowerCase();
  switch (norm) {
    case "pending":
      return `<span class="badge-status badge-pending">Pending</span>`;
    case "approved":
      return `<span class="badge-status badge-approved">Approved</span>`;
    case "overdue":
      return `<span class="badge-status badge-overdue"> Overdue</span>`;
    case "returned":
      return `<span class="badge-status badge-returned">Returned</span>`;
    case "rejected":
      return `<span class="badge-status badge-rejected">Rejected</span>`;
    default:
      return `<span class="badge-status">${escapeHtml(status)}</span>`;
  }
}

function formatDate(isoStr) {
  if (!isoStr) return "—";
  try {
    const dt = new Date(isoStr);
    return dt.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return isoStr;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(msg, type = "info") {
  const toast = document.getElementById("global-toast");
  const body = document.getElementById("toast-message");

  body.className = `toast-body toast-${type}`;
  body.textContent = msg;

  toast.classList.remove("hidden");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}
