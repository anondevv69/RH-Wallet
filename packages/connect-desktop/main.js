"use strict";

const { app, BrowserWindow, ipcMain, shell, clipboard } = require("electron");
const path = require("path");
const { runOAuth, stageTelegramHandoff, copyToClipboard } = require("@rhwallet/connect");

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 640,
    resizable: false,
    title: "RH Agentic Connect",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
  mainWindow.setMenuBarVisibility(false);
}

function sendStatus(msg) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("oauth-status", msg);
  }
}

ipcMain.handle("connect-robinhood", async () => {
  try {
    sendStatus("Starting Robinhood login…");
    const tokens = await runOAuth({
      onStatus: (msg) => sendStatus(msg),
    });

    copyToClipboard(tokens.accessToken);
    sendStatus("OAuth complete — staging secure handoff to Telegram…");

    let handoff = null;
    let handoffError = null;
    try {
      handoff = await stageTelegramHandoff({
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      });
    } catch (err) {
      handoffError = err.message || String(err);
      sendStatus(`Telegram handoff unavailable: ${handoffError}`);
    }

    return {
      ok: true,
      accessToken: tokens.accessToken,
      expiresIn: tokens.expiresIn || null,
      handoff,
      handoffError,
      pasteCommand: `/connect_agentic ${tokens.accessToken}`,
    };
  } catch (err) {
    return { ok: false, error: err.message || String(err) };
  }
});

ipcMain.handle("copy-text", async (_event, text) => {
  clipboard.writeText(String(text || ""));
  return true;
});

ipcMain.handle("open-external", async (_event, url) => {
  if (typeof url === "string" && (url.startsWith("https://") || url.startsWith("http://") || url.startsWith("tg:"))) {
    await shell.openExternal(url);
    return true;
  }
  return false;
});

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
