// Load rules from JSON file
// content.js (or module imported by content script)
// shared or content.js
async function loadRules() {
  // Try storage first
  const stored = await browser.storage.local.get("rules");
  let settings = stored.rules;
  if (!settings) {
    // fallback: read bundled JSON and persist it so next time comes from storage
    const resp = await fetch(browser.runtime.getURL("settings/rules.json"));
    settings = await resp.json();
    await browser.storage.local.set({ rules: settings });
    console.log("Fallback: bundled rules saved to storage");
  }

  const systemInfoPatterns = [];
  const username = await getCurrentUsername();
  if (username) {
    systemInfoPatterns.push({
      pattern: `\\b${escapeRegExp(username)}\\b`,
      replacement: "username"
    });
  }
  const hostname = window.location.hostname;
  if (hostname) {
    systemInfoPatterns.push({
      pattern: `\\b${escapeRegExp(hostname)}\\b`,
      replacement: "hostname"
    });
  }

  return {
    sites: settings.sites || [],
    rules: [...(settings.rules || []), ...systemInfoPatterns]
  };
}


// Modify text based on the rules
function modifyText(text, rules) {
  let originalText = text;
  rules.forEach(rule => {
    const regex = new RegExp(rule.pattern, 'g');
    text = text.replace(regex, rule.replacement);
  });
  console.log("Original text:", originalText);
  console.log("Modified text:", text);
  return text;
}

document.addEventListener('paste', async (event) => {
  console.log("Paste event triggered.");
  
  // Prevent the default paste action to modify clipboard first
  event.preventDefault();
  
  // Get clipboard data
  const clipboardData = event.clipboardData || window.clipboardData;
  let pastedData = clipboardData.getData('Text'); // Get pasted content

  // Read rules from storage (fall back to bundled JSON if not present)
  const stored = await browser.storage.local.get("rules");
  let settings = stored.rules;
  if (!settings) {
    // fallback: load bundled file and save to storage so next time comes from storage
    const resp = await fetch(chrome.runtime.getURL("settings/rules.json"));
    settings = await resp.json();
    await browser.storage.local.set({ rules: settings });
  }

  // Check if current site is allowed to use the extension
  if (isAllowedSite(rulesData.sites)) {
    console.log("Current site is allowed:", window.location.href);
    const modifiedText = modifyText(pastedData, rulesData.rules);

    // Write the modified text back to the clipboard
    navigator.clipboard.writeText(modifiedText).then(() => {
      console.log("Modified text copied to clipboard:", modifiedText);

      // Manually trigger the paste on focused element
      // Get the active element
      const activeElement = document.activeElement;

      if (activeElement.tagName.toLowerCase() === 'textarea' || 
          (activeElement.tagName.toLowerCase() === 'input' && 
           activeElement.type === 'text')) {
       
        // Insert the modified text at the current cursor position
        const start = activeElement.selectionStart;
        const end = activeElement.selectionEnd;
        const currentValue = activeElement.value;

        // Update the input value
        activeElement.value = currentValue.substring(0, start) + modifiedText + currentValue.substring(end);
        
        // Set the cursor position
        activeElement.selectionStart = activeElement.selectionEnd = start + modifiedText.length;
      }
    }).catch(err => {
      console.error("Failed to write to clipboard: ", err);
    });
  } else {
    console.warn("Current site is not allowed:", window.location.href);
  }
});


// Utility function to escape regex characters
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Function to get the current username
async function getCurrentUsername() {
  return new Promise((resolve) => {
    resolve("username"); // Replace with actual logic, if possible
  });
}

// Check if current site is in the allowed list
function isAllowedSite(sites) {
  const currentUrl = window.location.href;
  return sites.some(site => new RegExp(site.replace(/\*/g, '.*')).test(currentUrl));
}
browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "test") {
        console.log("Received message from background script.");
        // Handle your logic here.
        sendResponse({ status: "success" });
    }
});
