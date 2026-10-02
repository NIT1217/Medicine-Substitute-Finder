document.addEventListener("DOMContentLoaded", function () {

    const searchForm = document.querySelector(".search-form");

    const searchInput = document.getElementById("query");

    if (!searchForm) {
        return;
    }


    searchForm.addEventListener("submit", function () {

        if (!searchInput) {
            return;
        }


        const query = searchInput.value.trim();


        if (!query) {

            alert("Please enter a medicine name or composition.");

            return;

        }

    });

});