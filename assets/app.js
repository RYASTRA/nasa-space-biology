// OSDR explorer — client-side facets + search + sort over studies.json.
(() => {
  "use strict";

  const FACETS = [
    { key: "organisms", label: "Organism", path: (s) => s.subject.organisms },
    { key: "assay_types", label: "Assay type", path: (s) => s.assay.types },
    { key: "factor_types", label: "Factor type", path: (s) => s.factors.types },
    { key: "flight_programs", label: "Flight program", path: (s) => s.mission.flight_programs },
  ];
  const TOP_N = 12;

  const el = {
    facets: document.getElementById("facets"),
    results: document.getElementById("results"),
    search: document.getElementById("search"),
    count: document.getElementById("count"),
    sort: document.getElementById("sort"),
    clear: document.getElementById("clear"),
    toggle: document.getElementById("facet-toggle"),
  };

  const state = {
    studies: [],
    selected: {
      organisms: new Set(),
      assay_types: new Set(),
      factor_types: new Set(),
      flight_programs: new Set(),
    },
    query: "",
    sort: "newest",
    expanded: new Set(),
  };

  const first = (arr) => (arr && arr.length ? arr[0] : "");
  const esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
    );
  const anySelected = () => FACETS.some((f) => state.selected[f.key].size > 0) || state.query;

  // Full-text search over title + description via MiniSearch (vendored UMD global).
  let searchMatches = null; // Set<accession> | null (null = no active query)
  let searchOrder = null; // Map<accession, rank> | null (for relevance sort)
  let index = null;

  function matchesFacets(s, exceptKey) {
    for (const f of FACETS) {
      if (f.key === exceptKey) continue;
      const sel = state.selected[f.key];
      if (sel.size === 0) continue;
      const vals = f.path(s);
      if (!vals.some((v) => sel.has(v))) return false;
    }
    return true;
  }

  function matchesSearch(s) {
    return searchMatches === null || searchMatches.has(s.identity.accession);
  }

  function currentResults() {
    return state.studies.filter((s) => matchesFacets(s, null) && matchesSearch(s));
  }

  function sortStudies(list) {
    const dateKey = (s) => s.overview.release_date || "";
    const sorted = list.slice();
    if (state.sort === "newest") sorted.sort((a, b) => dateKey(b).localeCompare(dateKey(a)));
    else if (state.sort === "oldest") sorted.sort((a, b) => dateKey(a).localeCompare(dateKey(b)));
    else if (state.sort === "accession")
      sorted.sort((a, b) => a.identity.osd_num - b.identity.osd_num);
    else if (state.sort === "relevance" && searchOrder)
      sorted.sort(
        (a, b) =>
          (searchOrder.get(a.identity.accession) ?? 1e9) -
          (searchOrder.get(b.identity.accession) ?? 1e9),
      );
    return sorted;
  }

  function facetCounts(key) {
    // Count values over studies matching all OTHER facets + search (drill-down preview).
    const f = FACETS.find((x) => x.key === key);
    const counts = new Map();
    for (const s of state.studies) {
      if (!matchesFacets(s, key) || !matchesSearch(s)) continue;
      for (const v of new Set(f.path(s))) counts.set(v, (counts.get(v) || 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function renderFacets() {
    el.facets.querySelectorAll(".facet-group").forEach((n) => n.remove());
    for (const f of FACETS) {
      const values = facetCounts(f.key);
      const group = document.createElement("section");
      group.className = "facet-group";
      const expanded = state.expanded.has(f.key);
      const shown = expanded ? values : values.slice(0, TOP_N);
      group.innerHTML = `<h2>${f.label}</h2>`;
      const ul = document.createElement("ul");
      for (const [value, n] of shown) {
        const li = document.createElement("li");
        const checked = state.selected[f.key].has(value) ? "checked" : "";
        li.innerHTML =
          `<label><input type="checkbox" data-facet="${f.key}" value="${encodeURIComponent(value)}" ${checked}>` +
          `<span class="v">${esc(value)}</span><span class="n">${n}</span></label>`;
        ul.appendChild(li);
      }
      group.appendChild(ul);
      if (values.length > TOP_N) {
        const more = document.createElement("button");
        more.className = "more";
        more.textContent = expanded ? "Show less" : `Show ${values.length - TOP_N} more`;
        more.addEventListener("click", () => {
          if (expanded) state.expanded.delete(f.key);
          else state.expanded.add(f.key);
          renderFacets();
        });
        group.appendChild(more);
      }
      el.facets.appendChild(group);
    }
    el.clear.hidden = !anySelected();
  }

  function metaLine(s) {
    return [first(s.subject.organisms), first(s.assay.types), first(s.mission.names), s.overview.release_date]
      .filter(Boolean)
      .join(" · ");
  }

  function renderResults() {
    const results = sortStudies(currentResults());
    el.count.textContent =
      results.length === state.studies.length
        ? `${state.studies.length} studies`
        : `${results.length} of ${state.studies.length}`;
    el.results.innerHTML = "";
    const frag = document.createDocumentFragment();
    for (const s of results) {
      const row = document.createElement("article");
      row.className = "row";
      row.innerHTML =
        `<a class="title" href="study/${esc(s.identity.accession)}.html">${esc(s.overview.title)}</a>` +
        `<div class="meta">${esc(metaLine(s))}</div>` +
        `<span class="badge">${esc(s.identity.accession)}</span>`;
      frag.appendChild(row);
    }
    el.results.appendChild(frag);
    if (!results.length) {
      el.results.innerHTML = `<p class="empty">No studies match. <button id="empty-clear">Clear filters</button></p>`;
      const b = document.getElementById("empty-clear");
      if (b) b.addEventListener("click", clearAll);
    }
  }

  function rerender() {
    renderFacets();
    renderResults();
  }

  function clearAll() {
    for (const f of FACETS) state.selected[f.key].clear();
    state.query = "";
    el.search.value = "";
    onSearch(); // recompute searchMatches (Task 5); safe no-op in Task 4
    rerender();
  }

  function buildIndex() {
    index = new MiniSearch({
      idField: "id",
      fields: ["title", "description"],
      searchOptions: { boost: { title: 2 }, prefix: true, fuzzy: 0.2 },
    });
    index.addAll(
      state.studies.map((s) => ({
        id: s.identity.accession,
        title: s.overview.title,
        description: s.overview.description,
      })),
    );
  }

  function onSearch() {
    state.query = el.search.value.trim();
    if (!state.query) {
      searchMatches = null;
      searchOrder = null;
      return;
    }
    const hits = index.search(state.query);
    searchMatches = new Set(hits.map((h) => h.id));
    searchOrder = new Map(hits.map((h, i) => [h.id, i]));
  }

  function wire() {
    el.facets.addEventListener("change", (e) => {
      const cb = e.target;
      if (!cb.dataset || !cb.dataset.facet) return;
      const value = decodeURIComponent(cb.value);
      const sel = state.selected[cb.dataset.facet];
      if (cb.checked) sel.add(value);
      else sel.delete(value);
      rerender();
    });
    el.sort.addEventListener("change", () => {
      state.sort = el.sort.value;
      renderResults();
    });
    el.search.addEventListener("input", () => {
      onSearch();
      if (state.query && el.sort.value === "newest") {
        state.sort = "relevance";
        el.sort.value = "relevance";
      }
      rerender();
    });
    el.clear.addEventListener("click", clearAll);
    el.toggle.addEventListener("click", () => {
      const open = el.facets.classList.toggle("open");
      el.toggle.setAttribute("aria-expanded", String(open));
    });
  }

  async function init() {
    const res = await fetch("data/studies.json");
    state.studies = await res.json();
    buildIndex();
    wire();
    rerender();
  }

  init().catch((err) => {
    el.results.innerHTML = `<p class="empty">Failed to load studies: ${err}</p>`;
  });
})();
