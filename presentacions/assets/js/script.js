// Carrega el fitxer extern JSON amb la llista de presentacions
async function loadPresentations() {
  try {
    const res = await fetch("assets/data/presentations.json");
    if (!res.ok) throw new Error("No s'ha pogut carregar presentations.json");
    return await res.json();
  } catch (err) {
    console.error("Error carregant presentacions:", err);
    return [];
  }
}

// Funció de cerca
const byQuery = (q) => (p) => {
  if (!q) return true;
  const hay = (p.title + " " + p.description + " " + (p.tags || []).join(" ")).toLowerCase();
  return hay.includes(q.toLowerCase());
};

// Renderitza la graella de targetes
function render(list) {
  const grid = document.getElementById("presentations-grid");
  grid.innerHTML = "";

  if (!list.length) {
    grid.innerHTML = `<p>No s'ha trobat cap presentació amb aquest filtre.</p>`;
    return;
  }

  list.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";

    const htmlLink = `${p.slug}.html`;
    const mdLink   = `${p.slug}.md`;

    card.innerHTML = `
      <h2>${p.title}</h2>
      <p>${p.description}</p>
      <div class="meta">${(p.tags || []).map(t => `#${t}`).join(" ")}</div>
      <div class="actions">
        <a class="button primary" href="${htmlLink}">Obrir presentació</a>
        <a class="button ghost"   href="${mdLink}" target="_blank" rel="noopener">Veure .md</a>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Inicialitza el portal
(async () => {
  const presentations = await loadPresentations();
  render(presentations);

  // Cerca en temps real
  const search = document.getElementById("search");
  search?.addEventListener("input", (e) => {
    render(presentations.filter(byQuery(e.target.value)));
  });
})();
