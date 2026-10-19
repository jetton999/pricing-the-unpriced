/* Greenmount corridor map — vanilla JS, Leaflet 1.9.4. */
(function () {
  "use strict";

  var ADMIN_PAGE = 50;
  var TIER_COLORS = ["#c8c3b8", "#f3c66b", "#e58a2d", "#a4290f"];

  function tier(n) { return n === 0 ? 0 : n < 10 ? 1 : n < 25 ? 2 : 3; }
  function tierLabel(t) { return ["0", "1–9", "10–24", "25+"][t]; }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") node.className = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else if (k.slice(0, 2) === "on") node.addEventListener(k.slice(2), attrs[k]);
        else node.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c == null) return;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  function fmtNum(v) {
    if (v == null || v === "") return "—";
    if (typeof v === "number") return v.toLocaleString();
    return String(v);
  }
  function fmtMoney(v) {
    if (v == null || v === "") return "—";
    if (typeof v !== "number") return String(v);
    return "$" + v.toLocaleString();
  }
  function fmtBool(v) { return v === true ? "yes" : v === false ? "no" : "—"; }
  function dash(v) { return (v == null || v === "") ? "—" : String(v); }

  function datePart(s) { return (s || "").slice(0, 10); }
  function yearOf(s) { return (s || "").slice(0, 4); }

  /* Human date label honouring date_precision. Returns {text, approx}. */
  function dateLabel(inc) {
    var p = inc.date_precision || "";
    var y = yearOf(inc.occurred_at);
    var d = datePart(inc.occurred_at);
    switch (p) {
      case "exact":   return { text: d, approx: false };
      case "year":    return { text: y, approx: false };
      case "circa":   return { text: "c. " + y, approx: true };
      case "decade":  return { text: y.slice(0, 3) + "0s", approx: true };
      case "range":
        var end = inc.occurred_at_end ? yearOf(inc.occurred_at_end) : "?";
        return { text: y + " – " + end, approx: true };
      case "unknown": return { text: "date unknown (" + y + ")", approx: true };
      default:        return { text: d, approx: false };
    }
  }

  function chip(text, cls) { return el("span", { class: "chip " + (cls || ""), text: text }); }

  /* Use categories (team list) and their colours; same palette as the team explorer page. */
  var USE_CATS = ["retail goods", "food & drink", "personal services", "automotive",
    "entertainment & assembly", "institutional & religious", "office",
    "production & light industry", "residential", "vacant"];
  var USE_COLORS = {
    "retail goods": "#2a78d6", "food & drink": "#eb6834", "personal services": "#1baf7a",
    "automotive": "#eda100", "entertainment & assembly": "#e87ba4",
    "institutional & religious": "#008300", "office": "#6250d6",
    "production & light industry": "#e34948", "residential": "#b9bdb8", "vacant": "#ffffff",
    "storefront (use not stated)": "#ffffff"
  };
  var STOREFRONT = "storefront (use not stated)";
  function gridUse(e) {   // a bare "store" names a shop front, not what it sold
    return e.use_subcategory === "store building (generic)" ? STOREFRONT : e.use_category;
  }
  var USE_DECADES = [];
  for (var dd = 1870; dd <= 2020; dd += 10) USE_DECADES.push(dd);
  var SOURCE_LABEL = {
    polk_directory: "Polk directory", permit_card: "permit card", sanborn: "Sanborn map",
    nr_inventory: "NR inventory", dhcd_1970s: "1970s DHCD scan", current_2026: "2026 tenant check"
  };
  function sourceLabel(src) {
    if (src.indexOf("sponsor:") === 0) return "sponsor · " + src.slice(8);
    return SOURCE_LABEL[src] || src;
  }
  function swatch(cat) {
    return el("i", { class: "sw" + (cat === "vacant" ? " vac" : cat === STOREFRONT ? " ring" : ""), style: "background:" + (USE_COLORS[cat] || "#eee") });
  }
  function useChip(cat, text, weak) {
    return el("span", { class: "ucat" + (weak ? " weak" : "") }, [swatch(cat), text || cat]);
  }
  function yearSpan(a, b) { a = String(a); b = String(b); return a === b ? a : a + "–" + b; }

  /* ---------------------------------------------------------------- map */
  var map = L.map("map", { preferCanvas: true }).setView([39.318, -76.609], 15);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var markerById = {};
  var pointsLayer = null;
  var selectedLayer = L.layerGroup().addTo(map);   // lot + buildings of selected property
  var lotsLayer = L.geoJSON(null, {
    style: { color: "#5b6fb5", weight: 1, fillOpacity: 0.06 },
    onEachFeature: function (f, layer) {
      layer.on("click", function () { selectProperty(f.properties.id); });
      layer.bindTooltip(f.properties.address);
    }
  });
  var hoodsLayer = L.geoJSON(null, {
    style: { color: "#2e7d32", weight: 2, dashArray: "6 4", fillOpacity: 0.03 },
    onEachFeature: function (f, layer) { layer.bindTooltip(f.properties.name); }
  });
  // Proposed first focus area: a working outline, drawn under the markers and not clickable.
  var focusLayer = L.geoJSON(null, {
    style: { color: "#b03fd6", weight: 3, fillOpacity: 0.04 },
    interactive: false
  }).addTo(map);
  var focusOnly = false;
  var lotsLoaded = {};
  var selectedId = null;
  var baseStats = "";

  var useMode = false;          // colour markers by recorded use instead of curated depth
  var useDecade = "dominant";   // "dominant" or a decade such as "1910"

  /* null = outside the frontage the extractor covers; "" = no record in that decade */
  function useOf(p) {
    if (!p.use_history) return null;
    if (useDecade === "dominant") return p.use_dominant || "";
    var list = p.use_decades[useDecade];
    return list && list.length ? list[0] : "";
  }

  function markerStyle(f, selected) {
    if (useMode) return useMarkerStyle(f, selected);
    var t = tier(f.properties.curated_count);
    var dim = focusOnly && !f.properties.in_focus && !selected;
    return {
      radius: selected ? 9 : (t === 0 ? 4 : 5 + t),
      fillColor: TIER_COLORS[t],
      color: selected ? "#111" : "#3a3631",
      weight: selected ? 2.5 : 0.8,
      fillOpacity: dim ? 0.12 : 0.9,
      opacity: dim ? 0.2 : 1,
      dashArray: null
    };
  }

  function useMarkerStyle(f, selected) {
    var u = useOf(f.properties);
    if (u === null) {
      return { radius: selected ? 8 : 3, fillColor: "#c8c3b8", color: selected ? "#111" : "#c8c3b8",
               weight: selected ? 2.5 : 0.5, fillOpacity: 0.3, opacity: 0.4, dashArray: null };
    }
    if (u === "") {   // silence in the sources is not vacancy: hollow, dashed
      return { radius: selected ? 9 : 5, fillColor: "#ffffff", color: selected ? "#111" : "#6f6a62",
               weight: selected ? 2.5 : 1.2, fillOpacity: 0.6, opacity: 0.9, dashArray: "2 2" };
    }
    if (u === STOREFRONT) {
      return { radius: selected ? 10 : 6, fillColor: "#ffffff", color: selected ? "#111" : USE_COLORS["retail goods"],
               weight: selected ? 2.5 : 2.2, fillOpacity: 0.9, opacity: 1, dashArray: null };
    }
    return { radius: selected ? 10 : 7, fillColor: USE_COLORS[u],
             color: selected ? "#111" : (u === "vacant" ? "#3a3631" : "#ffffff"),
             weight: selected ? 2.5 : (u === "vacant" ? 1.6 : 1), fillOpacity: 0.95, opacity: 1, dashArray: null };
  }

  function tooltipText(f) {
    var p = f.properties;
    var base = p.address + " · " + p.curated_count + " curated";
    if (!useMode) return base;
    if (!p.use_history) return p.address + " · outside the frontage the extractor covers";
    if (useDecade === "dominant") return p.address + " · use in the most decades: " + (p.use_dominant || "none coded");
    var list = p.use_decades[useDecade];
    return p.address + " · " + useDecade + "s: " + (list && list.length ? list.join(", ") : "no record (not the same as vacant)");
  }

  function restyleMarkers() {
    if (!pointsLayer) return;
    pointsLayer.eachLayer(function (m) {
      m.setStyle(markerStyle(m.feature, m.feature.properties.id === selectedId));
      var u = useMode ? useOf(m.feature.properties) : null;
      if (useMode ? u : tier(m.feature.properties.curated_count) > 0) m.bringToFront();
    });
    if (selectedId != null && markerById[selectedId]) markerById[selectedId].bringToFront();
  }

  function paintStats() {
    var text = baseStats;
    if (useMode && pointsLayer) {
      var nUse = 0, nFront = 0;
      pointsLayer.eachLayer(function (m) {
        var u = useOf(m.feature.properties);
        if (u !== null) { nFront++; if (u) nUse++; }
      });
      document.getElementById("stats").textContent = nFront + " mapped frontage buildings · " + nUse + " with a recorded use " +
        (useDecade === "dominant" ? "(the use found in the most decades)" : "in the " + useDecade + "s");
      return;
    }
    if (focusOnly && pointsLayer) {
      var n = 0, withHistory = 0;
      pointsLayer.eachLayer(function (m) {
        var p = m.feature.properties;
        if (p.in_focus) { n++; if (p.curated_count > 0) withHistory++; }
      });
      text = n + " mapped in the focus area · " + withHistory + " with curated history";
    }
    document.getElementById("stats").textContent = text;
  }

  fetch("/api/properties").then(function (r) { return r.json(); }).then(function (gj) {
    pointsLayer = L.geoJSON(gj, {
      pointToLayer: function (f, latlng) {
        var m = L.circleMarker(latlng, markerStyle(f, false));
        m.feature = f;
        markerById[f.properties.id] = m;
        return m;
      },
      onEachFeature: function (f, layer) {
        layer.bindTooltip(function () { return tooltipText(f); });
        layer.on("click", function () { selectProperty(f.properties.id); });
      }
    }).addTo(map);
    // Bring deeper properties to the front so they aren't hidden under tier-0 dots.
    pointsLayer.eachLayer(function (m) { if (tier(m.feature.properties.curated_count) > 0) m.bringToFront(); });

    var tiers = [0, 0, 0, 0];
    gj.features.forEach(function (f) { tiers[tier(f.properties.curated_count)]++; });
    baseStats = gj.features.length + " mapped properties · " +
      (tiers[1] + tiers[2] + tiers[3]) + " mapped with curated history";
    paintStats();
  }).catch(function (e) {
    document.getElementById("stats").textContent = "failed to load /api/properties: " + e;
  });

  fetch("/api/summary").then(function (r) { return r.json(); }).then(function (s) {
    (s.notes || []).forEach(function (n) { console.info("[data note] " + n); });
  });

  /* ------------------------------------------------------ layer toggles */
  fetch("/api/focus-area").then(function (r) { return r.json(); }).then(function (gj) {
    if (gj.features.length) { focusLayer.addData(gj); focusLayer.bringToBack(); return; }
    ["toggle-focus", "toggle-focus-only"].forEach(function (id) {
      document.getElementById(id).disabled = true;
    });
  });
  document.getElementById("toggle-focus").addEventListener("change", function (e) {
    if (e.target.checked) { focusLayer.addTo(map); focusLayer.bringToBack(); }
    else map.removeLayer(focusLayer);
  });
  document.getElementById("toggle-focus-only").addEventListener("change", function (e) {
    focusOnly = e.target.checked;
    restyleMarkers();
    if (focusOnly && focusLayer.getLayers().length) map.fitBounds(focusLayer.getBounds().pad(0.08));
    paintStats();
  });
  document.getElementById("toggle-lots").addEventListener("change", function (e) {
    if (e.target.checked) { lotsLayer.addTo(map); loadVisibleLots(); }
    else map.removeLayer(lotsLayer);
  });
  map.on("moveend", function () { if (map.hasLayer(lotsLayer)) loadVisibleLots(); });

  function loadVisibleLots() {
    if (!pointsLayer) return;
    var b = map.getBounds();
    var ids = [];
    pointsLayer.eachLayer(function (m) {
      var id = m.feature.properties.id;
      if (!lotsLoaded[id] && b.contains(m.getLatLng())) ids.push(id);
    });
    if (!ids.length) return;
    if (ids.length > 600) ids = ids.slice(0, 600);
    ids.forEach(function (id) { lotsLoaded[id] = true; });
    fetch("/api/lots?ids=" + ids.join(",")).then(function (r) { return r.json(); })
      .then(function (gj) { lotsLayer.addData(gj); });
  }

  var hoodsFetched = false;
  document.getElementById("toggle-hoods").addEventListener("change", function (e) {
    if (!e.target.checked) { map.removeLayer(hoodsLayer); return; }
    hoodsLayer.addTo(map);
    if (hoodsFetched) return;
    hoodsFetched = true;
    fetch("/api/neighborhoods").then(function (r) { return r.json(); }).then(function (gj) {
      if (!gj.features.length) {
        console.info("[neighborhoods] no parseable bounds in this export; nothing to draw.");
        var label = e.target.parentNode;
        label.appendChild(el("span", { class: "muted", text: " (no bounds in export)" }));
        return;
      }
      hoodsLayer.addData(gj);
    });
  });

  /* Colour by use: the team extractor's spans, one decade at a time. */
  var useToggle = document.getElementById("toggle-use");
  var useSelect = document.getElementById("use-decade");
  var usePrev = document.getElementById("use-prev");
  var useNext = document.getElementById("use-next");
  useSelect.appendChild(el("option", { value: "dominant", text: "most decades" }));
  USE_DECADES.forEach(function (d) { useSelect.appendChild(el("option", { value: String(d), text: d + "s" })); });
  buildUseLegend();
  function setUseControls() {
    [useSelect, usePrev, useNext].forEach(function (n) { n.disabled = !useMode; });
    document.getElementById("legend-tier").hidden = useMode;
    document.getElementById("legend-use").hidden = !useMode;
    restyleMarkers();
    paintStats();
  }
  function stepDecade(k) {
    var i = useSelect.selectedIndex + k;
    if (i < 0 || i >= useSelect.options.length) return;
    useSelect.selectedIndex = i;
    useDecade = useSelect.value;
    setUseControls();
  }
  useToggle.addEventListener("change", function (e) { useMode = e.target.checked; setUseControls(); });
  useSelect.addEventListener("change", function () { useDecade = useSelect.value; setUseControls(); });
  usePrev.addEventListener("click", function () { stepDecade(-1); });
  useNext.addEventListener("click", function () { stepDecade(1); });
  fetch("/api/summary").then(function (r) { return r.json(); }).then(function (s) {
    if (!s.use_history_properties) {
      useToggle.disabled = true;
      useToggle.parentNode.appendChild(el("span", { class: "muted", text: " (run team/extractor)" }));
    }
  });

  function buildUseLegend() {
    var box = document.getElementById("legend-use");
    box.appendChild(el("div", { class: "legend-title", text: "Recorded use" }));
    USE_CATS.forEach(function (c) {
      box.appendChild(el("div", {}, [el("i", { class: c === "vacant" ? "vac" : "", style: "background:" + USE_COLORS[c] }), " " + c]));
      if (c === "retail goods") box.appendChild(el("div", {}, [el("i", { class: "ring" }), " storefront, use not stated"]));
    });
    box.appendChild(el("div", {}, [el("i", { class: "hollow" }), " no record that decade"]));
    box.appendChild(el("div", { class: "muted" }, [el("i", { style: "background:#c8c3b8;opacity:.4" }), " outside the frontage"]));
  }

  /* ----------------------------------------------------------- search */
  var qInput = document.getElementById("q");
  var resultsEl = document.getElementById("results");
  var searchTimer = null;
  var activeIdx = -1;
  var lastResults = [];

  qInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    var q = qInput.value.trim();
    if (q.length < 2) { hideResults(); return; }
    searchTimer = setTimeout(function () { runSearch(q); }, 150);
  });
  qInput.addEventListener("keydown", function (e) {
    if (resultsEl.hidden) return;
    if (e.key === "ArrowDown") { activeIdx = Math.min(activeIdx + 1, lastResults.length - 1); paintActive(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { activeIdx = Math.max(activeIdx - 1, 0); paintActive(); e.preventDefault(); }
    else if (e.key === "Enter") { if (lastResults[activeIdx >= 0 ? activeIdx : 0]) pickResult(lastResults[activeIdx >= 0 ? activeIdx : 0]); e.preventDefault(); }
    else if (e.key === "Escape") hideResults();
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".search")) hideResults();
  });

  function hideResults() { resultsEl.hidden = true; resultsEl.innerHTML = ""; activeIdx = -1; }
  function paintActive() {
    Array.prototype.forEach.call(resultsEl.children, function (li, i) {
      li.classList.toggle("active", i === activeIdx);
    });
  }
  function runSearch(q) {
    fetch("/api/search?q=" + encodeURIComponent(q)).then(function (r) { return r.json(); })
      .then(function (data) {
        lastResults = data.results || [];
        resultsEl.innerHTML = "";
        activeIdx = -1;
        if (!lastResults.length) {
          resultsEl.appendChild(el("li", { class: "muted", text: "no matches" }));
        }
        lastResults.forEach(function (res) {
          var li = el("li", { onclick: function () { pickResult(res); } }, [
            el("span", { class: "kind", text: res.match_type }),
            el("span", { text: res.label }),
            res.match_type !== "address" ? el("div", { class: "addr", text: res.address }) : null,
            el("span", { class: "addr", text: "  · " + res.curated_count + " curated" })
          ]);
          resultsEl.appendChild(li);
        });
        resultsEl.hidden = false;
      });
  }
  function pickResult(res) {
    hideResults();
    qInput.value = res.label;
    if (res.lat != null && res.lng != null) map.flyTo([res.lat, res.lng], Math.max(map.getZoom(), 17), { duration: 0.6 });
    selectProperty(res.property_id);
  }

  /* ---------------------------------------------------------- sidebar */
  var sidebar = document.getElementById("sidebar");
  var bodyEl = document.getElementById("sidebar-body");
  var emptyEl = document.getElementById("sidebar-empty");

  function selectProperty(id) {
    if (selectedId != null && markerById[selectedId]) {
      markerById[selectedId].setStyle(markerStyle(markerById[selectedId].feature, false));
    }
    selectedId = id;
    if (markerById[id]) {
      markerById[id].setStyle(markerStyle(markerById[id].feature, true));
      markerById[id].bringToFront();
    }
    bodyEl.innerHTML = "";
    bodyEl.appendChild(el("p", { class: "muted", text: "loading property " + id + "…" }));
    emptyEl.hidden = true;
    bodyEl.hidden = false;
    sidebar.classList.remove("empty");
    sidebar.scrollTop = 0;

    fetch("/api/properties/" + id).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (d) {
      if (selectedId !== id) return; // user clicked elsewhere meanwhile
      renderDetail(d);
      drawSelectedGeometry(d);
    }).catch(function (e) {
      bodyEl.innerHTML = "";
      bodyEl.appendChild(el("p", { class: "none", text: "could not load property " + id + ": " + e.message }));
    });
  }

  function drawSelectedGeometry(d) {
    selectedLayer.clearLayers();
    if (d.lot_polygon) {
      L.geoJSON(d.lot_polygon, { style: { color: "#111", weight: 2, fillOpacity: 0.05, dashArray: "4 3" } }).addTo(selectedLayer);
    }
    if (d.building_polygons && d.building_polygons.features.length) {
      L.geoJSON(d.building_polygons, { style: { color: "#a4290f", weight: 1.5, fillOpacity: 0.18 } }).addTo(selectedLayer);
    }
  }

  function section(title, count, body) {
    var h = el("h3", {}, [title, count != null ? el("span", { class: "count", text: count }) : null]);
    return [h, body];
  }
  function noneNote(what) { return el("p", { class: "none", text: "none in export" + (what ? " (" + what + ")" : "") }); }

  function renderDetail(d) {
    var f = d.fields;
    var t = tier(d.counts.curated);
    bodyEl.innerHTML = "";

    bodyEl.appendChild(el("h2", { text: f.address || ("property " + d.id) }));
    bodyEl.appendChild(el("div", {}, [
      el("span", { class: "tier-chip tier-" + t, text: d.counts.curated + " curated (" + tierLabel(t) + ")" }),
      " ",
      el("span", { class: "muted", text: d.counts.administrative + " administrative · id " + d.id +
        (f.blocklot ? " · blocklot " + f.blocklot : "") })
    ]));

    // Key fields
    var kv = el("table", { class: "kv" });
    [
      ["Owner", dash(f.owner_name) + (f.owner_type ? " (" + f.owner_type + ")" : "")],
      ["Zoning", dash(f.zoning_code)],
      ["Year built", f.year_built ? String(f.year_built) : "—"],
      ["Structure sqft", fmtNum(f.structure_sqft)],
      ["Dwelling units", fmtNum(f.dwelling_units)],
      ["Stories", fmtNum(f.num_stories)],
      ["Assessed value", fmtMoney(f.assessed_value)],
      ["Last sale", (f.last_sale_price != null ? fmtMoney(f.last_sale_price) : "—") + (f.last_sale_date ? " on " + f.last_sale_date : "")],
      ["Vacant", fmtBool(f.vacancy_indicator) + (f.vacant_notice_status ? " · notice: " + f.vacant_notice_status : "")],
      ["City owned", fmtBool(f.city_owned)],
      ["Active business", fmtBool(f.has_active_business)],
      ["Historic district", dash(f.historic_district)],
      ["Census tract", dash(f.census_tract)],
      ["Block side", dash(f.block_side_id)],
      ["Permits / violations (12mo)", fmtNum(f.active_permit_count) + " / " + fmtNum(f.violations_12mo_count)],
      ["Fair market rent (2br)", fmtMoney(f.fair_market_rent_2br)],
      ["Coordinates", f.latitude != null ? f.latitude + ", " + f.longitude : "— (not mapped)"]
    ].forEach(function (row) {
      kv.appendChild(el("tr", {}, [el("th", { text: row[0] }), el("td", { text: row[1] })]));
    });
    bodyEl.appendChild(kv);

    var allFieldsBtn = el("button", { class: "btn", text: "show all " + Object.keys(f).length + " columns" });
    var allFields = el("table", { class: "kv", hidden: "" });
    Object.keys(f).sort().forEach(function (k) {
      var v = f[k];
      allFields.appendChild(el("tr", {}, [el("th", { text: k }),
        el("td", { text: v == null || v === "" ? "—" : (typeof v === "object" ? JSON.stringify(v) : String(v)) })]));
    });
    allFieldsBtn.addEventListener("click", function () {
      allFields.hidden = !allFields.hidden;
      allFieldsBtn.textContent = allFields.hidden ? "show all " + Object.keys(f).length + " columns" : "hide columns";
    });
    bodyEl.appendChild(el("p", {}, [allFieldsBtn]));
    bodyEl.appendChild(allFields);

    // Use history (team extractor; frontage only)
    if (d.use_history) {
      section("Use history (team extractor)", d.use_history.spans.length + " spans · " + d.use_history.evidence.length + " records",
        renderUseHistory(d.use_history)).forEach(function (n) { bodyEl.appendChild(n); });
    }

    // History timeline (curated, oldest first)
    var cur = d.incidents.curated;
    var hist = section("History (curated)", cur.length + (d.counts.roster ? " · " + d.counts.roster + " roster" : ""),
      cur.length ? renderTimeline(cur) : noneNote("no hand-researched records at this address"));
    hist.forEach(function (n) { bodyEl.appendChild(n); });

    // Administrative feed (newest first, paged)
    var adm = d.incidents.administrative;
    var feedWrap = el("div");
    if (!adm.length) feedWrap.appendChild(noneNote());
    else {
      var list = el("ul", { class: "feed" });
      feedWrap.appendChild(list);
      var shown = 0;
      var more = el("button", { class: "btn" });
      function showAdmin(n) {
        adm.slice(shown, shown + n).forEach(function (inc) { list.appendChild(renderFeedItem(inc)); });
        shown = Math.min(adm.length, shown + n);
        more.textContent = "show all (" + (adm.length - shown) + " more)";
        more.hidden = shown >= adm.length;
      }
      more.addEventListener("click", function () { showAdmin(adm.length); });
      showAdmin(ADMIN_PAGE);
      feedWrap.appendChild(el("p", {}, [more]));
    }
    section("Administrative feed", adm.length, feedWrap).forEach(function (n) { bodyEl.appendChild(n); });

    // People & businesses
    var subs = d.subjects;
    var subWrap;
    if (!subs.length) subWrap = noneNote();
    else {
      subWrap = el("ul", { class: "subjects-list" });
      subs.forEach(function (s) {
        var rels = Object.keys(s.relationships).map(function (k) {
          return k + (s.relationships[k] > 1 ? " ×" + s.relationships[k] : "");
        }).join(", ");
        var li = el("li", {}, [
          el("b", { text: s.name }), " ",
          chip(s.kind || "subject"),
          el("div", { class: "rel", text: rels })
        ]);
        if (s.other_property_ids.length) {
          var also = el("div", { class: "also" }, ["also linked to: "]);
          s.other_property_ids.slice(0, 8).forEach(function (pid, i) {
            if (i) also.appendChild(document.createTextNode(", "));
            also.appendChild(el("a", { href: "#", text: "property " + pid, onclick: function (e) {
              e.preventDefault(); goTo(pid);
            } }));
          });
          if (s.other_property_ids.length > 8) also.appendChild(document.createTextNode(" +" + (s.other_property_ids.length - 8) + " more"));
          li.appendChild(also);
        }
        subWrap.appendChild(li);
      });
    }
    section("People & businesses", subs.length, subWrap).forEach(function (n) { bodyEl.appendChild(n); });

    // Registered IP
    var ips = d.registered_ips;
    var ipWrap;
    if (!ips.length) ipWrap = noneNote();
    else {
      ipWrap = el("ul", { class: "plain" });
      ips.forEach(function (ip) {
        ipWrap.appendChild(el("li", {}, [
          chip(ip.ip_type), el("b", { text: ip.title || ip.number }),
          el("div", { class: "muted", text: [ip.number, ip.status, ip.owner_name].filter(Boolean).join(" · ") }),
          el("div", { class: "muted", text: "filed " + dash(ip.filing_date) + (ip.grant_date ? ", granted " + ip.grant_date : "") +
            " · " + ip.source + " · match " + dash(ip.match_confidence) })
        ]));
      });
    }
    section("Registered IP", ips.length, ipWrap).forEach(function (n) { bodyEl.appendChild(n); });

    // Grant program matches
    var grants = d.grant_program_matches;
    var gWrap;
    if (!grants.length) gWrap = noneNote();
    else {
      gWrap = el("ul", { class: "plain" });
      grants.forEach(function (g) {
        gWrap.appendChild(el("li", {}, [
          chip(g.category), el("b", { text: g.program_name }),
          g.amount_cap ? el("span", { class: "muted", text: " · cap " + g.amount_cap }) : null,
          el("div", { class: "muted", text: g.summary }),
          g.matched_reason ? el("div", { class: "muted", text: "matched: " + g.matched_reason }) : null
        ]));
      });
    }
    section("Grant program matches", grants.length, gWrap).forEach(function (n) { bodyEl.appendChild(n); });

    // Baseline snapshots
    var bl = d.baseline_snapshots;
    var bWrap;
    if (!bl.length) bWrap = noneNote("this property was not in the July 2026 baseline");
    else {
      bWrap = el("div");
      bWrap.appendChild(el("p", { class: "muted", text: "captured " + bl.map(function (b) { return b.captured_on; }).join(" and ") }));
      var tbl = el("table", { class: "baseline" });
      var head = el("tr", {}, [el("th", { text: "field" })]);
      bl.forEach(function (b) { head.appendChild(el("th", { text: b.captured_on })); });
      tbl.appendChild(head);
      // Omitted: avm_estimate, building_condition, vacant_notice_status (blank in every snapshot)
      // and sale_count, public_investment_total (0 in every snapshot). See DATA_DICTIONARY.md.
      ["assessed_value", "owner_name", "last_sale_price", "last_sale_date",
       "incident_count", "violations_12mo_count", "active_permit_count", "vacancy_indicator",
       "receivership_status", "tax_certificate_active", "registered_ip_count",
       "cdbg_investment_total", "hmda_loan_count", "hmda_median_value",
       "hmda_denial_rate", "market_typology"].forEach(function (k) {
        var tr = el("tr", {}, [el("th", { text: k })]);
        bl.forEach(function (b) {
          var v = b[k];
          tr.appendChild(el("td", { class: typeof v === "number" ? "num" : "", text: v === true ? "yes" : v === false ? "no" : dash(v) }));
        });
        tbl.appendChild(tr);
      });
      bWrap.appendChild(tbl);
    }
    section("Baseline snapshots", bl.length, bWrap).forEach(function (n) { bodyEl.appendChild(n); });
  }

  function evidenceItem(e) {
    var text = e.text || "(no text)";
    var body;
    if (e.sensitive) {
      body = summaryNode({ summary: text, sensitivity: "flagged in the source record" }, "summary");
    } else {
      body = el("div", { class: "summary", text: (e.business ? e.business + " — " : "") + text });
    }
    var meta = el("div", { class: "meta" }, [
      chip(sourceLabel(e.source)),
      e.use_category ? useChip(e.use_category, e.use_subcategory ? e.use_category + " · " + e.use_subcategory : e.use_category)
                     : chip("not coded to a use"),
      e.basis === "inferred" ? chip("address inferred: " + e.address_method, "ev-inferred") : null
    ]);
    var ref = el("div", { class: "src-ref" });
    var inc = /^incident (\d+)$/.exec(e.source_ref || "");
    if (inc) {   // a sponsor record: jump to it in the curated history below
      ref.appendChild(el("a", { href: "#", text: e.source_ref, title: "show this record in History (curated)", onclick: function (ev) {
        ev.preventDefault();
        var target = document.getElementById("inc-" + inc[1]);
        if (!target) return;
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        target.classList.remove("flash"); void target.offsetWidth; target.classList.add("flash");
      } }));
    } else {
      ref.appendChild(document.createTextNode(e.source_ref));
    }
    if (e.url) {
      ref.appendChild(document.createTextNode(" · "));
      ref.appendChild(el("a", { href: e.url, target: "_blank", rel: "noopener", text: "open source" }));
    }
    return el("li", {}, [el("span", { class: "when", text: e.year != null ? String(e.year) : "undated" }), meta, body, ref]);
  }

  function evidenceList(items, limit) {
    var wrap = el("div");
    var ul = el("ul", { class: "evlist" });
    wrap.appendChild(ul);
    var shown = 0;
    var more = el("button", { class: "btn" });
    function show(n) {
      items.slice(shown, shown + n).forEach(function (e) { ul.appendChild(evidenceItem(e)); });
      shown = Math.min(items.length, shown + n);
      more.textContent = "show all (" + (items.length - shown) + " more)";
      more.hidden = shown >= items.length;
    }
    more.addEventListener("click", function () { show(items.length); });
    show(limit || items.length);
    wrap.appendChild(el("p", {}, [more]));
    return wrap;
  }

  function toggleBlock(label, build) {
    var btn = el("button", { class: "btn small", text: label });
    var box = el("div", { hidden: "" });
    var built = false;
    btn.addEventListener("click", function () {
      if (!built) { box.appendChild(build()); built = true; }
      box.hidden = !box.hidden;
      btn.classList.toggle("on", !box.hidden);
    });
    return [btn, box];
  }

  function renderUseHistory(h) {
    var wrap = el("div", { class: "use-history" });
    var byIdx = {};
    h.evidence.forEach(function (e) { byIdx[e.idx] = e; });

    wrap.appendChild(el("p", { class: "muted small", text:
      "Coded by team/extractor from the sponsor's curated records, Polk directories (1901–23), " +
      "permit cards (1924–61), Sanborn sheets (1915, 1928, 1953), the National Register inventory, " +
      "1970s DHCD scans and a 2026 tenant check. \u201cAddress inferred\u201d means the number came " +
      "through the York Road renumbering or a neighbouring house number. Open the source before citing." }));

    if (h.proven.length) {
      var pv = el("div", { class: "use-proven" });
      h.proven.forEach(function (p) {
        pv.appendChild(useChip(p.use_category, p.use_category + " " + yearSpan(p.first_year, p.last_year) +
          " · " + p.n_decades + (p.n_decades === 1 ? " decade" : " decades"), p.strength !== "proven"));
      });
      wrap.appendChild(pv);
      wrap.appendChild(el("p", { class: "muted small", text: "Solid chips: the use appears in two or more decades. Faded: a single mention." }));
    }

    // Decade grid: one row per use, one column per decade; click a cell for its records.
    var counts = {}, any = {};
    h.evidence.forEach(function (e) {
      if (e.decade == null) return;
      any[e.decade] = (any[e.decade] || 0) + 1;
      var g = gridUse(e);
      if (!g) return;
      counts[g] = counts[g] || {};
      counts[g][e.decade] = (counts[g][e.decade] || 0) + 1;
    });
    var cats = USE_CATS.slice(0, 1).concat([STOREFRONT], USE_CATS.slice(1)).filter(function (c) { return counts[c]; });
    var cellBox = el("div", { class: "cell-detail" });
    var tbl = el("table", { class: "decgrid" });
    var head = el("tr", {}, [el("th")]);
    USE_DECADES.forEach(function (d) {
      head.appendChild(el("th", { class: "dh", title: d + "s", text: String(d).slice(2) }));
    });
    tbl.appendChild(head);
    var activeCell = null;
    function addRow(label, cat, data) {
      var tr = el("tr", {}, [el("th", { text: label === STOREFRONT ? "storefront (use?)" : label, title: label })]);
      USE_DECADES.forEach(function (d) {
        var n = data[d] || 0;
        var attrs = { title: d + "s · " + label + " · " + n + (n === 1 ? " record" : " records") };
        var td = el("td", attrs);
        if (n) {
          td.className = "on" + (cat === "vacant" ? " vac" : cat === STOREFRONT ? " ring" : "");
          td.style.background = cat ? USE_COLORS[cat] : "#8a8378";
          td.style.opacity = n >= 3 ? 1 : n === 2 ? 0.7 : 0.45;
          td.addEventListener("click", function () {
            if (activeCell) activeCell.classList.remove("picked");
            activeCell = td; td.classList.add("picked");
            var rowsHere = h.evidence.filter(function (e) {
              return e.decade === d && (cat ? gridUse(e) === cat : true);
            });
            cellBox.innerHTML = "";
            cellBox.appendChild(el("div", { class: "cell-title" }, [
              cat ? swatch(cat) : null, d + "s · " + label + " · " + rowsHere.length + (rowsHere.length === 1 ? " record" : " records")]));
            cellBox.appendChild(evidenceList(rowsHere, 12));
          });
        }
        tr.appendChild(td);
      });
      tbl.appendChild(tr);
    }
    cats.forEach(function (c) { addRow(c, c, counts[c]); });
    addRow("any record", "", any);
    wrap.appendChild(tbl);
    wrap.appendChild(el("p", { class: "muted small", text: "Darker = more records in that decade. A blank decade means no source " +
      "has been read for it yet, not that the building stood empty. Click a cell for its records." }));
    wrap.appendChild(cellBox);

    if (h.silence) {
      var si = h.silence;
      wrap.appendChild(el("p", { class: "small" }, [
        el("b", { text: "Coverage: " + si.status }), " · " + si.decades_all_sources + " decades with a coded use (sponsor records alone: " +
        si.decades_sponsor_only + ")" + (si.gap_decades ? " · gaps: " + si.gap_decades.split(" ").map(function (g) { return g + "s"; }).join(", ") : "")
      ]));
      if (si.what_would_fill_it) wrap.appendChild(el("p", { class: "muted small", text: "To fill the gaps: " + si.what_would_fill_it }));
    }

    // Spans, oldest first
    var ul = el("ul", { class: "spans" });
    h.spans.forEach(function (sp) {
      var li = el("li", { style: "border-left-color:" + (sp.use_category === "vacant" ? "#3a3631" : (USE_COLORS[sp.use_category] || "#ccc")) }, [
        el("span", { class: "when", text: yearSpan(sp.start_year, sp.end_year) }),
        " ", useChip(sp.use_category, sp.use_category + (sp.subcategories ? " · " + sp.subcategories : "")),
        sp.occupant ? el("div", { class: "occ", text: sp.occupant }) : null,
        el("div", { class: "meta muted small", text: [sp.evidence_grade, sp.n_records + (sp.n_records === "1" || sp.n_records === 1 ? " record" : " records"),
          sp.sources, sp.stated_or_inferred === "inferred" ? "address inferred" : "address as written"].join(" · ") })
      ]);
      var ev = (sp.evidence || []).map(function (i) { return byIdx[i]; }).filter(Boolean);
      if (ev.length) toggleBlock("sources (" + ev.length + ")", function () { return evidenceList(ev); }).forEach(function (n) { li.appendChild(n); });
      ul.appendChild(li);
    });
    wrap.appendChild(el("h4", { text: "Spans of use" }));
    wrap.appendChild(ul);

    var uncoded = h.evidence.filter(function (e) { return !e.use_category; });
    if (uncoded.length) {
      wrap.appendChild(el("h4", { text: "Other records here (" + uncoded.length + ", not coded to a use)" }));
      toggleBlock("show", function () { return evidenceList(uncoded, 30); }).forEach(function (n) { wrap.appendChild(n); });
    }
    return wrap;
  }

  function goTo(pid) {
    var m = markerById[pid];
    if (m) map.flyTo(m.getLatLng(), Math.max(map.getZoom(), 17), { duration: 0.6 });
    selectProperty(pid);
  }

  function summaryNode(inc, cls) {
    var text = inc.summary || "(no summary)";
    if (!inc.sensitivity) return el("div", { class: cls, text: text });
    // Sensitive: keep the record, collapse the summary behind a click.
    var wrap = el("div", { class: "collapsed-summary" });
    var btn = el("button", { text: "show" });
    var note = el("span", { class: "note", text: "summary hidden · flagged " + inc.sensitivity });
    var body = el("div", { class: cls, text: text, hidden: "" });
    btn.addEventListener("click", function () {
      body.hidden = !body.hidden;
      btn.textContent = body.hidden ? "show" : "hide";
    });
    wrap.appendChild(btn); wrap.appendChild(note); wrap.appendChild(body);
    return wrap;
  }

  function flags(inc) {
    var out = [];
    if (inc.sensitivity) out.push(el("span", { class: "badge-sensitive", text: "sensitive: " + inc.sensitivity }));
    if (inc.rights) out.push(chip("rights: " + inc.rights, "rights"));
    return out;
  }

  function renderTimeline(items) {
    var ul = el("ul", { class: "timeline" });
    items.forEach(function (inc) {
      var p = inc.date_precision || "unset";
      var dl = dateLabel(inc);
      var meta = el("div", { class: "meta" }, [
        chip(inc.source_kind === "roster" ? "roster · " + inc.source : inc.source, inc.source_kind === "roster" ? "roster" : ""),
        chip(inc.category || "—"),
        chip(inc.evidence_status ? inc.evidence_status : "ungraded", "ev-" + (inc.evidence_status || "ungraded")),
        chip("precision: " + p)
      ].concat(flags(inc)));
      var li = el("li", { class: "p-" + p, id: "inc-" + inc.id }, [
        el("span", { class: "when" + (dl.approx ? " approx" : ""), text: dl.text }),
        meta,
        summaryNode(inc, "summary")
      ]);
      if (inc.subjects.length) {
        var s = el("div", { class: "subjects" }, ["→ "]);
        inc.subjects.forEach(function (sub, i) {
          if (i) s.appendChild(document.createTextNode("; "));
          s.appendChild(el("b", { text: sub.name }));
          s.appendChild(document.createTextNode(" (" + sub.relationship + ")"));
        });
        li.appendChild(s);
      }
      ul.appendChild(li);
    });
    return ul;
  }

  function renderFeedItem(inc) {
    var li = el("li", {}, [
      el("span", { class: "when", text: datePart(inc.occurred_at) }),
      chip(inc.category || "—")
    ].concat(flags(inc)).concat([
      summaryNode(inc, "feed-summary"),
      el("span", { class: "src", text: inc.source })
    ]));
    return li;
  }

  /* Deep link: #property=<id> */
  function fromHash() {
    var m = /property=(\d+)/.exec(location.hash);
    if (m) {
      var wait = setInterval(function () {
        if (pointsLayer) { clearInterval(wait); goTo(Number(m[1])); }
      }, 100);
    }
  }
  window.addEventListener("hashchange", fromHash);
  fromHash();

  // Expose for console poking.
  window.corridorMap = { map: map, select: selectProperty, goTo: goTo };
})();
