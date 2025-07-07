/*const socket = io("/device");

socket.on("connect", () => {
  console.log("[WS] Connesso a /device");
});

socket.on("danger_level_update", (data) => {
  const level = data.danger_level;
  updateDangerLevel(level);
  sendAutoCommand(level);
});

let lastCommandSent = null;

function sendAutoCommand(level) {
  const commandMap = {
    0: "0D", // Nessun rischio
    1: "1D", // Potenziale
    2: "2D"  // Confermato
  };

  const command = commandMap[level];

  if (command !== lastCommandSent) {
    fetch("http://localhost:5001/send-command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command })
    })
    .then(response => {
      if (!response.ok) throw new Error("Errore comando");
      return response.json();
    })
    .then(() => {
      showCommandAlert(`Comando ${command} inviato automaticamente`, "success");
      lastCommandSent = command;
    })
    .catch(() => {
      showCommandAlert("Errore nell'invio del comando automatico!", "danger");
    });
  }
}


document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".command-btn");

    buttons.forEach(button => {
        button.addEventListener("click", () => {
        const command = button.getAttribute("data-command");

        fetch("http://localhost:5001/send-command", {
            method: "POST",
            headers: {
            "Content-Type": "application/json"
            },
            body: JSON.stringify({ command })
        })
        .then(response => {
            if (!response.ok) throw new Error("Errore nel comando");
            return response.json();
        })
        .then(() => showCommandAlert("Comando inviato con successo!", "success"))
        .catch(() => showCommandAlert("Errore nell'invio del comando!", "danger"));
        });
    });

    function showCommandAlert(message, type) {
    const alertBox = document.getElementById("command-alert");
    const alertText = document.getElementById("command-alert-message");

    alertBox.classList.remove("d-none", "alert-success", "alert-danger", "show");
    alertBox.classList.add(`alert-${type}`, "show");
    alertText.textContent = message;

    setTimeout(() => {
        alertBox.classList.remove("show");
        setTimeout(() => {
        alertBox.classList.add("d-none");
        }, 500); // tempo per animazione uscita
    }, 3000);
    }

});
*/

document.addEventListener("DOMContentLoaded", () => {
    const socket = io("/device");

    socket.on("connect", () => {
    console.log("[WS] Connesso a /device");
    });

    socket.on("disconnect", () => {
        console.log("[WS] Disconnesso da /device");
    });


    socket.on("danger_level_update", (data) => {
    const level = data.danger_level;
    updateDangerLevel(level);
    sendAutoCommand(level);
    });

    let lastCommandSent = null;

    // Funzione per inviare automaticamente comandi al cambio livello
    function sendAutoCommand(level) {
    const commandMap = {
        0: "0D", // Nessun rischio
        1: "1D", // Potenziale
        2: "2D"  // Confermato
    };

  const command = commandMap[level];

  if (command !== lastCommandSent) {
    fetch("http://localhost:5001/send-command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command })
    })
    .then(response => {
      if (!response.ok) throw new Error("Errore comando");
      return response.json();
    })
    .then(() => {
      showCommandAlert(`Comando ${command} inviato automaticamente`, "success");
      lastCommandSent = command;
    })
    .catch(() => {
      showCommandAlert("Errore nell'invio del comando automatico!", "danger");
    });
  }
}

// Funzione per aggiornare graficamente il danger level
function updateDangerLevel(value) {
  const dangerBox = document.getElementById("danger-level-box");
  const dangerValue = document.getElementById("danger-value");

  dangerValue.textContent = value;

  if (value === 0) dangerBox.style.backgroundColor = "#28a745";       // Verde
  else if (value === 1) dangerBox.style.backgroundColor = "#ffc107";  // Giallo
  else dangerBox.style.backgroundColor = "#dc3545";                   // Rosso
}


  // Imposta il comando attuale come già inviato (evita doppio comando all'avvio)
  const currentLevel = parseInt(document.getElementById("danger-value").textContent);
  if (!isNaN(currentLevel)) {
    const map = { 0: "0D", 1: "1D", 2: "2D" };
    lastCommandSent = map[currentLevel] || null;
  }

  // Gestione click manuale sui pulsanti
  const buttons = document.querySelectorAll(".command-btn");

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      const command = button.getAttribute("data-command");

      fetch("http://localhost:5001/send-command", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ command })
      })
      .then(response => {
        if (!response.ok) throw new Error("Errore nel comando");
        return response.json();
      })
      .then(() => showCommandAlert(`Comando ${command} inviato manualmente`, "success"))
      .catch(() => showCommandAlert("Errore nell'invio del comando!", "danger"));
    });
  });

  // Notifica visiva
  function showCommandAlert(message, type) {
    const alertBox = document.getElementById("command-alert");
    const alertText = document.getElementById("command-alert-message");

    alertBox.classList.remove("d-none", "alert-success", "alert-danger", "show");
    alertBox.classList.add(`alert-${type}`, "show");
    alertText.textContent = message;

    setTimeout(() => {
      alertBox.classList.remove("show");
      setTimeout(() => {
        alertBox.classList.add("d-none");
      }, 500); // tempo per animazione uscita
    }, 3000);
  }
});
