document.addEventListener("DOMContentLoaded", function() {
    // Supondo que o nome do usuário esteja disponível em uma variável global
    var userName = window.userName || ""; // ou você pode pegar isso de algum lugar específico
    
    // Se o nome estiver disponível, coloca ele no span com id "userName"
    if (userName) {
        document.getElementById("userName").textContent = userName;
    }
});

// Supondo que o nome do usuário seja carregado no HTML
document.addEventListener('DOMContentLoaded', function() {
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        // Exemplo: manipulação do nome do usuário, se necessário
        userNameElement.innerHTML = "Nome alterado via JS: " + userNameElement.innerHTML;
    }
});
