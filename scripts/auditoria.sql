-- Procedimiento para registrar inicio de sesión
CREATE PROCEDURE inicioSesion (@Usuario NVARCHAR(255))
AS
BEGIN
    INSERT INTO Auditoria (UsuarioSys, accion, fecha)
    VALUES (@Usuario, 'Inicio de sesión', GETDATE());
END
GO

-- Procedimiento para registrar cierre de sesión
CREATE PROCEDURE cerrarSesion (@Usuario NVARCHAR(255))
AS
BEGIN
    INSERT INTO Auditoria (UsuarioSys, accion, fecha)
    VALUES (@Usuario, 'Cierre de sesión', GETDATE());
END
GO
--hola este es un comentario