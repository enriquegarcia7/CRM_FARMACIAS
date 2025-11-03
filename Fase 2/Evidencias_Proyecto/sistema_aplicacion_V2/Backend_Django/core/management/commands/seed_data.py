from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import random
from core.models import Cliente, Producto, Proveedor, OfertaLaboratorio, Venta, DetalleVenta, SugerenciaCompra, Transaccion

class Command(BaseCommand):
    help = 'Poblar la base de datos SmartPharm con datos de prueba realistas'

    def handle(self, *args, **kwargs):
        self.stdout.write('🧹 Limpiando datos existentes...')
        Cliente.objects.all().delete()
        Producto.objects.all().delete()
        Proveedor.objects.all().delete()

        self.stdout.write('👥 Creando proveedores...')
        proveedores = self.crear_proveedores()

        self.stdout.write('💊 Creando productos...')
        productos = self.crear_productos(proveedores)

        self.stdout.write('🧑‍⚕️ Creando clientes...')
        clientes = self.crear_clientes()

        self.stdout.write('🏷️ Creando ofertas...')
        self.crear_ofertas(productos, proveedores)

        self.stdout.write('🛒 Creando ventas históricas...')
        self.crear_ventas(clientes, productos)

        self.stdout.write('📋 Creando sugerencias de compra...')
        self.crear_sugerencias(productos)

        self.stdout.write(self.style.SUCCESS('\n✅ Base de datos poblada exitosamente'))
        self.mostrar_resumen()

    def crear_proveedores(self):
        nombres_proveedores = [
            ('Lab Chile', 'ventas@labchile.cl', '+56222345678', '12345678-9'),
            ('MediSupply', 'contacto@medisupply.cl', '+56223456789', '23456789-0'),
            ('Farmalab', 'ventas@farmalab.cl', '+56224567890', '34567890-1'),
            ('Pharma Plus', 'info@pharmaplus.cl', '+56225678901', '45678901-2'),
            ('BioMed', 'ventas@biomed.cl', '+56226789012', '56789012-3')
        ]

        proveedores = []
        for nombre, email, telefono, rut in nombres_proveedores:
            prov = Proveedor.objects.create(
                nombre=nombre,
                rut=rut,
                contacto='Gerente de Ventas',
                telefono=telefono,
                correo=email,
                direccion=f'Av. Providencia {random.randint(1000, 3000)}, Santiago',
                activo=True
            )
            proveedores.append(prov)
            self.stdout.write(f'  ✓ {nombre}')

        return proveedores

    def crear_productos(self, proveedores):
        medicamentos = [
            ('Paracetamol 500mg', 'Analgésico', 3000, 2000, 'MED001'),
            ('Ibuprofeno 400mg', 'Antiinflamatorio', 4500, 3000, 'MED002'),
            ('Amoxicilina 500mg', 'Antibiótico', 8000, 6000, 'MED003'),
            ('Loratadina 10mg', 'Antihistamínico', 3500, 2500, 'MED004'),
            ('Omeprazol 20mg', 'Gastroprotector', 5000, 3500, 'MED005'),
            ('Cetirizina 10mg', 'Antialérgico', 3500, 2500, 'MED006'),
            ('Atorvastatina 20mg', 'Hipolipemiante', 6000, 4500, 'MED007'),
            ('Clonazepam 0.5mg', 'Ansiolítico', 5500, 4000, 'MED008'),
            ('Metformina 850mg', 'Antidiabético', 4000, 3000, 'MED009'),
            ('Salbutamol Inhalador', 'Broncodilatador', 12000, 9000, 'MED010'),
            ('Budesonida Nasal', 'Corticoide', 15000, 11000, 'MED011'),
            ('Diclofenaco 50mg', 'Antiinflamatorio', 4000, 3000, 'MED012'),
            ('Losartán 50mg', 'Antihipertensivo', 5500, 4000, 'MED013'),
            ('Ranitidina 150mg', 'Antiulceroso', 4500, 3200, 'MED014'),
            ('Levocetirizina 5mg', 'Antihistamínico', 4200, 3000, 'MED015')
        ]

        productos = []
        for i, (nombre, categoria, precio_venta, precio_costo, codigo) in enumerate(medicamentos):
            stock = random.randint(50, 500)
            prod = Producto.objects.create(
                codigo=codigo,
                descripcion=nombre,
                categoria=categoria,
                stock_actual=stock,
                stock_minimo=random.randint(20, 50),
                precio_venta=Decimal(str(precio_venta)),
                precio_costo=Decimal(str(precio_costo)),
                activo=True
            )
            productos.append(prod)
            self.stdout.write(f'  ✓ {nombre} (Stock: {stock})')

        return productos

    def crear_clientes(self):
        nombres_clientes = [
            ('María González', 'maria.gonzalez@email.com', '+56912345678', '11111111-1', 15, 2500000),
            ('Juan Pérez', 'juan.perez@email.com', '+56987654321', '22222222-2', 8, 1200000),
            ('Ana Silva', 'ana.silva@email.com', '+56923456789', '33333333-3', 3, 450000),
            ('Pedro Martínez', 'pedro.martinez@email.com', '+56934567890', '44444444-4', 12, 1850000),
            ('Carmen López', 'carmen.lopez@email.com', '+56945678901', '55555555-5', 7, 980000),
            ('Roberto Díaz', 'roberto.diaz@email.com', '+56956789012', '66666666-6', 2, 280000),
            ('Laura Fernández', 'laura.fernandez@email.com', '+56967890123', '77777777-7', 18, 3200000),
            ('Carlos Rojas', 'carlos.rojas@email.com', '+56978901234', '88888888-8', 4, 620000),
            ('Patricia Muñoz', 'patricia.munoz@email.com', '+56989012345', '99999999-9', 10, 1450000),
            ('Jorge Soto', 'jorge.soto@email.com', '+56990123456', '10101010-1', 6, 850000),
            ('Sofía Castro', 'sofia.castro@email.com', '+56901234567', '20202020-2', 1, 120000),
            ('Diego Ramírez', 'diego.ramirez@email.com', '+56912345670', '30303030-3', 14, 2100000),
            ('Valentina Torres', 'valentina.torres@email.com', '+56923456781', '40404040-4', 9, 1350000),
            ('Sebastián Morales', 'sebastian.morales@email.com', '+56934567892', '50505050-5', 11, 1650000),
            ('Camila Vargas', 'camila.vargas@email.com', '+56945678903', '60606060-6', 5, 750000)
        ]

        clientes = []
        for nombre, correo, telefono, rut, compras, monto in nombres_clientes:
            cliente = Cliente.objects.create(
                nombre=nombre,
                correo=correo,
                telefono=telefono,
                fecha_registro=timezone.now() - timedelta(days=random.randint(30, 365))
            )
            clientes.append(cliente)
            frecuente = "Frecuente" if compras >= 5 else "Normal"
            self.stdout.write(f'  ✓ {nombre} ({frecuente}, {compras} compras)')

        return clientes

    def crear_ofertas(self, productos, proveedores):
        contador = 0
        for _ in range(min(15, len(productos))):
            producto = random.choice(productos)
            proveedor = random.choice(proveedores)
            precio_normal = producto.precio_venta
            descuento = Decimal(str(random.choice([10, 15, 20, 25, 30])))
            precio_oferta = precio_normal * (Decimal('1') - descuento / Decimal('100'))

            OfertaLaboratorio.objects.create(
                proveedor=proveedor,
                producto=producto,
                precio_normal=precio_normal,
                precio_oferta=precio_oferta,
                descuento_porcentaje=descuento,
                fecha_vigencia=timezone.now().date() + timedelta(days=30),
                activa=True
            )
            contador += 1

        self.stdout.write(f'  ✓ {contador} ofertas activas creadas')

    def crear_ventas(self, clientes, productos):
        total_ventas = 0
        for mes in range(1, 11):  # Enero a Octubre 2025
            ventas_mes = random.randint(15, 25)
            for _ in range(ventas_mes):
                cliente = random.choice(clientes)
                fecha = timezone.make_aware(datetime(2025, mes, random.randint(1, 28)))

                venta = Venta.objects.create(
                    cliente=cliente,
                    fecha=fecha,
                    total=Decimal('0'),
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia']),
                    estado='completada'
                )

                # 1-5 productos por venta
                total = Decimal('0')
                for _ in range(random.randint(1, 5)):
                    producto = random.choice(productos)
                    cantidad = random.randint(1, 3)
                    precio = producto.precio_venta
                    subtotal = precio * cantidad

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal
                    )
                    total += subtotal

                venta.total = total
                venta.save()
                total_ventas += 1

        self.stdout.write(f'  ✓ {total_ventas} ventas históricas creadas')

    def crear_sugerencias(self, productos):
        tipos = [
            ('bajo_stock', 'Stock crítico - Reabastecer urgente', 'critica'),
            ('estacional', 'Temporada de gripe - Alta demanda esperada', 'alta'),
            ('epidemiologico', 'Alerta MINSAL - Aumento de casos respiratorios', 'alta'),
            ('bajo_stock', 'Producto de alta rotación - Stock preventivo', 'media'),
            ('estacional', 'Temporada primaveral - Alergias', 'media'),
            ('estacional', 'Invierno - Enfermedades respiratorias', 'alta')
        ]

        contador = 0
        for _ in range(20):
            tipo, razon, prioridad = random.choice(tipos)
            SugerenciaCompra.objects.create(
                producto=random.choice(productos),
                tipo=tipo,
                cantidad_sugerida=random.randint(100, 500),
                prioridad=prioridad,
                razon=razon,
                procesada=False
            )
            contador += 1

        self.stdout.write(f'  ✓ {contador} sugerencias de compra creadas')

    def mostrar_resumen(self):
        self.stdout.write('\n📊 RESUMEN DE DATOS CREADOS:')
        self.stdout.write(f'  • Proveedores: {Proveedor.objects.count()}')
        self.stdout.write(f'  • Productos: {Producto.objects.count()}')
        self.stdout.write(f'  • Clientes: {Cliente.objects.count()}')
        self.stdout.write(f'  • Ofertas: {OfertaLaboratorio.objects.count()}')
        self.stdout.write(f'  • Ventas: {Venta.objects.count()}')
        self.stdout.write(f'  • Detalles de venta: {DetalleVenta.objects.count()}')
        self.stdout.write(f'  • Sugerencias: {SugerenciaCompra.objects.count()}')
