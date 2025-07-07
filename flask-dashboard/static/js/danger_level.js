export function initDangerLevelWidget() {
  const socket = io("/device");
  let lastCommandSent = null;

  const dangerBox = document.getElementById("danger-level-box");
  const dangerValue = document.getElementById("danger-value");

  const updateDangerLevel = (value) => {
    dangerValue.textContent = value;
    if (value === 0) dangerBox.style.backgroundColor = "#28a745";
    else if (value === 1) dangerBox.style.backgroundColor = "#ffc107";
    else dangerBox.style.backgroundColor = "#dc3545";
  };

  const sendAutoCommand = (level) => {
    const map = { 0: "0D", 1: "1D", 2: "2D" };
    const command = map[level];
    if (command !== lastCommandSent) {
      fetch("http://localhost:5001/send-command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command })
      })
        .then((res) => {
          if (!res.ok) throw new Error();
          return res.json();
        })
        .then(() => {
          showCommandAlert(`Comando ${command} inviato automaticamente`, "success");
          lastCommandSent = command;
        })
        .catch(() => {
          showCommandAlert("Errore nell'invio del comando automatico!", "danger");
        });
    }
  };

  const showCommandAlert = (message, type) => {
    const alertBox = document.getElementById("command-alert");
    const alertText = document.getElementById("command-alert-message");
    alertBox.classList.remove("d-none", "alert-success", "alert-danger", "show");
    alertBox.classList.add(`alert-${type}`, "show");
    alertText.textContent = message;
    setTimeout(() => {
      alertBox.classList.remove("show");
      setTimeout(() => {
        alertBox.classList.add("d-none");
      }, 500);
    }, 3000);
  };

  socket.on("connect", () => console.log("[WS] Connesso a /device"));
  socket.on("disconnect", () => console.log("[WS] Disconnesso da /device"));
  socket.on("danger_level_update", (data) => {
    const level = data.danger_level;
    updateDangerLevel(level);
    sendAutoCommand(level);
  });

  // inizializzazione da valore statico backend
  const initial = parseInt(dangerValue.textContent);
  if (!isNaN(initial)) {
    lastCommandSent = { 0: "0D", 1: "1D", 2: "2D" }[initial] || null;
  }
}
