let appSocket = null;
let appMessageHandler = null;
let wsStatusElement = null;

function setWsStatusElement(element) {
  wsStatusElement = element;
}

function updateWsStatus(text, className = "disconnected") {
  if (!wsStatusElement) return;
  wsStatusElement.textContent = text;
  wsStatusElement.className = `status-value ${className}`;
}

function setWsMessageHandler(handler) {
  appMessageHandler = handler;
}

function sendWsMessage(payload) {
  if (!appSocket || appSocket.readyState !== WebSocket.OPEN) {
    console.warn("WebSocket не подключен");
    return;
  }

  appSocket.send(JSON.stringify(payload));
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  appSocket = new WebSocket(wsUrl);

  appSocket.addEventListener("open", () => {
    updateWsStatus("подключено", "connected");
    console.log("WebSocket подключен");
  });

  appSocket.addEventListener("message", (event) => {
    try {
      const message = JSON.parse(event.data);
      if (typeof appMessageHandler === "function") {
        appMessageHandler(message);
      }
    } catch (error) {
      console.error("Ошибка разбора WebSocket сообщения:", error, event.data);
    }
  });

  appSocket.addEventListener("close", () => {
    updateWsStatus("отключено", "disconnected");
    console.warn("WebSocket отключен, переподключение через 2 секунды");
    setTimeout(connectWebSocket, 2000);
  });

  appSocket.addEventListener("error", (error) => {
    updateWsStatus("ошибка", "error");
    console.error("WebSocket ошибка:", error);
  });
}