"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("rhConnect", {
  connectRobinhood: () => ipcRenderer.invoke("connect-robinhood"),
  copyText: (text) => ipcRenderer.invoke("copy-text", text),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
  onStatus: (cb) => {
    const handler = (_event, msg) => cb(msg);
    ipcRenderer.on("oauth-status", handler);
    return () => ipcRenderer.removeListener("oauth-status", handler);
  },
});
