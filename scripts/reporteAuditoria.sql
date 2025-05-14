-- Crear un procedimiento almacenado que devuelva un informe de auditoría.
--ejcutar 14-05-2025
CREATE PROCEDURE informeAuditoria
AS
BEGIN
    WITH CTE_Auditoria AS (
        SELECT 
            id,
            UsuarioSys,
            accion,
            fecha
        FROM Auditoria
    )
    SELECT * FROM CTE_Auditoria;
END;
