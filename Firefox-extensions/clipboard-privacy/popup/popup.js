document.addEventListener('DOMContentLoaded', loadExistingData);

document.getElementById('addRuleForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const pattern = document.getElementById('pattern').value;
    const replacement = document.getElementById('replacement').value;
    addRule(pattern, replacement);
});

document.getElementById('addSiteForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const site = document.getElementById('site').value;
    addSite(site);
});

async function loadExistingData() {
    // Fetch rules and sites from storage (you might want to change how you load this)
    const data = await browser.storage.local.get("rules");
    
    // If the data does not exist, initialize it
    if (!data.rules) {
        data.rules = { sites: [], rules: [] }; 
    }

    // Display current rules
    const rulesTableBody = document.querySelector('#rulesTable tbody');
    rulesTableBody.innerHTML = ''; // Clear existing rows
    data.rules.rules.forEach((rule, index) => {
        const row = rulesTableBody.insertRow();
        row.insertCell(0).textContent = rule.pattern;
        row.insertCell(1).textContent = rule.replacement;
        
        const deleteCell = row.insertCell(2);
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.onclick = () => deleteRule(index);
        deleteCell.appendChild(deleteButton);
    });

    // Display current sites
    const sitesList = document.getElementById('sitesList');
    sitesList.innerHTML = ''; // Clear existing list items
    data.rules.sites.forEach(site => {
        const listItem = document.createElement('li');
        listItem.textContent = site;
        
        const deleteSiteButton = document.createElement('button');
        deleteSiteButton.textContent = 'Delete';
        deleteSiteButton.onclick = () => deleteSite(site);
        listItem.appendChild(deleteSiteButton);
        
        sitesList.appendChild(listItem);
    });
}

async function getStored() {
  const res = await browser.storage.local.get("rules");
  return res.rules || { sites: [], rules: [] };
}

async function addRule(pattern, replacement) {
  const data = await getStored();
  data.rules.push({ pattern, replacement });
  await browser.storage.local.set({ rules: data });
  loadExistingData();
}

async function deleteRule(index) {
  const data = await getStored();
  if (index >= 0 && index < data.rules.length) {
    data.rules.splice(index, 1);
    await browser.storage.local.set({ rules: data });
    loadExistingData();
  }
}

async function addSite(site) {
  if (!site) return;
  const data = await getStored();
  if (!data.sites.includes(site)) {
    data.sites.push(site);
    await browser.storage.local.set({ rules: data });
    loadExistingData();
  }
}

async function deleteSite(site) {
  const data = await getStored();
  const newSites = data.sites.filter(s => s !== site);
  if (newSites.length !== data.sites.length) {
    data.sites = newSites;
    await browser.storage.local.set({ rules: data });
    loadExistingData();
  }
}
