// =====================================================
// MEDIFIND - MEDICATION JAVASCRIPT
// =====================================================


// -----------------------------------------------------
// Open Add Medicine modal
// -----------------------------------------------------

function openMedicationForm() {

    const modal =
        document.getElementById(
            "medication-form"
        );


    if (modal) {

        modal.style.display = "flex";

    }

}


// -----------------------------------------------------
// Close Add Medicine modal
// -----------------------------------------------------

function closeMedicationForm() {

    const modal =
        document.getElementById(
            "medication-form"
        );


    if (modal) {

        modal.style.display = "none";

    }

}


// -----------------------------------------------------
// Change frequency fields
// -----------------------------------------------------

const frequencySelect =
    document.getElementById("frequency");


if (frequencySelect) {

    frequencySelect.addEventListener(
        "change",
        function() {

            const selectedValue =
                this.value;


            console.log(
                "Selected frequency:",
                selectedValue
            );


            if (
                selectedValue === "custom"
            ) {

                showCustomFrequency();

            }
            else {

                hideCustomFrequency();

            }

        }
    );

}


// -----------------------------------------------------
// Show custom frequency
// -----------------------------------------------------

function showCustomFrequency() {

    let container =
        document.getElementById(
            "custom-frequency"
        );


    if (!container) {

        container =
            document.createElement("div");

        container.id =
            "custom-frequency";

        container.className =
            "form-group";


        container.innerHTML = `

            <label for="custom_hours">
                Every how many hours?
            </label>

            <input
                type="number"
                id="custom_hours"
                name="custom_hours"
                min="1"
                max="168"
                placeholder="Enter hours"
            >

        `;


        frequencySelect
            .parentElement
            .after(container);

    }

}


// -----------------------------------------------------
// Hide custom frequency
// -----------------------------------------------------

function hideCustomFrequency() {

    const container =
        document.getElementById(
            "custom-frequency"
        );


    if (container) {

        container.remove();

    }

}


// -----------------------------------------------------
// Delete medication
// -----------------------------------------------------

async function deleteMedication(
    medicationId
) {

    const confirmed =
        confirm(
            "Are you sure you want to remove this medicine?"
        );


    if (!confirmed) {

        return;

    }


    try {

        const response = await fetch(
            `/api/medications/${medicationId}`,
            {
                method: "DELETE"
            }
        );


        if (!response.ok) {

            throw new Error(
                "Unable to delete medication."
            );

        }


        alert(
            "Medicine removed successfully."
        );


        location.reload();

    }
    catch (error) {

        console.error(error);

        alert(
            "Unable to remove medicine."
        );

    }

}