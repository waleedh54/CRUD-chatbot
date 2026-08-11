const API_BASE = "http://localhost:8000";
const token = localStorage.getItem("token");
const adminEmail = localStorage.getItem("admin_email");

if (!token) {
  window.location.href = "login.html";
}

document.getElementById("adminEmail").textContent = adminEmail || "";

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.clear();
  window.location.href = "login.html";
});

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");

function appendMessage(text, cls) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${cls}`;
  bubble.textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  messageInput.value = "";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message }),
    });

    if (res.status === 401) {
      localStorage.clear();
      window.location.href = "login.html";
      return;
    }

    const data = await res.json();
    if (!res.ok) {
      appendMessage(data.detail || "Something went wrong.", "bot error");
      return;
    }
    appendMessage(data.reply, data.success ? "bot" : "bot error");
  } catch (err) {
    appendMessage("Could not reach server.", "bot error");
  }
});