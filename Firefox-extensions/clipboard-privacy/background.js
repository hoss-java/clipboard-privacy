// Example to test communication
browser.runtime.onInstalled.addListener(() => {
    console.log("Extension installed. Sending test message to content script.");
    // Send a message when the extension is installed or at a specific event.
    browser.tabs.query({active: true, currentWindow: true}).then((tabs) => {
        browser.tabs.sendMessage(tabs[0].id, {action: "test"})
            .then(response => console.log(response.status))
            .catch(error => console.error("Error sending message:", error));
    });
});

browser.runtime.onInstalled.addListener(async () => {
  const s = await browser.storage.local.get("rulesData");
  if (!s.rulesData) {
    const url = browser.runtime.getURL("settings/rules.json");
    const resp = await fetch(url);
    const data = await resp.json();
    await browser.storage.local.set({ rulesData: data });
  }
});

// background.js (service worker)
browser.runtime.onInstalled.addListener(async () => {
  const s = await browser.storage.local.get("rules");
  if (!s.rules) {
    const url = browser.runtime.getURL("settings/rules.json");
    const resp = await fetch(url);
    const data = await resp.json();
    await browser.storage.local.set({ rules: data });
    console.log("Default rules saved to storage");
  } else {
    console.log("Rules already in storage — skipping initial save");
  }
});
