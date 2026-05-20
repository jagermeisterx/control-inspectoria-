document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.autocomplete-alumno').forEach(function(wrapper) {
        var input = wrapper.querySelector('.ac-input');
        var hidden = wrapper.querySelector('.ac-hidden');
        var list = wrapper.querySelector('.ac-list');
        var timer = null;

        input.addEventListener('input', function() {
            var q = this.value.trim();
            clearTimeout(timer);
            if (q.length < 2) { list.innerHTML = ''; list.style.display = 'none'; return; }
            timer = setTimeout(function() {
                fetch('/api/alumnos/?q=' + encodeURIComponent(q))
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!data.length) { list.innerHTML = ''; list.style.display = 'none'; return; }
                        list.innerHTML = '';
                        data.forEach(function(al) {
                            var li = document.createElement('div');
                            li.className = 'ac-item';
                            li.textContent = al.text;
                            li.dataset.id = al.id;
                            li.addEventListener('click', function() {
                                input.value = al.text;
                                hidden.value = al.id;
                                list.innerHTML = '';
                                list.style.display = 'none';
                            });
                            list.appendChild(li);
                        });
                        list.style.display = 'block';
                    });
            }, 200);
        });

        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                list.style.display = 'none';
            }
        });
    });
});
