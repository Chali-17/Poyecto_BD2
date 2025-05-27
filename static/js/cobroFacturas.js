// ... existing code ...

function cobrarPedido(pedidoId) {
    if (confirm('¿Está seguro de cobrar este pedido?')) {
        fetch('/cajero/cobrar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pedido_id: pedidoId })
        })
        .then(response => {
            if (response.ok) {
                // Abrir el PDF en una nueva ventana
                response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    window.open(url, '_blank');
                    // Recargar la página después de un breve retraso
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                });
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Error al procesar el cobro');
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al procesar el cobro: ' + error.message);
        });
    }
}

// ... existing code ...