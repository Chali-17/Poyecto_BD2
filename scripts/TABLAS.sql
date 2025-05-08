CREATE TABLE [Pedidos] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [UsuarioSys] NVARCHAR(255) NOT NULL,
  [mesa_id] INTEGER NOT NULL,
  [fecha_pedido] TIMESTAMP,
  [estado] NVARCHAR(255)
)
GO

CREATE TABLE [Productos] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [nombre] NVARCHAR(255),
  [precio] DECIMAL(10,2),
  [categoria_id] INTEGER NOT NULL
)
GO

CREATE TABLE [Categoria] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [nombre] NVARCHAR(255)
)
GO

CREATE TABLE [Detalle_Pedidos] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [pedido_id] INTEGER NOT NULL,
  [producto_id] INTEGER NOT NULL,
  [cantidad] INTEGER,
  [subtotal] DECIMAL(10,2)
)
GO

CREATE TABLE [Pagos] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [pedido_id] INTEGER NOT NULL,
  [UsuarioSys] NVARCHAR(255) NOT NULL,
  [monto] DECIMAL(10,2),
  [metodo_pago] NVARCHAR(255),
  [fecha_pago] TIMESTAMP
)
GO

CREATE TABLE [Mesas] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [numero_mesa] INTEGER NOT NULL,
  [estado] NVARCHAR(255)
)
GO

CREATE TABLE [Auditoria] (
  [id] INTEGER IDENTITY(1,1) PRIMARY KEY,
  [UsuarioSys] NVARCHAR(255) NOT NULL,
  [accion] NVARCHAR(255),
  [fecha] DATETIME DEFAULT GETDATE()
)
GO

ALTER TABLE [Pedidos] ADD CONSTRAINT [pedido_mesa] FOREIGN KEY ([mesa_id]) REFERENCES [Mesas] ([id])
GO

ALTER TABLE [Detalle_Pedidos] ADD CONSTRAINT [pedido_detalle] FOREIGN KEY ([pedido_id]) REFERENCES [Pedidos] ([id])
GO

ALTER TABLE [Detalle_Pedidos] ADD CONSTRAINT [producto_detalle] FOREIGN KEY ([producto_id]) REFERENCES [Productos] ([id])
GO

ALTER TABLE [Productos] ADD CONSTRAINT [producto_categoria] FOREIGN KEY ([categoria_id]) REFERENCES [Categoria] ([id])
GO

ALTER TABLE [Pagos] ADD CONSTRAINT [pago_pedido] FOREIGN KEY ([pedido_id]) REFERENCES [Pedidos] ([id])
GO



USE bdRestaurante;
-- Dar permisos para ejecutar los procedimientos almacenados
GRANT EXECUTE ON inicioSesion TO adminRes, camarero, cajero, cocina;
GRANT EXECUTE ON cerrarSesion TO adminRes, camarero, cajero, cocina;

-- Dar permisos para insertar en la tabla Auditoria
GRANT INSERT ON Auditoria TO adminRes, camarero, cajero, cocina;