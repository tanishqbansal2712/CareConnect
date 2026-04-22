
new Vue({
  el: "#app",
  delimiters: ['[[', ']]'],

  data: {
    username: "",
    password: "",
    role: ""
  },

  created() {
    this.role = window.location.pathname.split("/").pop()
  },

  methods: {
    login() {
      fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: this.username,
          password: this.password,
          role: this.role
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.token) {
          localStorage.setItem("token", data.token)

          // save role-specific id so dashboards can use it
          if (data.patient_id)
            localStorage.setItem("patient_id", data.patient_id)
          if (data.patient_name)
            localStorage.setItem("patient_name", data.patient_name)
          if (data.doctor_id)
            localStorage.setItem("doctor_id", data.doctor_id)
          if (data.doctor_name)
            localStorage.setItem("doctor_name", data.doctor_name)

          window.location.href = "/dashboard_" + this.role
        } else {
          showToast(data.msg || "Invalid credentials", "danger")
        }
      })
    }
  }
})