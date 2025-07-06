document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/overview");  // namespace definito in Flask

  const tableId = "#alerts-table"; 
  const temperaturaBox = document.getElementById("temperatura");
  const umiditaBox = document.getElementById("umidita");
  const fumoBox = document.getElementById("fumo");

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
    console.log("[WS] Connesso al namespace /overview");
  });

  socket.on("disconnect", () => {
    console.log("[WS] Disconnesso da /overview");
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

  socket.on("update_sensor_values", (sensorData) => {
    const tempHtml = [];
    const humidHtml = [];
    const smokeHtml = [];

    sensorData.forEach((sensor) => {
      const id = sensor.sensor_id || "N/A";
      const temp = sensor.avg_temperature !== null ? `${sensor.avg_temperature.toFixed(1)} °C` : "-";
      const humid = sensor.avg_humidity !== null ? `${sensor.avg_humidity.toFixed(1)} %` : "-";
      const gas = sensor.avg_gas !== null ? `${sensor.avg_gas.toFixed(1)} ppm` : "-";

      tempHtml.push(`<div><strong>${id}</strong>: ${temp}</div>`);
      humidHtml.push(`<div><strong>${id}</strong>: ${humid}</div>`);
      smokeHtml.push(`<div><strong>${id}</strong>: ${gas}</div>`);
    });

    temperaturaBox.innerHTML = tempHtml.join("");
    umiditaBox.innerHTML = humidHtml.join("");
    fumoBox.innerHTML = smokeHtml.join("");
  });
  
});
