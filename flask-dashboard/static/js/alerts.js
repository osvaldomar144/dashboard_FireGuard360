document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/alerts");  // namespace definito in Flask

  const tableId = "#alerts-table"; 

  // Inizializza DataTables dopo il caricamento iniziale
  let dataTable = $(tableId).DataTable({
    responsive: true,
    language: {
      url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json'
    },
    dom: '<"d-flex justify-content-between align-items-center"lfB>rtip',
    buttons: [
      'copy', 'csv', 'excel', 'pdf', 'print'
    ]
  });

  socket.on("connect", () => {
    console.log("[WS] Connesso al namespace /alerts");
  });

  socket.on("disconnect", () => {
    console.log("[WS] Disconnesso da /alerts");
  });

  socket.on("update_alerts", (data) => {
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
