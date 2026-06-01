(function () {
  const form = document.querySelector("form");
  const profileInput = document.getElementById("profile");
  const profileBase64 = document.getElementById("profile_base64");

  profileInput.addEventListener("change", function () {
    const file = this.files[0];
    if (!file) {
      profileBase64.value = "";
      return;
    }

    document.querySelectorAll(".file-warning").forEach(function (el) {
      el.remove();
    });

    if (file.size > 15 * 1024 * 1024) {
      const warn = document.createElement("p");
      warn.className = "file-warning";
      warn.style.color = "#c00";
      warn.textContent =
        "Image is too large (" +
        (file.size / (1024 * 1024)).toFixed(1) +
        "MB). Maximum is 15MB.";
      profileInput.parentNode.after(warn);
      this.value = "";
      profileBase64.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      profileBase64.value = e.target.result;
    };
    reader.readAsDataURL(file);
  });

  form.addEventListener("submit", function (e) {
    document.querySelectorAll(".field-error").forEach(function (el) {
      el.remove();
    });

    const errors = [];

    const fullName = form.full_name.value.trim();
    const userName = form.user_name.value.trim();
    const email = form.user_email.value.trim();
    const password = form.password.value;
    const passwordConfirm = form.password_confirm.value;

    if (!fullName) {
      errors.push("Full name is required.");
    } else if (fullName.length > 64) {
      errors.push("Full name must be 64 characters or less.");
    }

    if (!userName) {
      errors.push("Username is required.");
    } else if (userName.length > 24) {
      errors.push("Username must be 24 characters or less.");
    }

    if (!email) {
      errors.push("Email is required.");
    }

    if (!password) {
      errors.push("Password is required.");
    } else {
      if (password.length < 8) {
        errors.push("Password must be at least 8 characters.");
      }
      if (!/[A-Z]/.test(password)) {
        errors.push("Password must contain an uppercase letter.");
      }
      if (!/[a-z]/.test(password)) {
        errors.push("Password must contain a lowercase letter.");
      }
      if (!/[0-9]/.test(password)) {
        errors.push("Password must contain a digit.");
      }
      if (!/[^A-Za-z0-9]/.test(password)) {
        errors.push("Password must contain a special character.");
      }
    }

    if (!passwordConfirm) {
      errors.push("Please confirm your password.");
    } else if (password !== passwordConfirm) {
      errors.push("Passwords do not match.");
    }

    if (!form.querySelector('input[name="user_role"]:checked')) {
      errors.push("Please select a role.");
    }

    if (errors.length) {
      e.preventDefault();
      const container = document.createElement("div");
      container.className = "field-error";
      container.style.color = "#c00";
      container.style.marginBottom = "1em";
      container.innerHTML = errors.join("<br>");
      form.prepend(container);
    }
  });
})();
