// =====================================================
// MEDIFIND - PROFILE JAVASCRIPT
// =====================================================


// -----------------------------------------------------
// Notification setting
// -----------------------------------------------------

const notificationToggle =
    document.querySelector(
        'input[name="medication_notifications"]'
    );


if (notificationToggle) {

    notificationToggle.addEventListener(
        "change",
        async function() {

            const enabled =
                this.checked;


            try {

                const response =
                    await fetch(
                        "/api/profile/notifications",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                enabled: enabled
                            })
                        }
                    );


                if (!response.ok) {

                    throw new Error(
                        "Unable to update notification settings."
                    );

                }


                console.log(
                    "Notification setting updated."
                );

            }
            catch (error) {

                console.error(error);

                alert(
                    "Unable to update notification settings."
                );

            }

        }
    );

}