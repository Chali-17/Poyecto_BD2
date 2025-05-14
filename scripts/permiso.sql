use bdRestaurante;

--ver que permisos tiene los usuarios 
--SELECT DP.class_desc, DP.permission_name, DP.state_desc, DP.grantee_principal_id, U.name AS Usuario
--FROM sys.database_permissions DP
--JOIN sys.database_principals U ON DP.grantee_principal_id = U.principal_id
--WHERE U.name = 'cocina';

--para ver que roles tiene el usuario 
--SELECT 
  --  p.name AS Usuario,
   -- r.name AS Rol
--FROM 
--    sys.database_role_members rm
--JOIN 
  --  sys.database_principals r ON rm.role_principal_id = r.principal_id
--JOIN 
--    sys.database_principals p ON rm.member_principal_id = p.principal_id;



--PERMISOS PARA ADMINRES
CREATE ROLE AdministradorRol;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO AdministradorRol;
EXEC sp_addrolemember 'AdministradorRol', 'adminRes';

--PERMISOS PARA COCINA
--estados de comandas: Pendiente, Preparando, Servido, Pagado, Cancelado
--vista de cocina
CREATE VIEW vistaCocina AS
	SELECT id, UsuarioSys, mesa_id, fecha_pedido, estado
	FROM Pedidos
	WHERE estado = 'Pendiente';

CREATE ROLE CocinaRol;
GRANT SELECT ON vistaCocina TO CocinaRol;
EXEC sp_addrolemember 'CocinaRol', 'cocina';

--PERMISOS PARA CAJERO
CREATE VIEW vistaCajero AS
	SELECT id, UsuarioSys, mesa_id, fecha_pedido, estado
	FROM Pedidos
	WHERE estado = 'Servido';

CREATE ROLE CajeroRol;
GRANT SELECT ON vistaCocina TO CajeroRol;
GRANT INSERT ON Pagos TO CajeroRol;
EXEC sp_addrolemember 'CajeroRol', 'cajero';

--PERMIRSOS PARA CAMARERO
CREATE ROLE CamareroRol;
GRANT SELECT, INSERT, UPDATE ON Pedidos TO CamareroRol;
EXEC sp_addrolemember 'CamareroRol', 'camarero';








--ejecutar estas lineas 14-05-2025


--nuevos permisos 
GRANT SELECT ON dbo.Mesas TO camarero;
GRANT SELECT ON dbo.Productos TO camarero;
GRANT EXECUTE ON InsertarPedidoCompleto TO camarero;

--modificar tabla 
ALTER TABLE Pedidos DROP COLUMN fecha_pedido;

ALTER TABLE Pedidos ADD fecha_pedido DATETIME DEFAULT GETDATE();

