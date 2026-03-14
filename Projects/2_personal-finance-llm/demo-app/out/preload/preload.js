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
  financeCommand: (command) => electron.ipcRenderer.invoke("finance:command", command),
  // Run a non-SELECT SQL statement (INSERT/UPDATE/DELETE)
  dbExecute: (sql) => electron.ipcRenderer.invoke("db:execute", sql),
  // Returns up to 3 recent chat query strings from session logs
  recentTopics: () => electron.ipcRenderer.invoke("finance:recent-topics"),
  // Parse a receipt text with AI and return structured fields
  parseReceipt: (text) => electron.ipcRenderer.invoke("finance:parse-receipt", text),
  // Generate a standard chart by type and return base64 data URL
  generateChart: (type, months) => electron.ipcRenderer.invoke("finance:generate-chart", type, months)
});
