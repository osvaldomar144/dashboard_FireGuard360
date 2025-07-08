document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/sensors");  // namespace definito in Flask

  const tableId = "#sensors-table"; 

  let startDate = null;
  let endDate = null;

  // Inizializza DataTables
  let dataTable = $(tableId).DataTable({
    responsive: true,
    language: {
      url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json'
    },
    dom: '<"d-flex justify-content-between align-items-center"lfB>rtip',
    buttons: ['copy', 'csv', 'excel', 'pdf', 'print']
  });

  const getColor = (i) => `hsl(${i * 60}, 70%, 50%)`;

  // === CREA I GRAFICI DOPO CHE IL DOM È PRONTO ===
  const tempChart = new Chart(document.getElementById("chartTemp").getContext("2d"), {
    type: 'line',
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Andamento Temperatura per Sensore" },
        legend: { position: "top" }
      },
      scales: {
        x: { title: { display: true, text: "Tempo" } },
        y: { beginAtZero: true, title: { display: true, text: "Temperatura (°C)" } }
      }
    }
  });

  const humChart = new Chart(document.getElementById("chartUmi").getContext("2d"), {
    type: 'line',
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Andamento Umidità per Sensore" },
        legend: { position: "top" }
      },
      scales: {
        x: { title: { display: true, text: "Tempo" } },
        y: { beginAtZero: true, title: { display: true, text: "Umidità (%)" } }
      }
    }
  });

  const gasChart = new Chart(document.getElementById("chartGas").getContext("2d"), {
    type: 'line',
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: "Andamento Gas per Sensore" },
        legend: { position: "top" }
      },
      scales: {
        x: { title: { display: true, text: "Tempo" } },
        y: { beginAtZero: true, title: { display: true, text: "Gas (ppm)" } }
      }
    }
  });

  // Invio dei parametri di filtro
  function sendFilter() {
    socket.emit("update_filter", {
      start_date: startDate,
      end_date: endDate
    });
  }

  // Intercetta invio del form
  const filterForm = document.getElementById("filterForm");
  if (filterForm) {
    filterForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const startInput = document.getElementById("startDate").value;
      const endInput = document.getElementById("endDate").value;

      startDate = startInput ? new Date(startInput).toISOString() : null;
      endDate = endInput ? new Date(endInput).toISOString() : null;

      sendFilter(); // Invia parametri aggiornati
    });
  }

  socket.on("connect", () => {
    console.log("[WS] Connesso al namespace /sensors");
    sendFilter(); // Invio iniziale
  });

  socket.on("disconnect", () => console.log("[WS] Disconnesso da /sensors"));

  // Dati grezzi → tabella
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

  // Dati aggregati → grafici
  socket.on("update_stats", (stats) => {
    if (!stats || stats.length === 0) return;

    stats.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const labels = stats.map(row => row.timestamp);

    const temperatureMap = {};
    const humidityMap = {};
    const gasMap = {};

    stats.forEach(row => {
      const sid = row.sensor_id;
      if (!temperatureMap[sid]) {
        temperatureMap[sid] = [];
        humidityMap[sid] = [];
        gasMap[sid] = [];
      }
      temperatureMap[sid].push(row.avg_temperature);
      humidityMap[sid].push(row.avg_humidity);
      gasMap[sid].push(row.avg_gas);
    });

    const buildDataset = (dataMap) =>
      Object.entries(dataMap).map(([sid, values], index) => ({
        label: sid,
        data: values,
        borderColor: getColor(index),
        fill: false,
        tension: 0.3
      }));

    tempChart.data.labels = labels;
    tempChart.data.datasets = buildDataset(temperatureMap);
    tempChart.update();

    humChart.data.labels = labels;
    humChart.data.datasets = buildDataset(humidityMap);
    humChart.update();

    gasChart.data.labels = labels;
    gasChart.data.datasets = buildDataset(gasMap);
    gasChart.update();
  });
});







/*document.addEventListener("DOMContentLoaded", () => {
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

  lineChart = window["lineChart_chart"];

  socket.on("connect", () => console.log("[WS] Connesso al namespace /sensors"));
  socket.on("disconnect", () => console.log("[WS] Disconnesso da /sensors"));

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


    // Se il grafico esiste, aggiorna
    if (lineChart) {
      data.sort((a, b) => new Date(a.detected_at) - new Date(b.detected_at));
      const labels = data.map(row => row.detected_at);
      const values = data.map(row => row.temperature);

      lineChart.data.labels = labels;
      lineChart.data.datasets[0].data = values;
      lineChart.update();
    }

  });
    
});*/