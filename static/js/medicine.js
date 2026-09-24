// =====================================================
// MEDIFIND - MEDICINE DETAILS JAVASCRIPT
// =====================================================


// -----------------------------------------------------
// Add medicine to user's medication list
// -----------------------------------------------------

async function addMedicineToMyList(medicineId) {

    try {

        const response = await fetch(
            `/api/medications`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    medicine_id: medicineId
                })
            }
        );


        if (!response.ok) {

            throw new Error(
                "Unable to add medicine."
            );

        }


        alert(
            "Medicine added to your medicines."
        );

    }
    catch (error) {

        console.error(error);

        alert(
            "Unable to add medicine."
        );

    }

}


// -----------------------------------------------------
// Load medicine safety information
// -----------------------------------------------------

async function loadSafetyInformation(medicineId) {

    try {

        const response = await fetch(
            `/api/medicine/${medicineId}/safety`
        );


        if (!response.ok) {

            throw new Error(
                "Unable to load safety information."
            );

        }


        const data =
            await response.json();


        displaySafetyInformation(data);

    }
    catch (error) {

        console.error(error);

    }

}


// -----------------------------------------------------
// Display safety information
// -----------------------------------------------------

function displaySafetyInformation(data) {

    const sideEffects =
        document.querySelector(
            ".side-effects-list"
        );


    const precautions =
        document.querySelector(
            ".precautions-list"
        );


    if (sideEffects) {

        sideEffects.innerHTML = "";


        data.side_effects.forEach(
            function(effect) {

                const li =
                    document.createElement("li");

                li.textContent = effect;

                sideEffects.appendChild(li);

            }
        );

    }


    if (precautions) {

        precautions.innerHTML = "";


        data.precautions.forEach(
            function(precaution) {

                const li =
                    document.createElement("li");

                li.textContent = precaution;

                precautions.appendChild(li);

            }
        );

    }

}