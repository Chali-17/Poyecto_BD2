CREATE FUNCTION dbo.fn_VentasPorDia (@fecha DATE)
RETURNS DECIMAL(10, 2)
AS
BEGIN
    DECLARE @total DECIMAL(10, 2)

    SELECT @total = ISNULL(SUM(monto), 0)
    FROM Pagos
    WHERE CAST(fecha_pago AS DATE) = @fecha

    RETURN @total
END
GO
