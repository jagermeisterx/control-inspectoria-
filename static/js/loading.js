/* Overlay global de carga para navegaciones y envíos de formularios.
   Las exportaciones (/exportar/ o botones data-export) usan estado "busy"
   en el propio botón, porque la descarga no recarga la página. */
(function () {
    var overlay = document.getElementById("global-loading");
    if (!overlay) return;
    var textEl = document.getElementById("global-loading-text");
    var timer = null;
    var DELAY = 150;

    function show(text) {
        clearTimeout(timer);
        timer = setTimeout(function () {
            if (textEl && text) textEl.textContent = text;
            overlay.hidden = false;
        }, DELAY);
    }

    function hideNow() {
        clearTimeout(timer);
        overlay.hidden = true;
    }
    window.showGlobalLoading = show;

    function busyButton(btn) {
        if (btn.dataset.busy) return;
        btn.dataset.busy = "1";
        btn.dataset.originalHtml = btn.innerHTML;
        btn.classList.add("disabled", "btn-loading");
        btn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-1"></span> Generando…';
        setTimeout(function () {
            btn.classList.remove("disabled", "btn-loading");
            btn.innerHTML = btn.dataset.originalHtml;
            delete btn.dataset.busy;
        }, 15000);
    }

    function isExportUrl(href) {
        return href.indexOf("/exportar/") !== -1 || href.indexOf("/reportes/desde-excel/pdf/") !== -1;
    }

    // Sin captura: así los handlers del formulario (ej. confirm() de eliminar)
    // ya se ejecutaron y podemos respetar defaultPrevented (usuario canceló).
    document.addEventListener("submit", function (e) {
        var form = e.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (e.defaultPrevented) return;
        if (form.hasAttribute("data-no-global-loader")) return;
        show(form.getAttribute("data-loading-text") || "Cargando…");
    });

    document.addEventListener("click", function (e) {
        var link = e.target.closest ? e.target.closest("a[href]") : null;
        if (!link) return;
        var href = link.getAttribute("href") || "";
        if (!href || href.charAt(0) === "#" || href.substring(0, 11).toLowerCase() === "javascript:") return;
        if (link.target === "_blank" || link.hasAttribute("download")) return;
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) return;
        if (link.origin && link.origin !== window.location.origin) return;
        if (isExportUrl(link.href)) {
            busyButton(link);
            return;
        }
        show(link.getAttribute("data-loading-text") || "Cargando…");
    });

    // Botones que disparan descargas vía JS (ej. Informe por Curso en reportes.html)
    document.addEventListener("click", function (e) {
        var btn = e.target.closest ? e.target.closest("[data-export]") : null;
        if (btn) busyButton(btn);
    });

    // Si el navegador restaura la página desde caché (bfcache), ocultar overlay
    window.addEventListener("pageshow", function (e) {
        if (e.persisted) hideNow();
    });
})();
