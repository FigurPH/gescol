document.addEventListener('DOMContentLoaded', () => {
    initEmpFilters();
    // Re-inicia quando o HTMX carregar novo conteúdo
    document.body.addEventListener('htmx:afterOnLoad', initEmpFilters);
});

// Executa imediatamente para lidar com injeção dinâmica via HTMX
initEmpFilters();

function initEmpFilters() {
    console.log("Iniciando filtros de colaboradores...");
    const tableBody = document.getElementById('table-colaboradores-body');
    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr');
    const filters = {
        nome: document.getElementById('filter-emp-nome'),
        cargo: document.getElementById('filter-emp-cargo'),
        setor: document.getElementById('filter-emp-setor')
    };

    const applyFilters = () => {
        const values = {
            nome: filters.nome?.value.toLowerCase() || '',
            cargo: filters.cargo?.value.toLowerCase() || '',
            setor: filters.setor?.value.toLowerCase() || ''
        };

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 3) return;

            const matchesNome = cells[0].textContent.toLowerCase().includes(values.nome);
            const matchesCargo = cells[1].textContent.toLowerCase().includes(values.cargo);
            const matchesSetor = cells[2].textContent.toLowerCase().includes(values.setor);

            if (matchesNome && matchesCargo && matchesSetor) {
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
