/**
 * Handles the signup process.
 * Validates the user's input, sends the data to the backend, and handles the response.
 */
function signup() {
  let email = document.getElementById("email").value;
  let password = document.getElementById("password").value;
  let name = document.getElementById("name").value;
  let confirmPassword = document.getElementById("confirm_password").value;

  // Validate that the password and confirm password match
  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return;
  }

  // Send signup data to backend
  fetch("/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email,
      password: password,
      name: name,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // If signup is successful, redirect to the login page
        window.location.href = "/login";
      } else {
        // If there's an error, redirect back to the signup page
        window.location.href = "/signup";
      }
    })
    .catch((error) => {
      // Handle any network or unexpected errors
      console.error("Error:", error);
      alert("An error occurred during signup.");
    });
}
