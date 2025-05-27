--nuevos permisos 
USE bdRestaurante;
GRANT UPDATE ON dbo.Pedidos TO camarero;
GRANT INSERT ON Auditoria TO camarero;

-- Otorgar permisos de lectura en las tablas necesarias
GRANT SELECT ON Pedidos TO cajero;
GRANT SELECT ON Mesas TO cajero;
GRANT SELECT ON Detalle_Pedidos TO cajero;
GRANT SELECT ON Productos TO cajero;

-- Otorgar permiso de actualizaci�n en la tabla Pedidos
GRANT UPDATE ON Pedidos TO cajero;

-- Otorgar permiso de inserci�n en la tabla Auditoria
GRANT INSERT ON Auditoria TO cajero;

-- Otorgar permiso de inserci�n en la tabla Pagos
GRANT INSERT ON Pagos TO cajero;

-- Otorgar permisos al cajero para actualizar la tabla Mesas
GRANT UPDATE ON Mesas TO cajero;

-- Ejecutar como administrador
GRANT SELECT, UPDATE ON Mesas TO cajero;
GRANT INSERT ON Pagos TO cajero;
GRANT UPDATE ON Pedidos TO cajero;
GRANT INSERT ON Auditoria TO cajero;


--modificar tabla 
ALTER TABLE Pagos DROP COLUMN fecha_pago;

ALTER TABLE Pagos ADD fecha_pago DATETIME DEFAULT GETDATE();


---27/05/2023
GRANT EXECUTE ON OBJECT::dbo.sp_ObtenerPagos TO adminRes;