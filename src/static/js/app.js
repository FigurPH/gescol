// Carregador de páginas SPA
async function loadContent(page) {
    try {
        const contentDiv = document.getElementById('content')
        contentDiv.innerHTML = '<div class="loading">Carregando...</div>'

        const response = await fetch(`${page}`)

        if (!response.ok) {
            throw new Error('Erro ao carregar conteúdo ou endpoint inexistente')
        }

        const html = await response.text()
        contentDiv.innerHTML = html

    } catch (error) {
        document.getElementById('content').innerHTML =
            '<div class="error">Erro ao carregar conteúdo. Tente novamente.</div>'
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const focusRegistration = () => {
        const regInput = document.getElementById('registration');
        if (regInput) regInput.focus();
    };

    focusRegistration();

    // Evento de input global para capturar mudanças no campo de matrícula (Saída de Equipamento)
    document.body.addEventListener('input', function (e) {
        if (e.target && e.target.id === 'registration') {
            const regInput = e.target;
            const collInput = document.getElementById('collector_number');

            // Garante que sejam apenas números
            regInput.value = regInput.value.replace(/\D/g, '');

            // Se chegar em 6 dígitos e existir o campo de coletor, foca nele
            if (regInput.value.length === 6 && collInput) {
                collInput.focus();
            }
        }
    });

    // Lógica para HTMX: após carregar dados do colaborador, garante foco no coletor se válido
    document.body.addEventListener('htmx:afterOnLoad', function (evt) {
        // Verifica se o alvo da resposta foi o resultado do colaborador
        if (evt.detail && evt.detail.target && evt.detail.target.id === 'employee-result') {
            const regInput = document.getElementById('registration');
            const collInput = document.getElementById('serialnumber');

            if (regInput && collInput && regInput.value.length === 6 &&
                !evt.detail.xhr.responseText.includes('Matrícula inválida')) {
                collInput.focus();
            }
        }

        // Se o conteúdo principal foi trocado, tenta focar na matrícula
        if (evt.detail && evt.detail.target && evt.detail.target.id === 'content') {
            focusRegistration();
        }
    });
});

// Comportamento global para dropdowns (mantido do original se houvesse)
function toggleDropdown(event) {
    if (event) event.stopPropagation();
    const dropdown = document.getElementById("myDropdown");
    if (dropdown) dropdown.classList.toggle("show-dropdown");
}
