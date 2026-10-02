// =====================================================
// MEDIFIND - MEDICINE DETAILS JAVASCRIPT
// =====================================================


// =====================================================
// SMALL HELPERS
// =====================================================

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function getJsonError(data, fallback) {

    if (data && data.error) {
        return data.error;
    }

    if (data && data.message) {
        return data.message;
    }

    return fallback;
}


async function readJsonResponse(response) {

    const contentType =
        response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {

        const text = await response.text();

        throw new Error(
            "Server returned a non-JSON response: " +
            text.substring(0, 250)
        );
    }

    return await response.json();
}


// =====================================================
// ADD MEDICINE TO USER'S MEDICATION LIST
// =====================================================

async function addMedicineToMyList(medicineId) {

    try {

        const response = await fetch(
            "/api/medications",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    medicine_id: medicineId
                })
            }
        );


        const data =
            await readJsonResponse(response);


        if (!response.ok) {

            if (response.status === 401) {

                window.location.href =
                    "/login";

                return;
            }


            throw new Error(
                getJsonError(
                    data,
                    "Unable to add medicine."
                )
            );
        }


        alert(
            data.message ||
            "Medicine added to My Medicines."
        );


        window.location.href =
            "/medications";

    }
    catch (error) {

        console.error(
            "Add medicine error:",
            error
        );


        alert(
            error.message ||
            "Unable to add medicine."
        );
    }
}


// =====================================================
// LOAD SUBSTITUTE MEDICINES
// =====================================================

async function loadSubstitutes(medicineId) {

    const container =
        document.querySelector(
            "#substitutes-container"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="empty-state">

            <h2>
                Finding substitutes...
            </h2>

            <p>
                Checking medicines with matching composition.
            </p>

        </div>

    `;


    try {

        const response =
            await fetch(
                `/api/medicine/${encodeURIComponent(medicineId)}/substitutes`,
                {
                    method: "GET",

                    headers: {
                        "Accept": "application/json"
                    },

                    cache: "no-store"
                }
            );


        const data =
            await readJsonResponse(response);


        console.log(
            "Substitute API response:",
            data
        );


        if (
            !response.ok ||
            data.success !== true
        ) {

            throw new Error(
                getJsonError(
                    data,
                    "Unable to load substitutes."
                )
            );
        }


        displaySubstitutes(
            data.substitutes || [],
            data.medicine || null
        );

    }
    catch (error) {

        console.error(
            "Substitute error:",
            error
        );


        container.innerHTML = `

            <div class="empty-state">

                <h2>
                    Unable to load substitutes
                </h2>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Something went wrong."
                    )}
                </p>

                <button
                    type="button"
                    class="secondary-button"
                    onclick="loadSubstitutes(${Number(medicineId)})"
                    style="margin-top:15px;"
                >
                    Try Again
                </button>

            </div>

        `;
    }
}


// =====================================================
// DISPLAY SUBSTITUTE MEDICINES
// =====================================================

function displaySubstitutes(
    substitutes,
    originalMedicine
) {

    const container =
        document.querySelector(
            "#substitutes-container"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !substitutes ||
        substitutes.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <h2>
                    No substitutes found
                </h2>

                <p>
                    No other medicine with the same
                    composition was found in the
                    MediFind database.
                </p>

            </div>

        `;

        return;
    }


    substitutes.forEach(
        function(medicine) {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "medicine-result-card";


            const medicineName =
                medicine.medicine_name ||
                medicine.name ||
                "Unknown medicine";


            const price =
                Number(
                    medicine.price || 0
                );


            let priceMessage = "";


            if (
                originalMedicine &&
                Number(originalMedicine.price) >
                price
            ) {

                const saving =
                    Number(originalMedicine.price) -
                    price;


                priceMessage = `

                    <p class="saving-text">

                        Lower database price by
                        ₹${saving.toFixed(2)}.

                    </p>

                `;
            }


            card.innerHTML = `

                <div>

                    <h3>
                        ${escapeHtml(
                            medicineName
                        )}
                    </h3>


                    <p>

                        <strong>
                            Composition:
                        </strong>

                        ${escapeHtml(
                            medicine.composition ||
                            "Not available"
                        )}

                    </p>


                    <p>

                        <strong>
                            Manufacturer:
                        </strong>

                        ${escapeHtml(
                            medicine.manufacturer ||
                            "Not available"
                        )}

                    </p>


                    <p class="price">

                        ₹${price.toFixed(2)}

                    </p>


                    ${priceMessage}

                </div>


                <a
                    href="/medicine/${Number(medicine.id)}"
                    class="secondary-button"
                >

                    View Details

                </a>

            `;


            container.appendChild(
                card
            );

        }
    );
}


// =====================================================
// SHOW AI RESULT
// =====================================================

function showAIResult(
    containerId,
    title,
    text,
    disclaimer
) {

    const container =
        document.getElementById(
            containerId
        );


    if (!container) {
        return;
    }


    container.style.display =
        "block";


    container.innerHTML = `

        <div
            class="safety-card"
            style="
                margin-top:20px;
                border-left:5px solid #2563eb;
            "
        >

            <h3>
                ${escapeHtml(title)}
            </h3>


            <div
                style="
                    white-space:pre-wrap;
                    line-height:1.75;
                    font-size:16px;
                    color:#334155;
                "
            >
                ${escapeHtml(text)}
            </div>


            ${
                disclaimer
                ?
                `
                    <p
                        class="medical-warning"
                        style="margin-top:18px;"
                    >
                        ${escapeHtml(
                            disclaimer
                        )}
                    </p>
                `
                :
                ""
            }

        </div>

    `;
}


// =====================================================
// SHOW AI ERROR
// =====================================================

function showAIError(
    containerId,
    errorMessage
) {

    const container =
        document.getElementById(
            containerId
        );


    if (!container) {
        return;
    }


    container.style.display =
        "block";


    container.innerHTML = `

        <div
            class="safety-card"
            style="
                margin-top:20px;
                border-left:5px solid #dc2626;
            "
        >

            <h3 style="color:#dc2626;">

                AI could not respond

            </h3>


            <p>

                ${escapeHtml(
                    errorMessage ||
                    "Unable to get an answer from Gemini."
                )}

            </p>


            <p style="margin-top:10px;">

                Check the Flask terminal for
                the detailed Gemini API error.

            </p>

        </div>

    `;
}


// =====================================================
// GET GENERAL AI MEDICINE ADVICE
// =====================================================

async function getAIAdvice() {

    const button =
        document.getElementById(
            "get-ai-advice-button"
        );


    const result =
        document.getElementById(
            "ai-advice-result"
        );


    if (!button || !result) {

        console.error(
            "AI advice elements are missing."
        );

        return;
    }


    button.disabled =
        true;


    button.textContent =
        "🤖 Getting AI Advice...";


    result.style.display =
        "block";


    result.innerHTML = `

        <div class="empty-state">

            <h2>
                AI is preparing the medicine information...
            </h2>

            <p>
                Please wait.
            </p>

        </div>

    `;


    try {

        const response =
            await fetch(
                `/api/medicine/${encodeURIComponent(currentMedicineId)}/safety`,
                {
                    method: "GET",

                    headers: {
                        "Accept": "application/json"
                    },

                    cache: "no-store"
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        console.log(
            "AI safety response:",
            data
        );


        if (
            !response.ok ||
            data.success !== true
        ) {

            throw new Error(
                getJsonError(
                    data,
                    "Gemini did not return an answer."
                )
            );
        }


        showAIResult(
            "ai-advice-result",
            "AI Medicine Information",
            data.advice ||
            data.answer ||
            "No AI information was returned.",
            data.disclaimer ||
            ""
        );

    }
    catch (error) {

        console.error(
            "AI advice error:",
            error
        );


        showAIError(
            "ai-advice-result",
            error.message
        );

    }
    finally {

        button.disabled =
            false;


        button.textContent =
            "🤖 Get AI Advice";
    }
}


// =====================================================
// ASK AI QUESTION
// =====================================================

async function askAI() {

    const input =
        document.getElementById(
            "ai-question"
        );


    const button =
        document.getElementById(
            "ask-ai-button"
        );


    const result =
        document.getElementById(
            "ai-question-result"
        );


    if (!input || !button) {

        console.error(
            "Ask AI elements are missing."
        );

        return;
    }


    const question =
        input.value.trim();


    if (!question) {

        alert(
            "Please enter your question first."
        );


        input.focus();

        return;
    }


    button.disabled =
        true;


    button.textContent =
        "Thinking...";


    if (result) {

        result.style.display =
            "block";


        result.innerHTML = `

            <div class="empty-state">

                <h2>
                    AI is thinking...
                </h2>

                <p>
                    Preparing an answer for your question.
                </p>

            </div>

        `;
    }


    try {

        const response =
            await fetch(
                "/api/ai/advisor",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify({

                        medicine_id:
                            currentMedicineId,

                        question:
                            question

                    })
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        console.log(
            "AI question response:",
            data
        );


        if (
            !response.ok ||
            data.success !== true
        ) {

            if (
                response.status === 401
            ) {

                throw new Error(
                    "Please log in before using Ask AI."
                );
            }


            throw new Error(
                getJsonError(
                    data,
                    "Gemini did not return an answer."
                )
            );
        }


        showAIResult(
            "ai-question-result",
            "AI Answer",
            data.answer ||
            "No answer returned.",
            data.disclaimer ||
            ""
        );

    }
    catch (error) {

        console.error(
            "Ask AI error:",
            error
        );


        showAIError(
            "ai-question-result",
            error.message
        );

    }
    finally {

        button.disabled =
            false;


        button.textContent =
            "Ask AI";
    }
}


// =====================================================
// PAGE INITIALIZATION
// =====================================================

window.addEventListener(
    "DOMContentLoaded",
    function () {

        if (
            typeof currentMedicineId !==
            "undefined"
        ) {

            loadSubstitutes(
                currentMedicineId
            );
        }


        const questionInput =
            document.getElementById(
                "ai-question"
            );


        if (questionInput) {

            questionInput.addEventListener(
                "keydown",
                function (event) {

                    if (
                        (event.ctrlKey ||
                            event.metaKey) &&
                        event.key === "Enter"
                    ) {

                        askAI();
                    }

                }
            );
        }

    }
);