/**
 * Handles the signup process.
 */
function signup() {
  let email = document.getElementById("email").value;
  let password = document.getElementById("password").value;
  let name = document.getElementById("name").value;
  let confirmPassword = document.getElementById("confirm_password").value;

  // Validate password match
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
        window.location.href = "/login"; // Redirect to login page
      } else {
        window.location.href = "/signup"; // Redirect to
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred during signup.");
    });
}
