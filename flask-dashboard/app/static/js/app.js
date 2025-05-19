$(document).ready(function () {
  const ctx = document.getElementById("graficoDinamico").getContext("2d");

  const graficoDinamico = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{ label: "Temperature",  }],
    },
    options: {
      borderWidth: 3,
      borderColor: ['rgba(255, 99, 132, 1)',],
    },
  });

function addData(label, data) {
  // Controlla se il label esiste già
  if (graficoDinamico.data.labels.includes(label)) {
    console.log("[DEBUG] Label già presente, dato ignorato:", label);
    return; // Non aggiungere dati duplicati
  }

  graficoDinamico.data.labels.push(label);
  graficoDinamico.data.datasets.forEach((dataset) => {
    dataset.data.push(data);
  });
  graficoDinamico.update();
}

  function removeFirstData() {
    graficoDinamico.data.labels.splice(0, 1);
    graficoDinamico.data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }

  const MAX_DATA_COUNT = 20;
  var socket = io.connect();

  //receive details from server
  socket.on("updateSensorData", function (msg) {
    console.log("Received sensorData: " + msg.toString());

    // Show only MAX_DATA_COUNT data
    if (graficoDinamico.data.labels.length > MAX_DATA_COUNT) {
      removeFirstData();
    }
    addData(msg.date, msg.temperature);
  });
});