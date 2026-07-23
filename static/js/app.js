function syncLinkFields(scope) {
  const select = scope.querySelector("[data-progress-stage]");
  const links = scope.querySelector("[data-link-fields]");
  if (!select || !links) return;
  const visibleStages = ["registered", "campaign_set", "spent"];
  links.hidden = !visibleStages.includes(select.value);
}

function syncStaffByManager(scope) {
  const managerSelect = scope.querySelector("[data-manager-staff-filter]");
  const staffSelect = scope.querySelector("[data-staff-filter-target]");
  if (!managerSelect || !staffSelect) return;
  const managerId = managerSelect.value;
  Array.from(staffSelect.options).forEach((option) => {
    if (!option.value) {
      option.hidden = false;
      return;
    }
    option.hidden = Boolean(managerId) && option.dataset.managerId !== managerId;
  });
  const selected = staffSelect.selectedOptions[0];
  if (selected && selected.hidden) staffSelect.value = "";
}

document.addEventListener("click", (event) => {
  const bulkOpener = event.target.closest("[data-open-bulk-modal]");
  if (bulkOpener) {
    const selected = getSelectedProjectIds();
    if (!selected.length) {
      alert("Vui lòng chọn ít nhất một dự án.");
      return;
    }
    const modal = document.getElementById("bulk-project-modal");
    const input = modal.querySelector("[data-bulk-project-ids]");
    input.value = selected.join(",");
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    syncStaffByManager(modal);
    syncSelectedProjectCount();
    return;
  }

  const opener = event.target.closest("[data-open-modal]");
  if (opener) {
    const modal = document.getElementById(opener.dataset.openModal);
    if (modal) {
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      syncLinkFields(modal);
      syncStaffByManager(modal);
    }
  }

  if (event.target.matches("[data-close-modal]") || event.target.classList.contains("modal-backdrop")) {
    const modal = event.target.closest(".modal-backdrop");
    if (modal) {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
    }
  }
});

document.addEventListener("change", (event) => {
  if (event.target.matches("[data-progress-stage]")) {
    syncLinkFields(event.target.closest("form"));
  }

  if (event.target.matches("[data-manager-staff-filter]")) {
    syncStaffByManager(event.target.closest("form"));
  }

  if (event.target.matches("[data-select-all-projects]")) {
    document.querySelectorAll(".project-select").forEach((checkbox) => {
      checkbox.checked = event.target.checked;
    });
    syncSelectedProjectCount();
  }

  if (event.target.matches(".project-select")) {
    syncSelectedProjectCount();
  }

  if (event.target.matches("[data-select-all-tasks]")) {
    document.querySelectorAll(".task-select").forEach((checkbox) => {
      checkbox.checked = event.target.checked;
    });
    syncBulkDeleteIds("task");
  }

  if (event.target.matches(".task-select")) syncBulkDeleteIds("task");
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll(".modal-backdrop.is-open").forEach((modal) => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
    });
  }
});

document.querySelectorAll(".project-update-form").forEach(syncLinkFields);

function getSelectedProjectIds() {
  return Array.from(document.querySelectorAll(".project-select:checked")).map((checkbox) => checkbox.value);
}

function syncSelectedProjectCount() {
  const count = getSelectedProjectIds().length;
  document.querySelectorAll("[data-selected-count]").forEach((node) => {
    node.textContent = count;
  });
  const hidden = document.querySelector("[data-bulk-project-ids]");
  if (hidden) hidden.value = getSelectedProjectIds().join(",");
  syncBulkDeleteIds("project");
}

function syncBulkDeleteIds(type) {
  const values = Array.from(document.querySelectorAll(`.${type}-select:checked`)).map((item) => item.value);
  const hidden = document.querySelector(`[data-bulk-delete-ids="${type}"]`);
  if (hidden) hidden.value = values.join(",");
}

document.querySelectorAll("[data-bulk-delete-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const type = form.dataset.bulkDeleteForm;
    syncBulkDeleteIds(type);
    if (!form.querySelector(`[data-bulk-delete-ids="${type}"]`).value) {
      event.preventDefault();
      alert("Vui lòng chọn ít nhất một mục để xóa.");
    }
  });
});

syncSelectedProjectCount();
