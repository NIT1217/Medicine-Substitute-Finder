// =====================================================
// MEDIFIND - REGISTER JAVASCRIPT
// =====================================================


const registerForm =
    document.querySelector(
        'form[action*="register"]'
    );


if (registerForm) {

    registerForm.addEventListener(
        "submit",
        function(event) {

            const password =
                document.getElementById(
                    "password"
                ).value;


            const confirmPassword =
                document.getElementById(
                    "confirm_password"
                ).value;


            // Check password length

            if (password.length < 8) {

                event.preventDefault();


                alert(
                    "Password must contain at least 8 characters."
                );


                return;

            }


            // Check password match

            if (
                password !==
                confirmPassword
            ) {

                event.preventDefault();


                alert(
                    "Passwords do not match."
                );


                return;

            }

        }
    );

}