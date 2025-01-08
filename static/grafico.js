document.addEventListener('DOMContentLoaded', () => {
    // Recupera o valor do atributo data-total
    const totalAgendamentos = parseInt(document.getElementById('totalAgendamentos').getAttribute('data-total'), 10);

    // Configuração do gráfico
    const ctx = document.getElementById('agendamentosChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Agendamentos Realizados'],
            datasets: [{
                label: 'Total de Agendamentos',
                data: [totalAgendamentos],  // Usando o valor convertido para número
                backgroundColor: ['rgba(75, 192, 192, 0.2)'],
                borderColor: ['rgba(75, 192, 192, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
});