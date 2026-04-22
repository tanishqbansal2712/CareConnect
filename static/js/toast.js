
// Usage: showToast("Doctor added successfully", "success")
//        showToast("Something went wrong", "danger")
//        showToast("Appointment cancelled", "warning")
//        showToast("Check your email", "info")

function showToast(message, type = "success") {
    // type: success | danger | warning | info
  
    const icons = {
      success: "✅",
      danger:  "❌",
      warning: "⚠️",
      info:    "ℹ️",
    }
  
    const colors = {
      success: "#198754",
      danger:  "#dc3545",
      warning: "#fd7e14",
      info:    "#0d6efd",
    }
  
    // create container if it doesn't exist
    let container = document.getElementById("toast-container")
    if (!container) {
      container = document.createElement("div")
      container.id = "toast-container"
      container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
      `
      document.body.appendChild(container)
    }
  
    // create toast element
    const toast = document.createElement("div")
    toast.style.cssText = `
      background: white;
      border-left: 5px solid ${colors[type] || colors.info};
      border-radius: 8px;
      padding: 14px 18px;
      min-width: 280px;
      max-width: 380px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      color: #333;
      animation: slideIn 0.3s ease;
    `
  
    toast.innerHTML = `
      <span style="font-size:18px">${icons[type] || icons.info}</span>
      <span style="flex:1">${message}</span>
      <span style="cursor:pointer;color:#999;font-size:18px;line-height:1"
            onclick="this.parentElement.remove()">×</span>
    `
  
    // add slide-in animation
    if (!document.getElementById("toast-style")) {
      const style = document.createElement("style")
      style.id = "toast-style"
      style.textContent = `
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(40px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideOut {
          from { opacity: 1; transform: translateX(0); }
          to   { opacity: 0; transform: translateX(40px); }
        }
      `
      document.head.appendChild(style)
    }
  
    container.appendChild(toast)
  
    // auto remove after 4 seconds
    setTimeout(() => {
      toast.style.animation = "slideOut 0.3s ease forwards"
      setTimeout(() => toast.remove(), 300)
    }, 4000)
  }