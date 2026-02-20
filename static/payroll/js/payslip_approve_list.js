setupSelectAll("selectAll", ".payslip-checkbox");

setupTableSearch({
    searchInputId: "searchPending",
    tableId: "pendingTable",
    rowSelector: ".payslip-row",
    cellSelectors: [".employee-name", ".staff-id", ".month-year"],
    countElementId: "pendingCount",
    noResultsRowId: "noResultsRow",
    colspan: 7
});

setupTableSearch({
    searchInputId: "searchRecent",
    tableId: "recentTable",
    rowSelector: ".recent-row",
    cellSelectors: [".employee-name", ".month-year", ".status-cell"],
    countElementId: "recentCount",
    noResultsRowId: "noRecentResultsRow",
    colspan: 6
});

const bulkApproveForm = document.getElementById("bulkApproveForm");
if (bulkApproveForm) {
    bulkApproveForm.addEventListener("submit", function (event) {
        const selected = document.querySelectorAll(".payslip-checkbox:checked");
        if (selected.length === 0) {
            event.preventDefault();
            alert("Please select at least one payslip before clicking Approve Selected.");
            return;
        }

        const confirmed = confirm(`Approve ${selected.length} selected payslip(s)?`);
        if (!confirmed) {
            event.preventDefault();
        }
    });
}
