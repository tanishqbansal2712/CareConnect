
new Vue({
    el: "#app",
    data: {
      name:     "",
      email:    "",
      password: "",
      phone:    "",
      dob:      "",
      gender:   "",
      address:  ""
    },
  
    methods: {
      register() {
        fetch("/register", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: this.name,
            email:    this.email,
            password: this.password,
            phone:    this.phone,
            dob:      this.dob,
            gender:   this.gender,
            address:  this.address,
            role:     "patient"
          })
        })
        .then(r => r.json())
        .then(data => {
          if (data.token) {
            showToast("Registered successfully! Redirecting...", "success")
            setTimeout(() => {
              window.location.href = "/login/patient"
            }, 1500)
          } else {
            showToast(data.msg || "Registration failed", "danger")
          }
        })
        .catch(() => {
          showToast("Something went wrong. Please try again.", "danger")
        })
      }
    }
  })