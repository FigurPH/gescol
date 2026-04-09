document.addEventListener('DOMContentLoaded', () => {
    initFilters();
    // Re-inicia quando o HTMX carregar novo conteúdo
    document.body.addEventListener('htmx:afterOnLoad', initFilters);
});

// Executa imediatamente para lidar com injeção dinâmica via HTMX
initFilters();

function initFilters() {
    console.log("Iniciando filtros de coletores...");
    const tableBody = document.getElementById('table-coletores-body');
    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr');
    const filters = {
        nome: document.getElementById('filter-nome'),
        modelo: document.getElementById('filter-modelo'),
        serie: document.getElementById('filter-serie'),
        status: document.getElementById('filter-status')
    };

    const applyFilters = () => {
        const values = {
            nome: filters.nome.value.toLowerCase(),
            modelo: filters.modelo.value.toLowerCase(),
            serie: filters.serie.value.toLowerCase(),
            status: filters.status.value.toLowerCase()
        };

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 4) return;

            const matchesNome = cells[0].textContent.toLowerCase().includes(values.nome);
            const matchesModelo = cells[1].textContent.toLowerCase().includes(values.modelo);
            const matchesSerie = cells[2].textContent.toLowerCase().includes(values.serie);

            // O status está em um span dentro da quarta célula
            const statusText = cells[3].textContent.toLowerCase().trim();
            const matchesStatus = values.status === "" || statusText === values.status;

            if (matchesNome && matchesModelo && matchesSerie && matchesStatus) {
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