// =====================================================
// MEDIFIND - DASHBOARD JAVASCRIPT
// =====================================================


// -----------------------------------------------------
// Load upcoming medications
// -----------------------------------------------------

async function loadUpcomingMedication() {

    try {

        const response =
            await fetch("/api/medications/upcoming");


        if (!response.ok) {

            throw new Error(
                "Unable to load medication."
            );

        }


        const data =
            await response.json();


        displayUpcomingMedication(data);

    }
    catch (error) {

        console.error(error);

    }

}


// -----------------------------------------------------
// Display upcoming medication
// -----------------------------------------------------

function displayUpcomingMedication(medication) {

    const container =
        document.querySelector(".medicine-card");


    if (!container) {
        return;
    }


    if (!medication) {

        container.innerHTML = `

            <div>

                <h3>No upcoming medication</h3>

                <p>
                    You don't have any upcoming doses.
                </p>

            </div>

        `;

        return;

    }


    container.innerHTML = `

        <div>

            <h3>
                ${medication.name}
            </h3>

            <p>
                Next dose:
                <strong>
                    ${medication.next_dose}
                </strong>
            </p>

        </div>


        <button
            class="secondary-button"
            onclick="markDoseTaken(${medication.id})"
        >
            Mark as Taken
        </button>

    `;

}


// -----------------------------------------------------
// Mark dose as taken
// -----------------------------------------------------

async function markDoseTaken(medicationId) {

    try {

        const response = await fetch(
            `/api/medications/${medicationId}/taken`,
            {
                method: "POST"
            }
        );


        if (!response.ok) {

            throw new Error(
                "Unable to update medication."
            );

        }


        alert("Dose marked as taken.");


        loadUpcomingMedication();

    }
    catch (error) {

        console.error(error);

        alert(
            "Unable to update medication."
        );

    }

}


// -----------------------------------------------------
// Load dashboard data
// -----------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    function() {

        if (
            document.querySelector(
                ".dashboard-container"
            )
        ) {

            loadUpcomingMedication();

        }

    }
);