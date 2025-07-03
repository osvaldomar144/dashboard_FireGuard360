document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/sensors");  // namespace definito in Flask

  const tableId = "#sensors-table"; 

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
    console.log("[WS] Connesso al namespace /sensors");
  });

  socket.on("disconnect", () => {
    console.log("[WS] Disconnesso da /sensors");
  });

  socket.on("update_sensors", (data) => {
    dataTable.clear();
    data.forEach((row) => {
      dataTable.row.add([
        row.detected_at || "",
        row.sensor_id || "",
        row.temperature || "",
        row.humidity || "",
        row.gas || "",
        row.danger_value || "",
      ]);
    });
    dataTable.draw();
  });
    
});