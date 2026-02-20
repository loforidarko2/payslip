function setupSelectAll(selectAllId, checkboxSelector) {
    const selectAll = document.getElementById(selectAllId);
    if (!selectAll) {
        return;
    }
    selectAll.addEventListener("change", function () {
        const checkboxes = document.querySelectorAll(checkboxSelector);
        checkboxes.forEach((checkbox) => {
            checkbox.checked = this.checked;
        });
    });
}

function setupTableSearch(config) {
    const searchInput = document.getElementById(config.searchInputId);
    const table = document.getElementById(config.tableId);
    const countElement = document.getElementById(config.countElementId);
    if (!searchInput || !table || !countElement) {
        return;
    }

    const rows = table.querySelectorAll(config.rowSelector);
    searchInput.addEventListener("input", function () {
        const searchTerm = this.value.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach((row) => {
            const matches = config.cellSelectors.some((selector) => {
                const cell = row.querySelector(selector);
                return cell && cell.textContent.toLowerCase().includes(searchTerm);
            });

            if (matches) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        countElement.textContent = visibleCount;

        const noResultsRow = table.querySelector(`#${config.noResultsRowId}`);
        if (visibleCount === 0 && searchTerm !== "") {
            const messageHtml = `<i class="bi bi-search"></i> No results found for "${searchTerm}"`;
            if (!noResultsRow) {
                const tbody = table.querySelector("tbody");
                const tr = document.createElement("tr");
                tr.id = config.noResultsRowId;
                tr.innerHTML = `<td colspan="${config.colspan}" class="text-center py-4 text-muted">${messageHtml}</td>`;
                tbody.appendChild(tr);
            } else {
                noResultsRow.querySelector("td").innerHTML = messageHtml;
                noResultsRow.style.display = "";
            }
        } else if (noResultsRow) {
            noResultsRow.style.display = "none";
        }
    });
}
