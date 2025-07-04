DECLARE @dest varchar(200)
SET @dest = 'C:\PROYECTOSGIT\Poyecto_BD2\copiaS\Copia_' + 
            CAST(DAY(GETDATE()) AS varchar) + '_' + 
            CAST(DATEPART(HOUR, GETDATE()) AS varchar) + '_' + 
            CAST(DATEPART(MINUTE, GETDATE()) AS varchar) + '_' + 
            CAST(DATEPART(SECOND, GETDATE()) AS varchar) + 
            '.bak'

BACKUP DATABASE [bdRestaurante] 
TO DISK = @dest 
WITH NOFORMAT, NOINIT,  
     NAME = 'bdRestaurante-Completa Base de datos Copia de seguridad', 
     SKIP, NOREWIND, NOUNLOAD,  
     STATS = 10
GO