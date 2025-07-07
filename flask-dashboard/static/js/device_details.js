document.addEventListener("DOMContentLoaded", () => {
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
