(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var inputBuscar = document.getElementById('rep-buscar');
        var selectCurso = document.getElementById('rep-curso');
        var contResultados = document.getElementById('rep-resultados');
        var emptyMsg = document.getElementById('rep-empty');
        if (!inputBuscar || !selectCurso || !contResultados) return;

        var timer = null;
        var lastQuery = '';

        function renderEmpty(msg) {
            contResultados.innerHTML = '<div class="text-muted small p-3 text-center"><i class="bi bi-search"></i> ' + msg + '</div>';
        }

        function renderResultados(data) {
            if (!data || !data.length) {
                renderEmpty('No se encontraron alumnos.');
                return;
            }
            var html = '';
            data.forEach(function(al) {
                html += '<a href="/reportes/alumno/' + al.id + '/" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">';
                html += '  <span><i class="bi bi-person-circle text-muted"></i> ' + al.text + '</span>';
                if (al.curso) {
                    html += '  <span class="badge badge-curso badge-curso-sm">' + al.curso + '</span>';
                }
                html += '</a>';
            });
            contResultados.innerHTML = html;
        }

        function buscar() {
            var q = inputBuscar.value.trim();
            var curso = selectCurso.value;
            var key = q + '|' + curso;
            if (key === lastQuery) return;
            lastQuery = key;
            if (q.length < 2 && !curso) {
                renderEmpty('Empieza a escribir o selecciona un curso para buscar...');
                return;
            }
            renderEmpty('Buscando...');
            var url = '/api/alumnos/?q=' + encodeURIComponent(q) + '&curso=' + encodeURIComponent(curso);
            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function(r) { return r.json(); })
                .then(function(data) { renderResultados(data); })
                .catch(function() { renderEmpty('Error al buscar. Intenta nuevamente.'); });
        }

        inputBuscar.addEventListener('input', function() {
            clearTimeout(timer);
            timer = setTimeout(buscar, 200);
        });

        selectCurso.addEventListener('change', function() {
            clearTimeout(timer);
            buscar();
        });
    });
})();
