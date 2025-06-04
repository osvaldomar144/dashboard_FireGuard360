document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/overview");  // namespace definito in Flask

  const tableId = "#alerts-table"; 
  let dataTable;

  // Inizializza DataTables dopo il caricamento iniziale
  dataTable = $(tableId).DataTable();

  socket.on("connect", () => {
    console.log("[WS] Connesso al namespace /overview");
  });

  socket.on("disconnect", () => {
    console.log("[WS] Disconnesso da /overview");
  });

  socket.on("update_alerts", (data) => {
    console.log("[WS] Ricevuti nuovi dati alerts", data);

    // Svuota la tabella e reinserisci righe
    dataTable.clear();

    data.forEach((row) => {
      dataTable.row.add([
        row.timestamp || "",
        row.sensor_id || "",
        row.alert_type || "",
        row.description || "",
        row.severity || "",
      ]);
    });

    dataTable.draw();
  });
});
