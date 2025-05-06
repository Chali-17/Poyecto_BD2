CREATE TABLE [Pedidos] (
  [id] integer PRIMARY KEY,
  [UsuarioSys] nvarchar(255) NOT NULL,
  [mesa_id] integer NOT NULL,
  [fecha_pedido] timestamp,
  [estado] nvarchar(255)
)
GO

CREATE TABLE [Productos] (
  [id] integer PRIMARY KEY,
  [nombre] nvarchar(255),
  [precio] decimal(10,2),
  [categoria_id] integer NOT NULL
)
GO

CREATE TABLE [Categoria] (
  [id] integer PRIMARY KEY,
  [nombre] nvarchar(255)
)
GO

CREATE TABLE [Detalle_Pedidos] (
  [id] integer PRIMARY KEY,
  [pedido_id] integer NOT NULL,
  [producto_id] integer NOT NULL,
  [cantidad] integer,
  [subtotal] decimal(10,2)
)
GO

CREATE TABLE [Pagos] (
  [id] integer PRIMARY KEY,
  [pedido_id] integer NOT NULL,
  [UsuarioSys] nvarchar(255) NOT NULL,
  [monto] decimal(10,2),
  [metodo_pago] nvarchar(255),
  [fecha_pago] timestamp
)
GO

CREATE TABLE [Mesas] (
  [id] integer PRIMARY KEY,
  [numero_mesa] integer NOT NULL,
  [estado] nvarchar(255)
)
GO

CREATE TABLE [Auditoria] (
  [id] integer PRIMARY KEY,
  [UsuarioSys] nvarchar(255) NOT NULL,
  [accion] nvarchar(255),
  [fecha] timestamp
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
