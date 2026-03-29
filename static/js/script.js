//Login validation
window.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");
    const passwordMessage = document.getElementById("password-message");
    const confirmInput = document.getElementById("confirm_password");
    const confirmMessage = document.getElementById("confirm-message");

    passwordInput.addEventListener("input", () => {
        const password = passwordInput.value;
        let errors = [];

        if (password.length < 10) errors.push("At least 10 characters");
        if (!/[A-Z]/.test(password)) errors.push("At least 1 uppercase letter");
        if (!/[a-z]/.test(password)) errors.push("At least 1 lowercase letter");
        if (!/[0-9]/.test(password)) errors.push("At least 1 number");
        if (!/[!@#$%^&*(),.?\":{}|<>]/.test(password)) errors.push("At least 1 symbol");

        if (errors.length === 0) {
            passwordMessage.style.color = "green";
            passwordMessage.textContent = "Password looks good!";
        } else {
            passwordMessage.style.color = "red";
            passwordMessage.textContent = "Password must include: " + errors.join(", ");
        }
    });

    confirmInput.addEventListener("input", () => {
        if (confirmInput.value !== passwordInput.value) {
            confirmMessage.textContent = "Passwords do not match";
            confirmMessage.style.color = "red";
        } else {
            confirmMessage.textContent = "Passwords match";
            confirmMessage.style.color = "green";
        }
    });
});

//Automatically shows to the user the application after entering a letter or more
document.getElementById("searchInput").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        this.form.submit();
    }
});

//Gives the user an option between choosing a predefined and custom status
const customInput = document.getElementById("customStatus");
const dropdown = document.getElementById("statusDropdown");

//If the custom statuses are chosen then the dropdown for predefined statuses are disabled
customInput.addEventListener('input', () => {
    dropdown.disabled = customInput.value.trim() !== '';
});

// Function to confirm deletion of an application
// Shows a popup asking the user to confirm before deleting
function confirmDelete() {
    return confirm("Are you sure you want to delete this application?");
}

// Function to confirm logout
// Shows a popup asking the user to confirm before logging out
function confirmLogout() {
    return confirm("Are you sure you want to log out?");
}
