// =====================================================
// MEDIFIND - MAIN JAVASCRIPT
// Common functionality used throughout the application
// =====================================================


// -----------------------------------------------------
// Show a simple message
// -----------------------------------------------------

function showMessage(message, type = "info") {

    alert(message);

}


// -----------------------------------------------------
// Confirm an action
// -----------------------------------------------------

function confirmAction(message) {

    return confirm(message);

}


// -----------------------------------------------------
// Format date
// -----------------------------------------------------

function formatDate(dateString) {

    const date = new Date(dateString);

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });

}


// -----------------------------------------------------
// Format date and time
// -----------------------------------------------------

function formatDateTime(dateString) {

    const date = new Date(dateString);

    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });

}


// -----------------------------------------------------
// Close modal when clicking outside
// -----------------------------------------------------

document.addEventListener("click", function(event) {

    const modal = document.querySelector(".modal");

    if (
        modal &&
        event.target === modal
    ) {

        modal.style.display = "none";

    }

});