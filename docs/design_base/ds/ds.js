/* ds.js — comportamientos OPCIONALES de la capa ds-* (JavaScript nativo, sin dependencias).
   La capa CSS funciona sin este archivo. Este script solo añade teclado y ARIA
   a los patrones que el HTML no resuelve por sí mismo.
   Uso: cargar ds.js con defer después de components.css ·  se auto-inicializa sobre document.
   Si inserta HTML dinámico (htmx, Vue, React): llame DS.init(contenedor).
   Todo se activa con atributos data-ds-*; nunca por clases de estilo. */
(function () {
  "use strict";
  var DS = window.DS || {};
  var NF = new Intl.NumberFormat("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var once = function (el, key) { if (el["__ds_" + key]) return false; el["__ds_" + key] = true; return true; };
  var $$ = function (root, sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); };

  /* ------------------------------------------------ región viva global */
  function live(msg) {
    var r = document.getElementById("ds-live");
    if (!r) { r = document.createElement("div"); r.id = "ds-live"; r.className = "ds-visually-hidden"; r.setAttribute("aria-live", "polite"); document.body.appendChild(r); }
    r.textContent = ""; setTimeout(function () { r.textContent = msg; }, 30);
  }
  DS.announce = live;

  /* ------------------------------------------------ pestañas  [data-ds-tabs] */
  function tabs(root) {
    $$(root, "[data-ds-tabs]").forEach(function (box) {
      if (!once(box, "tabs")) return;
      var list = box.querySelector('[role="tablist"]');
      var tabsEls = $$(list, '[role="tab"]');
      function select(t, focus) {
        tabsEls.forEach(function (x) {
          var on = x === t;
          x.setAttribute("aria-selected", on); x.tabIndex = on ? 0 : -1;
          var p = document.getElementById(x.getAttribute("aria-controls")); if (p) p.hidden = !on;
        });
        if (focus) t.focus();
      }
      tabsEls.forEach(function (t, i) {
        t.addEventListener("click", function () { select(t); });
        t.addEventListener("keydown", function (e) {
          var k = e.key, n = tabsEls.length, j = null;
          if (k === "ArrowRight") j = (i + 1) % n; else if (k === "ArrowLeft") j = (i - 1 + n) % n;
          else if (k === "Home") j = 0; else if (k === "End") j = n - 1;
          if (j !== null) { e.preventDefault(); select(tabsEls[j], true); }
        });
      });
    });
  }

  /* ------------------------------------------- combobox  [data-ds-combobox] */
  function combobox(root) {
    $$(root, "[data-ds-combobox]").forEach(function (box) {
      if (!once(box, "cbx")) return;
      var input = box.querySelector('[role="combobox"]');
      var list = box.querySelector('[role="listbox"]');
      var toggle = box.querySelector(".ds-combobox__toggle");
      var empty = box.querySelector(".ds-listbox__empty");
      var mode = box.getAttribute("data-ds-combobox"); // "select" | "autocomplete"
      var opts = $$(list, '[role="option"]');
      opts.forEach(function (o) { o.__label = o.getAttribute("data-label") || o.textContent.trim(); });
      var active = -1;
      function visible() { return opts.filter(function (o) { return !o.hidden; }); }
      function open() { list.hidden = false; input.setAttribute("aria-expanded", "true"); }
      function close() { list.hidden = true; input.setAttribute("aria-expanded", "false"); setActive(null); }
      function setActive(o) {
        opts.forEach(function (x) { x.classList.remove("is-active"); });
        if (o) { o.classList.add("is-active"); input.setAttribute("aria-activedescendant", o.id); o.scrollIntoView({ block: "nearest" }); }
        else input.removeAttribute("aria-activedescendant");
        active = o ? visible().indexOf(o) : -1;
      }
      function choose(o) {
        opts.forEach(function (x) { x.setAttribute("aria-selected", x === o); });
        input.value = o.__label; close();
        input.dispatchEvent(new Event("change", { bubbles: true }));
        var hidden = box.querySelector('input[type="hidden"]'); if (hidden) hidden.value = o.getAttribute("data-value") || o.__label;
      }
      function filter() {
        var q = input.value.trim().toLowerCase();
        var norm = function (s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
        var nq = norm(q), count = 0;
        opts.forEach(function (o) {
          var hit = !nq || norm(o.__label).indexOf(nq) > -1;
          o.hidden = !hit; if (hit) count++;
          var t = o.querySelector(".ds-option__text");
          if (t) {
            if (nq && hit) { var i = norm(o.__label).indexOf(nq); t.innerHTML = ""; t.append(o.__label.slice(0, i)); var m = document.createElement("mark"); m.textContent = o.__label.slice(i, i + nq.length); t.append(m, o.__label.slice(i + nq.length)); }
            else t.textContent = o.__label;
          }
        });
        if (empty) empty.hidden = count > 0;
        live(count === 0 ? "Sin resultados" : count + (count === 1 ? " resultado" : " resultados"));
      }
      input.addEventListener("input", function () { if (mode === "autocomplete") filter(); open(); var v = visible(); setActive(v[0] || null); });
      input.addEventListener("click", function () { if (mode === "select") { list.hidden ? open() : close(); } });
      input.addEventListener("keydown", function (e) {
        var v = visible();
        if (e.key === "ArrowDown") { e.preventDefault(); if (list.hidden) { open(); } setActive(v[Math.min(active + 1, v.length - 1)] || null); }
        else if (e.key === "ArrowUp") { e.preventDefault(); if (e.altKey) { close(); return; } setActive(v[Math.max(active - 1, 0)] || null); }
        else if (e.key === "Home" && !list.hidden && mode === "select") { e.preventDefault(); setActive(v[0]); }
        else if (e.key === "End" && !list.hidden && mode === "select") { e.preventDefault(); setActive(v[v.length - 1]); }
        else if (e.key === "Enter") { if (!list.hidden && active > -1) { e.preventDefault(); choose(v[active]); } }
        else if (e.key === "Escape") { if (!list.hidden) { e.preventDefault(); close(); } else if (mode === "autocomplete") { input.value = ""; filter(); } }
        else if (e.key === "Tab") { close(); }
      });
      opts.forEach(function (o) {
        o.addEventListener("mousedown", function (e) { e.preventDefault(); });
        o.addEventListener("click", function () { if (o.getAttribute("aria-disabled") !== "true") choose(o); });
      });
      if (toggle) toggle.addEventListener("click", function () { list.hidden ? open() : close(); input.focus(); });
      input.addEventListener("blur", function () { setTimeout(close, 120); });
    });
  }

  /* ----------------------------- listbox múltiple  [data-ds-listbox-multi] */
  function listboxMulti(root) {
    $$(root, "[data-ds-listbox-multi]").forEach(function (list) {
      if (!once(list, "lbm")) return;
      var opts = $$(list, '[role="option"]'), active = 0, anchor = 0;
      var out = document.getElementById(list.getAttribute("data-ds-listbox-multi"));
      function render() {
        opts.forEach(function (o, i) { o.classList.toggle("is-active", i === active && list === document.activeElement); });
        list.setAttribute("aria-activedescendant", opts[active].id);
        var n = opts.filter(function (o) { return o.getAttribute("aria-selected") === "true"; }).length;
        if (out) out.textContent = n === 0 ? "Ninguno seleccionado" : n + (n === 1 ? " seleccionado" : " seleccionados");
      }
      function toggle(i) { var o = opts[i]; if (o.getAttribute("aria-disabled") === "true") return; o.setAttribute("aria-selected", o.getAttribute("aria-selected") !== "true"); }
      list.addEventListener("focus", render); list.addEventListener("blur", render);
      list.addEventListener("keydown", function (e) {
        var k = e.key;
        if (k === "ArrowDown" || k === "ArrowUp") { e.preventDefault(); active = Math.max(0, Math.min(opts.length - 1, active + (k === "ArrowDown" ? 1 : -1))); if (e.shiftKey) toggle(active); else anchor = active; opts[active].scrollIntoView({ block: "nearest" }); }
        else if (k === " ") { e.preventDefault(); toggle(active); anchor = active; }
        else if (k === "Home") { e.preventDefault(); active = 0; } else if (k === "End") { e.preventDefault(); active = opts.length - 1; }
        else if ((e.ctrlKey || e.metaKey) && k.toLowerCase() === "a") { e.preventDefault(); var all = opts.every(function (o) { return o.getAttribute("aria-selected") === "true" || o.getAttribute("aria-disabled") === "true"; }); opts.forEach(function (o) { if (o.getAttribute("aria-disabled") !== "true") o.setAttribute("aria-selected", !all); }); }
        render();
      });
      opts.forEach(function (o, i) { o.addEventListener("click", function () { active = i; toggle(i); list.focus(); render(); }); });
      render();
    });
  }

  /* ------------------------------------------ diálogo  [data-ds-open="id"] */
  function dialogs(root) {
    $$(root, "[data-ds-open]").forEach(function (btn) {
      if (!once(btn, "dlg")) return;
      btn.addEventListener("click", function () { var d = document.getElementById(btn.getAttribute("data-ds-open")); if (d && d.showModal) d.showModal(); });
    });
    $$(root, "dialog.ds-modal, dialog.ds-drawer").forEach(function (d) {
      if (!once(d, "dlgc")) return;
      d.addEventListener("click", function (e) {
        if (e.target === d && d.getAttribute("data-ds-dismissable") !== "false") d.close("cancel");
        var c = e.target.closest("[data-ds-close]"); if (c && d.contains(c)) d.close(c.getAttribute("data-ds-close") || "cancel");
      });
    });
  }

  /* ------------------------------------ popover / menú  [data-ds-toggle="id"] */
  function toggles(root) {
    $$(root, "[data-ds-toggle]").forEach(function (btn) {
      if (!once(btn, "tgl")) return;
      var pop = document.getElementById(btn.getAttribute("data-ds-toggle"));
      var isMenu = pop.getAttribute("role") === "menu";
      var items = function () { return $$(pop, '[role="menuitem"]'); };
      function open() { pop.hidden = false; btn.setAttribute("aria-expanded", "true"); if (isMenu) items()[0].focus(); }
      function close(ret) { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); if (ret) btn.focus(); }
      btn.addEventListener("click", function () { pop.hidden ? open() : close(); });
      btn.addEventListener("keydown", function (e) { if (isMenu && (e.key === "ArrowDown")) { e.preventDefault(); open(); } });
      pop.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { e.preventDefault(); close(true); return; }
        if (!isMenu) return;
        var it = items(), i = it.indexOf(document.activeElement);
        if (e.key === "ArrowDown") { e.preventDefault(); it[(i + 1) % it.length].focus(); }
        if (e.key === "ArrowUp") { e.preventDefault(); it[(i - 1 + it.length) % it.length].focus(); }
        if (e.key === "Home") { e.preventDefault(); it[0].focus(); }
        if (e.key === "End") { e.preventDefault(); it[it.length - 1].focus(); }
        if (e.key === "Tab") close();
      });
      if (isMenu) items().forEach(function (it) { it.addEventListener("click", function () { close(true); }); });
      document.addEventListener("click", function (e) { if (!pop.hidden && !pop.contains(e.target) && !btn.contains(e.target)) close(); });
    });
  }

  /* ----------------- tooltip: Esc lo oculta sin mover el foco (WCAG 1.4.13) */
  function tooltips(root) {
    if (!once(document, "tt")) return;
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      $$(document, ".ds-tooltip-anchor").forEach(function (a) { if (a.matches(":hover, :focus-within")) { var t = a.querySelector(".ds-tooltip"); t.style.visibility = "hidden"; a.addEventListener("mouseleave", function r() { t.style.visibility = ""; a.removeEventListener("mouseleave", r); }); a.addEventListener("focusout", function r2() { t.style.visibility = ""; a.removeEventListener("focusout", r2); }); } });
    });
  }

  /* ------------------------------------------ tabla  [data-ds-table] */
  function tables(root) {
    $$(root, "[data-ds-table]").forEach(function (table) {
      if (!once(table, "tbl")) return;
      var tbody = table.tBodies[0];
      var all = table.querySelector("[data-ds-select-all]");
      var counter = document.getElementById(table.getAttribute("data-ds-selection-count") || "");
      var lastIdx = null;
      function rows() { return Array.prototype.slice.call(tbody.rows); }
      function sync() {
        var r = rows(), sel = r.filter(function (x) { var c = x.querySelector("[data-ds-select-row]"); return c && c.checked; });
        r.forEach(function (x) { var c = x.querySelector("[data-ds-select-row]"); if (c) x.setAttribute("aria-selected", c.checked); });
        if (all) { all.checked = sel.length === r.length && r.length > 0; all.indeterminate = sel.length > 0 && sel.length < r.length; }
        if (counter) { counter.hidden = sel.length === 0; var t = counter.querySelector("[data-ds-count]"); if (t) t.textContent = sel.length + (sel.length === 1 ? " fila seleccionada" : " filas seleccionadas"); }
      }
      if (all) all.addEventListener("change", function () { rows().forEach(function (x) { var c = x.querySelector("[data-ds-select-row]"); if (c) c.checked = all.checked; }); sync(); live(all.checked ? "Todas las filas seleccionadas" : "Selección vaciada"); });
      tbody.addEventListener("click", function (e) {
        var c = e.target.closest("[data-ds-select-row]"); if (!c) return;
        var idx = rows().indexOf(c.closest("tr"));
        if (e.shiftKey && lastIdx !== null) { var a = Math.min(idx, lastIdx), b = Math.max(idx, lastIdx); rows().slice(a, b + 1).forEach(function (x) { x.querySelector("[data-ds-select-row]").checked = c.checked; }); }
        lastIdx = idx; sync();
      });
      tbody.addEventListener("change", sync);
      $$(table, "th .ds-table__sort").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var th = btn.closest("th"), col = Array.prototype.indexOf.call(th.parentNode.children, th);
          var dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
          $$(table, "th[aria-sort]").forEach(function (h) { h.setAttribute("aria-sort", "none"); });
          th.setAttribute("aria-sort", dir);
          var type = th.getAttribute("data-type") || "text";
          var val = function (tr) { var cell = tr.cells[col]; var v = cell.getAttribute("data-value") || cell.textContent.trim(); return type === "number" ? parseFloat(v.replace(/[^0-9.\-]/g, "")) : v.toLocaleLowerCase("es-MX"); };
          var r = rows().sort(function (a, b) { var x = val(a), y = val(b); var c = type === "number" ? x - y : String(x).localeCompare(String(y), "es-MX"); return dir === "ascending" ? c : -c; });
          r.forEach(function (x) { tbody.appendChild(x); });
          live("Ordenado por " + btn.textContent.trim() + ", " + (dir === "ascending" ? "ascendente" : "descendente"));
        });
      });
      if (table.hasAttribute("data-ds-grid")) gridNav(table);
      sync();
    });
  }
  /* navegación de celdas con flechas (role="grid"): una sola parada de tabulación */
  function gridNav(table) {
    var cells = function () { return Array.prototype.slice.call(table.rows).map(function (r) { return Array.prototype.slice.call(r.cells); }); };
    var cur = [1, 0];
    function focusCell(r, c) {
      var g = cells(); r = Math.max(0, Math.min(g.length - 1, r)); c = Math.max(0, Math.min(g[r].length - 1, c));
      g.forEach(function (row) { row.forEach(function (x) { x.tabIndex = -1; x.classList.remove("is-focus"); }); });
      var cell = g[r][c]; cell.tabIndex = 0; cur = [r, c];
      var inner = cell.querySelector("button, input, a"); (inner || cell).focus(); cell.classList.add("is-focus");
    }
    var g = cells(); g.forEach(function (row) { row.forEach(function (x) { x.tabIndex = -1; $$(x, "button, input, a").forEach(function (i) { i.tabIndex = -1; }); }); });
    g[1][0].tabIndex = 0;
    table.addEventListener("focusin", function (e) { var td = e.target.closest("td, th"); if (td) { var r = td.parentNode.rowIndex, c = td.cellIndex; cur = [r, c]; cells().forEach(function (row) { row.forEach(function (x) { x.classList.toggle("is-focus", x === td); x.tabIndex = x === td ? 0 : -1; }); }); } });
    table.addEventListener("focusout", function (e) { if (!table.contains(e.relatedTarget)) $$(table, ".is-focus").forEach(function (x) { x.classList.remove("is-focus"); }); });
    table.addEventListener("keydown", function (e) {
      var k = e.key, r = cur[0], c = cur[1];
      if (k === "ArrowDown") r++; else if (k === "ArrowUp") r--; else if (k === "ArrowRight") c++; else if (k === "ArrowLeft") c--;
      else if (k === "Home") c = e.ctrlKey ? (r = 1, 0) : 0; else if (k === "End") { c = 99; if (e.ctrlKey) r = 999; }
      else if (k === "PageDown") r += 10; else if (k === "PageUp") r -= 10;
      else if (k === "Enter" || k === " ") { var inner = cells()[r][c].querySelector("button, input"); if (inner && document.activeElement !== inner) { inner.focus(); } if (inner && k === " " && inner.type === "checkbox") { e.preventDefault(); inner.click(); } return; }
      else return;
      e.preventDefault(); focusCell(r, c);
    });
  }

  /* ------------------------------------------ stepper  [data-ds-stepper] */
  function steppers(root) {
    $$(root, "[data-ds-stepper]").forEach(function (box) {
      if (!once(box, "stp")) return;
      var input = box.querySelector("input"), btns = box.querySelectorAll(".ds-stepper__btn");
      function upd() { var v = +input.value, min = input.min === "" ? -Infinity : +input.min, max = input.max === "" ? Infinity : +input.max; btns[0].disabled = v <= min || input.disabled; btns[1].disabled = v >= max || input.disabled; }
      btns[0].addEventListener("click", function () { input.stepDown(); input.dispatchEvent(new Event("input", { bubbles: true })); upd(); live(input.value); });
      btns[1].addEventListener("click", function () { input.stepUp(); input.dispatchEvent(new Event("input", { bubbles: true })); upd(); live(input.value); });
      input.addEventListener("input", upd); upd();
    });
  }

  /* --------------------------- contraseña  [data-ds-password-toggle] */
  function passwords(root) {
    $$(root, "[data-ds-password-toggle]").forEach(function (btn) {
      if (!once(btn, "pwd")) return;
      var input = document.getElementById(btn.getAttribute("data-ds-password-toggle"));
      btn.addEventListener("click", function () {
        var show = input.type === "password"; input.type = show ? "text" : "password";
        btn.setAttribute("aria-pressed", show); btn.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
        var u = btn.querySelector("use"); if (u) u.setAttribute("href", show ? "#i-eye-off" : "#i-eye");
      });
    });
  }

  /* --------------------------------- moneda MXN  [data-ds-money] */
  function money(root) {
    $$(root, "[data-ds-money]").forEach(function (input) {
      if (!once(input, "mny")) return;
      input.addEventListener("focus", function () { input.value = input.value.replace(/,/g, ""); });
      input.addEventListener("blur", function () { var n = parseFloat(input.value.replace(/[^0-9.\-]/g, "")); if (!isNaN(n)) input.value = NF.format(n); });
      if (input.value) { var n = parseFloat(input.value.replace(/[^0-9.\-]/g, "")); if (!isNaN(n)) input.value = NF.format(n); }
    });
  }
  DS.formatMXN = function (n) { return "$" + NF.format(n) + " MXN"; };

  /* ---------------------------- contador de caracteres  [data-ds-counter="id"] */
  function counters(root) {
    $$(root, "[data-ds-counter]").forEach(function (input) {
      if (!once(input, "cnt")) return;
      var out = document.getElementById(input.getAttribute("data-ds-counter"));
      var max = +input.getAttribute("data-max");
      function upd() {
        var n = input.value.length, over = n > max;
        out.textContent = n.toLocaleString("es-MX") + " de " + max.toLocaleString("es-MX");
        out.classList.toggle("is-over", over);
        if (over !== input.__over) { input.__over = over; if (over) live("Excede el límite por " + (n - max) + " caracteres"); }
      }
      input.addEventListener("input", upd); upd();
    });
  }

  /* -------------------------------------- archivo  [data-ds-file] */
  function files(root) {
    $$(root, "[data-ds-file]").forEach(function (zone) {
      if (!once(zone, "file")) return;
      var input = zone.querySelector('input[type="file"]');
      var list = document.getElementById(zone.getAttribute("data-ds-file"));
      var maxMB = +(zone.getAttribute("data-max-mb") || 10);
      function size(b) { return b > 1048576 ? (b / 1048576).toLocaleString("es-MX", { maximumFractionDigits: 1 }) + " MB" : Math.ceil(b / 1024).toLocaleString("es-MX") + " KB"; }
      function render(fl) {
        Array.prototype.forEach.call(fl, function (f) {
          var li = document.createElement("li"), bad = f.size > maxMB * 1048576;
          li.className = "ds-file-list__item" + (bad ? " is-error" : "");
          li.innerHTML = '<svg class="ds-icon" aria-hidden="true"><use href="#i-' + (bad ? "x-circle" : "file") + '"/></svg><span class="ds-file-list__name"></span><span class="ds-file-list__meta"></span><button type="button" class="ds-btn ds-btn--ghost ds-btn--icon ds-btn--sm"><svg class="ds-icon" aria-hidden="true"><use href="#i-x"/></svg></button>';
          li.querySelector(".ds-file-list__name").textContent = f.name;
          li.querySelector(".ds-file-list__meta").textContent = bad ? "Pesa " + size(f.size) + "; el máximo es " + maxMB + " MB" : size(f.size);
          var b = li.querySelector("button"); b.setAttribute("aria-label", "Quitar " + f.name); b.addEventListener("click", function () { li.remove(); live("Archivo quitado"); });
          list.appendChild(li);
        });
        live(fl.length + (fl.length === 1 ? " archivo agregado" : " archivos agregados"));
      }
      input.addEventListener("change", function () { render(input.files); });
      ["dragenter", "dragover"].forEach(function (ev) { zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add("is-dragover"); }); });
      ["dragleave", "drop"].forEach(function (ev) { zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.remove("is-dragover"); if (ev === "drop") render(e.dataTransfer.files); }); });
    });
  }

  /* ---------------------- botones conmutables  [data-ds-pressed] y switch */
  function pressables(root) {
    $$(root, "[data-ds-pressed]").forEach(function (b) {
      if (!once(b, "prs")) return;
      b.addEventListener("click", function () {
        var group = b.closest("[data-ds-exclusive]");
        if (group) { $$(group, "[data-ds-pressed]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); }
        else b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") !== "true");
      });
    });
    $$(root, ".ds-switch[data-ds-state]").forEach(function (s) {
      if (!once(s, "sw")) return;
      var out = document.getElementById(s.getAttribute("data-ds-state"));
      var upd = function () { if (out) out.textContent = s.checked ? "Activado" : "Desactivado"; };
      s.addEventListener("change", upd); upd();
    });
    $$(root, ".ds-chip__remove").forEach(function (b) {
      if (!once(b, "chip")) return;
      b.addEventListener("click", function () { var chip = b.closest(".ds-chip"), next = chip.nextElementSibling || chip.previousElementSibling; chip.remove(); live((b.getAttribute("aria-label") || "Elemento quitado").replace("Quitar", "Se quitó")); if (next) { var f = next.querySelector("button") || next; f.focus && f.focus(); } });
    });
  }

  /* --------------------------------------------- notificación emergente */
  DS.toast = function (o) {
    o = o || {}; var type = o.type || "info";
    var region = document.querySelector(".ds-toast-region");
    if (!region) { region = document.createElement("div"); region.className = "ds-toast-region"; region.setAttribute("role", "region"); region.setAttribute("aria-label", "Notificaciones"); document.body.appendChild(region); }
    var icon = { success: "check-circle", danger: "x-circle", warning: "alert-triangle", info: "info" }[type];
    var t = document.createElement("div");
    t.className = "ds-toast ds-toast--" + type; t.setAttribute("role", type === "danger" ? "alert" : "status");
    t.innerHTML = '<svg class="ds-icon" aria-hidden="true"><use href="#i-' + icon + '"/></svg><div class="ds-toast__body"><p class="ds-toast__title"></p><p class="ds-toast__text"></p></div>' + (o.action ? '<button type="button" class="ds-btn ds-btn--ghost ds-btn--sm" data-act></button>' : "") + '<button type="button" class="ds-btn ds-btn--ghost ds-btn--icon ds-btn--sm" aria-label="Cerrar notificación"><svg class="ds-icon" aria-hidden="true"><use href="#i-x"/></svg></button>';
    t.querySelector(".ds-toast__title").textContent = o.title || "";
    t.querySelector(".ds-toast__text").textContent = o.text || "";
    if (o.action) { var a = t.querySelector("[data-act]"); a.textContent = o.action; a.addEventListener("click", function () { o.onAction && o.onAction(); t.remove(); }); }
    t.querySelector('[aria-label="Cerrar notificación"]').addEventListener("click", function () { t.remove(); });
    region.appendChild(t);
    var ms = o.duration === 0 ? 0 : (o.duration || (type === "danger" ? 0 : 6000));
    if (ms) { var timer = setTimeout(function () { t.remove(); }, ms); t.addEventListener("mouseenter", function () { clearTimeout(timer); }); t.addEventListener("focusin", function () { clearTimeout(timer); }); }
    return t;
  };

  DS.init = function (root) {
    root = root || document;
    [tabs, combobox, listboxMulti, dialogs, toggles, tooltips, tables, steppers, passwords, money, counters, files, pressables].forEach(function (f) { f(root); });
  };
  window.DS = DS;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { DS.init(); });
  else DS.init();
})();
