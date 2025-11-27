from core.models import OfertaLaboratorio, ProductoCatalogo, Proveedor

try:
    prov = Proveedor.objects.get(nombre='Provefarma')
    ofertas_prov = OfertaLaboratorio.objects.filter(producto_catalogo__proveedor=prov)

    print(f'\n✅ Ofertas de Provefarma: {ofertas_prov.count()}\n')

    print('Primeras 10 ofertas:')
    for oferta in ofertas_prov[:10]:
        nombre = oferta.producto_catalogo.nombre[:50]
        lab = oferta.laboratorio.nombre
        precio = oferta.precio_oferta if oferta.precio_oferta > 0 else oferta.precio_normal
        print(f'  - {nombre:50} | Lab: {lab:20} | ${precio}')

    labs = set(ofertas_prov.values_list('laboratorio__nombre', flat=True))
    print(f'\n📊 Total laboratorios únicos: {len(labs)}')
    print(f'Ejemplos: {list(labs)[:15]}')

except Proveedor.DoesNotExist:
    print('❌ Proveedor "Provefarma" no encontrado')
