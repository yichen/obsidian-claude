"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("api", {
  // Returns { text, chartPath? } — final response delivered via Promise return value
  sendChat: (messages) => electron.ipcRenderer.invoke("chat:send", messages),
  // Tool-call progress updates (informational, shown while waiting)
  onToolResult: (cb) => {
    const handler = (_e, data) => cb(data);
    electron.ipcRenderer.on("chat:tool-result", handler);
    return () => {
      electron.ipcRenderer.removeListener("chat:tool-result", handler);
    };
  },
  // Streaming tokens — subscribe for live text updates during final response
  onStreamToken: (cb) => {
    const handler = (_e, data) => cb(data);
    electron.ipcRenderer.on("chat:stream-token", handler);
    return () => {
      electron.ipcRenderer.removeListener("chat:stream-token", handler);
    };
  },
  dbQuery: (sql) => electron.ipcRenderer.invoke("db:query", sql),
  financeCommand: (command) => electron.ipcRenderer.invoke("finance:command", command)
});
