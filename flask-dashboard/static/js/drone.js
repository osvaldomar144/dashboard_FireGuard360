document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/drone");  // namespace definito in Flask

  socket.on("connect", () => {
    console.log("[WS] Connesso al namespace /overview");
  });

  socket.on("disconnect", () => {
    console.log("[WS] Disconnesso da /overview");
  });

});
