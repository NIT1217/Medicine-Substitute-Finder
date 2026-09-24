// =====================================================
// MEDIFIND - SEARCH JAVASCRIPT
// =====================================================


// Get search form

const searchForm =
    document.querySelector(".medicine-search-form");


if (searchForm) {

    searchForm.addEventListener("submit", async function(event) {

        // Prevent normal page reload

        event.preventDefault();


        const query =
            document.querySelector(
                'input[name="query"]'
            ).value.trim();


        const searchType =
            document.querySelector(
                'select[name="search_type"]'
            ).value;


        if (query === "") {

            alert("Please enter a medicine name or composition.");

            return;

        }


        try {

            // Show loading message

            showLoading();


            // Call Flask API

            const response = await fetch(
                `/api/search?query=${encodeURIComponent(query)}&search_type=${searchType}`
            );


            if (!response.ok) {

                throw new Error(
                    "Unable to search medicines."
                );

            }


            const data = await response.json();


            displaySearchResults(data.results);


        }
        catch (error) {

            console.error(error);

            alert(
                "Something went wrong while searching."
            );

        }
        finally {

            hideLoading();

        }

    });

}


// -----------------------------------------------------
// Display search results
// -----------------------------------------------------

function displaySearchResults(results) {

    const container =
        document.querySelector(".results-container");


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!results || results.length === 0) {

        container.innerHTML = `
            <div class="empty-state">

                <h2>No medicines found</h2>

                <p>
                    Try another medicine name or composition.
                </p>

            </div>
        `;

        return;

    }


    results.forEach(function(medicine) {

        const card = document.createElement("div");

        card.className = "medicine-result-card";


        card.innerHTML = `

            <div>

                <h3>
                    ${medicine.name}
                </h3>

                <p>
                    Composition:
                    ${medicine.composition}
                </p>

                <p>
                    Manufacturer:
                    ${medicine.manufacturer}
                </p>

                <p class="price">
                    ₹${medicine.price}
                </p>

            </div>


            <a
                href="/medicine/${medicine.id}"
                class="secondary-button"
            >
                View Details
            </a>

        `;


        container.appendChild(card);

    });

}


// -----------------------------------------------------
// Loading message
// -----------------------------------------------------

function showLoading() {

    const container =
        document.querySelector(".results-container");


    if (container) {

        container.innerHTML = `
            <div class="empty-state">

                <h2>Searching...</h2>

                <p>
                    Finding matching medicines.
                </p>

            </div>
        `;

    }

}


// -----------------------------------------------------
// Remove loading message
// -----------------------------------------------------

function hideLoading() {

    // Results will replace the loading message.

}