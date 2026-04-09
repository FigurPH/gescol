document.addEventListener('DOMContentLoaded', () => {
    initUserFilters();
    // Re-inicia quando o HTMX carregar novo conteúdo
    document.body.addEventListener('htmx:afterOnLoad', initUserFilters);
});

// Executa imediatamente para lidar com injeção dinâmica via HTMX
initUserFilters();

function initUserFilters() {
    console.log("Iniciando filtros de usuários...");
    const tableBody = document.getElementById('table-usuarios-body');
    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr');
    const filters = {
        nome: document.getElementById('filter-user-nome'),
        login: document.getElementById('filter-user-login'),
        cd: document.getElementById('filter-user-cd'),
        nivel: document.getElementById('filter-user-nivel')
    };

    const applyFilters = () => {
        const values = {
            nome: filters.nome?.value.toLowerCase() || '',
            login: filters.login?.value.toLowerCase() || '',
            cd: filters.cd?.value.toLowerCase() || '',
            nivel: filters.nivel?.value || ''
        };

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 4) return;

            const matchesNome = cells[0].textContent.toLowerCase().includes(values.nome);
            const matchesLogin = cells[1].textContent.toLowerCase().includes(values.login);
            const matchesCD = cells[2].textContent.toLowerCase().includes(values.cd);

            // O nível está em um badge, extraímos o número
            const nivelText = cells[3].textContent.trim(); // Ex: "Lvl 10"
            const matchesNivel = values.nivel === "" || nivelText.includes('Lvl ' + values.nivel);

            if (matchesNome && matchesLogin && matchesCD && matchesNivel) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    };

    // Adiciona o evento de input a todos os filtros
    Object.values(filters).forEach(filter => {
        if (filter) {
            filter.addEventListener('input', applyFilters);
        }
    });
}
