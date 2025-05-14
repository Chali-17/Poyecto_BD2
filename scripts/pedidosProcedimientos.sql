--procedmiento para insertar pedidos 
--ejeuctar 14-05-2025

CREATE PROCEDURE InsertarPedidoCompleto
    @mesa_id INTEGER,
    @estado NVARCHAR(255),
    @ProductosDetalles NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @pedido_id INTEGER;
    DECLARE @UsuarioSys NVARCHAR(255) = SUSER_NAME(); -- Captura el usuario de la sesión

    -- Verificar que la mesa existe
    IF NOT EXISTS (SELECT 1 FROM Mesas WHERE id = @mesa_id)
    BEGIN
        RAISERROR('La mesa especificada no existe.', 16, 1);
        RETURN;
    END

    -- Insertar en Pedidos sin requerir el usuario desde la app
    INSERT INTO Pedidos (UsuarioSys, mesa_id, estado)
    VALUES (@UsuarioSys, @mesa_id, @estado);

    SET @pedido_id = SCOPE_IDENTITY();

    -- Insertar en Detalle_Pedidos, calculando el subtotal con el precio de Productos
    INSERT INTO Detalle_Pedidos (pedido_id, producto_id, cantidad, subtotal)
    SELECT @pedido_id, p.id, JSON_VALUE(pd.value, '$.cantidad'), 
           JSON_VALUE(pd.value, '$.cantidad') * p.precio -- Calculando el subtotal
    FROM OPENJSON(@ProductosDetalles) AS pd
    INNER JOIN Productos p ON p.id = JSON_VALUE(pd.value, '$.producto_id')
    INNER JOIN Categoria c ON c.id = p.categoria_id;

    -- Registrar acción en Auditoría
    INSERT INTO Auditoria (UsuarioSys, accion, fecha)
    VALUES (@UsuarioSys, 'Inicio pedido ID ' + CAST(@pedido_id AS NVARCHAR(50)), GETDATE());
END
GO
