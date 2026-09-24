// =====================================================
// MEDIFIND - HISTORY JAVASCRIPT
// =====================================================


// -----------------------------------------------------
// Load search history
// -----------------------------------------------------

async function loadSearchHistory() {

    try {

        const response =
            await fetch(
                "/api/history"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load history."
            );

        }


        const data =
            await response.json();


        displayHistory(data);

    }
    catch (error) {

        console.error(error);

    }

}


// -----------------------------------------------------
// Display history
// -----------------------------------------------------

function displayHistory(history) {

    const tbody =
        document.querySelector(
            "table tbody"
        );


    if (!tbody) {

        return;

    }


    tbody.innerHTML = "";


    if (
        !history ||
        history.length === 0
    ) {

        return;

    }


    history.forEach(function(item) {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                ${formatDateTime(
                    item.searched_at
                )}
            </td>

            <td>
                ${item.search_text}
            </td>

            <td>
                ${item.medicine_name}
            </td>

            <td>
                ${item.composition}
            </td>

            <td>

                <a
                    href="/medicine/${item.medicine_id}"
                >
                    View
                </a>

            </td>

        `;


        tbody.appendChild(row);

    });

}


// -----------------------------------------------------
// Run when history page loads
// -----------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    function() {

        if (
            document.querySelector(
                ".history-container"
            )
        ) {

            loadSearchHistory();

        }

    }
);      