document.addEventListener('DOMContentLoaded', () => {
    // Recupera o valor do atributo data-total e converte para número inteiro
    const totalAgendamentos = parseInt(document.getElementById('totalAgendamentos').getAttribute('data-total'), 10);

    // Configuração do gráfico
    const ctx = document.getElementById('agendamentosChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',  // Tipo do gráfico
        data: {
            labels: ['Agendamentos Realizados'],  // Rótulo do eixo X
            datasets: [{
                label: 'Total de Agendamentos',
                data: [totalAgendamentos],  // Valor de dados que será exibido
                backgroundColor: ['rgba(75, 192, 192, 0.2)'],  // Cor de fundo das barras
                borderColor: ['rgba(75, 192, 192, 1)'],  // Cor da borda das barras
                borderWidth: 3  // Largura da borda
            }]
        },
        options: {
            responsive: true,  // Torna o gráfico responsivo
            plugins: {
                legend: { display: true },  // Exibe a legenda
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            // Exibe os valores inteiros no tooltip
                            return tooltipItem.raw.toFixed(0);
                        }
                    }
                }
            },
            scales: {
                // Eixo Y
                y: {
                    beginAtZero: true,  // Começa o gráfico do zero
                    ticks: {
                        display: false,  // Desabilita os números do eixo Y
                    },
                    grid: {
                        display: false,  // Desabilita as linhas de grade
                    },
                    border: {
                        display: false,  // Remove a linha do eixo Y
                    }
                },
                // Eixo X
                x: {
                    grid: {
                        display: false,  // Desabilita as linhas de grade do eixo X
                    },
                    border: {
                        display: false,  // Remove a linha do eixo X
                    }
                }
            }
        }
    });
});