$(document).ready(function () {
    // Initialize Select2 on the employee dropdown
    $("#id_employee").select2({
        theme: "bootstrap-5",
        width: "100%",
        placeholder: "Search for an employee...",
        allowClear: true
    });

    // Load employee data
    const detailsData = JSON.parse(document.getElementById("employee-details-data").textContent);
    const salaryData = JSON.parse(document.getElementById("employee-salaries-data").textContent);
    const salaryInput = $("#id_basic_salary");

    // Monitor changes on the employee dropdown
    $("#id_employee").on("change", function () {
        const employeeId = $(this).val();

        // Autofill salary
        if (employeeId && salaryData[employeeId]) {
            const salary = salaryData[employeeId];
            salaryInput.val(salary.toFixed(2));
        } else {
            salaryInput.val("");
        }

        // Autofill details (Department, Unit, Grade, Level)
        if (employeeId && detailsData[employeeId]) {
            $("#id_department").val(detailsData[employeeId].department || "");
            $("#id_unit").val(detailsData[employeeId].unit || "");
            $("#id_grade").val(detailsData[employeeId].grade || "");
            $("#id_level").val(detailsData[employeeId].level || "");
        } else {
            $("#id_department").val("");
            $("#id_unit").val("");
            $("#id_grade").val("");
            $("#id_level").val("");
        }
    });
});
