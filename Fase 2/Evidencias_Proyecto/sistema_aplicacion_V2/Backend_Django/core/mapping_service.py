# core/mapping_service.py
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import re
from .models import Producto, ProductoCatalogo, ProductoProveedorMapping, Proveedor


class ProductMappingService:
    """
    Servicio de mapeo automático entre productos internos y catálogos de proveedores.

    Usa fuzzy matching para vincular productos con nombres diferentes:
    - "PARACETA.BE COM.500MG,16 ANDROMACO" (interno)
    - "PARACETAMOL COM 500 MG X 16 AND (BE)" (proveedor)
    """

    def __init__(self):
        self.CONFIDENCE_THRESHOLD_HIGH = 85  # Match excelente
        self.CONFIDENCE_THRESHOLD_MEDIUM = 70  # Match bueno
        self.CONFIDENCE_THRESHOLD_LOW = 60  # Match dudoso
        self.MIN_CONFIDENCE = 50  # Mínimo para considerar

    def normalize_text(self, text):
        """
        Normaliza texto para comparación:
        - Mayúsculas
        - Elimina caracteres especiales
        - Normaliza espacios
        - Normaliza abreviaturas comunes
        """
        if not text:
            return ""

        text = text.upper()

        # Normalizar abreviaturas farmacéuticas comunes
        replacements = {
            'PARACETA.': 'PARACETAMOL',
            'PARACET.': 'PARACETAMOL',
            'IBUPRO.': 'IBUPROFENO',
            'AMOXI.': 'AMOXICILINA',
            'COM.': 'COMPRIMIDO',
            'COM ': 'COMPRIMIDO ',
            'CAP.': 'CAPSULA',
            'TAB.': 'TABLETA',
            'JBE.': 'JARABE',
            'SUS.': 'SUSPENSION',
            'CR.': 'CREMA',
            'GEL.': 'GEL',
            'SOL.': 'SOLUCION',
            'AMP.': 'AMPOLLA',
            'X ': ' ',
            ' X': ' ',
            'MG,': 'MG ',
            'MG.': 'MG ',
            'ML.': 'ML ',
            'GR.': 'GR ',
            '(BE)': 'BIOEQUIVALENTE',
            ' BE ': ' BIOEQUIVALENTE ',
            'BE.': 'BIOEQUIVALENTE',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Eliminar caracteres especiales excepto números
        text = re.sub(r'[^A-Z0-9\s]', ' ', text)

        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def extract_key_features(self, text):
        """
        Extrae características clave del nombre del producto:
        - Principio activo
        - Dosis (números + unidad: 500MG, 100ML)
        - Presentación (COMPRIMIDO, JARABE, etc)
        - Cantidad (16, 30, etc)
        """
        normalized = self.normalize_text(text)

        # Extraer dosis (ej: 500MG, 100ML, 20GR)
        dosis_pattern = r'\d+\s*(?:MG|ML|GR|G|MCG|UI)'
        dosis = re.findall(dosis_pattern, normalized)

        # Extraer cantidad (número solo)
        cantidad_pattern = r'\b(\d+)\b'
        cantidades = re.findall(cantidad_pattern, normalized)

        # Palabras clave de forma farmacéutica
        formas = ['COMPRIMIDO', 'CAPSULA', 'TABLETA', 'JARABE', 'SUSPENSION',
                  'CREMA', 'GEL', 'SOLUCION', 'AMPOLLA', 'BIOEQUIVALENTE']
        forma_encontrada = [f for f in formas if f in normalized]

        return {
            'normalized': normalized,
            'dosis': dosis,
            'cantidades': cantidades,
            'formas': forma_encontrada
        }

    def calculate_similarity(self, producto_interno, producto_catalogo):
        """
        Calcula similitud entre producto interno y producto de catálogo.
        Retorna score 0-100.

        Combina múltiples métricas:
        - Similitud de texto completo (40%)
        - Coincidencia de dosis (30%)
        - Coincidencia de forma farmacéutica (20%)
        - Coincidencia de cantidad (10%)
        """
        # Extraer características
        feat_interno = self.extract_key_features(producto_interno.nombre)
        feat_catalogo = self.extract_key_features(producto_catalogo.nombre)

        # 1. Similitud de texto completo usando fuzzy matching (40%)
        text_similarity = fuzz.token_sort_ratio(
            feat_interno['normalized'],
            feat_catalogo['normalized']
        ) * 0.4

        # 2. Coincidencia de dosis (30%)
        dosis_score = 0
        if feat_interno['dosis'] and feat_catalogo['dosis']:
            # Si alguna dosis coincide exactamente
            if any(d in feat_catalogo['dosis'] for d in feat_interno['dosis']):
                dosis_score = 30
            else:
                # Coincidencia parcial
                dosis_score = 15

        # 3. Coincidencia de forma farmacéutica (20%)
        forma_score = 0
        if feat_interno['formas'] and feat_catalogo['formas']:
            if any(f in feat_catalogo['formas'] for f in feat_interno['formas']):
                forma_score = 20

        # 4. Coincidencia de cantidad (10%)
        cantidad_score = 0
        if feat_interno['cantidades'] and feat_catalogo['cantidades']:
            if any(c in feat_catalogo['cantidades'] for c in feat_interno['cantidades']):
                cantidad_score = 10

        total_score = text_similarity + dosis_score + forma_score + cantidad_score

        return min(100, max(0, total_score))

    def find_best_matches(self, producto_interno, proveedor=None, limit=5):
        """
        Encuentra los mejores matches para un producto interno.

        Args:
            producto_interno: Producto del inventario interno
            proveedor: Filtrar por proveedor específico (opcional)
            limit: Número máximo de matches a retornar

        Returns:
            Lista de tuplas (ProductoCatalogo, confidence_score)
        """
        # Query de productos de catálogo
        catalogo_query = ProductoCatalogo.objects.filter(activo=True)

        if proveedor:
            catalogo_query = catalogo_query.filter(proveedor=proveedor)

        matches = []

        for prod_catalogo in catalogo_query:
            similarity = self.calculate_similarity(producto_interno, prod_catalogo)

            # Solo considerar si supera el mínimo
            if similarity >= self.MIN_CONFIDENCE:
                matches.append({
                    'producto_catalogo': prod_catalogo,
                    'confidence': round(similarity, 2),
                    'proveedor': prod_catalogo.proveedor,
                    'codigo_proveedor': prod_catalogo.codigo,
                    'nombre_catalogo': prod_catalogo.nombre
                })

        # Ordenar por confianza descendente
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        return matches[:limit]

    def auto_map_product(self, producto_interno, min_confidence=None, auto_create=True):
        """
        Mapea automáticamente un producto interno a productos de catálogo.

        Args:
            producto_interno: Producto del inventario interno
            min_confidence: Confianza mínima para crear mapeo automático
            auto_create: Si True, crea mappings automáticamente

        Returns:
            Lista de mappings creados o encontrados
        """
        if min_confidence is None:
            min_confidence = self.CONFIDENCE_THRESHOLD_MEDIUM

        # Buscar mejores matches
        matches = self.find_best_matches(producto_interno, limit=10)

        mappings_created = []

        for match in matches:
            # Solo crear si supera la confianza mínima
            if match['confidence'] < min_confidence:
                continue

            # Verificar si ya existe el mapping
            existing = ProductoProveedorMapping.objects.filter(
                producto_interno=producto_interno,
                codigo_proveedor=match['codigo_proveedor'],
                proveedor=match['proveedor']
            ).first()

            if existing:
                # Actualizar confianza si es mayor
                if match['confidence'] > float(existing.confianza):
                    existing.confianza = match['confidence']
                    existing.mapeado_por = 'ml_actualizado'
                    existing.save()
                    mappings_created.append(existing)
            elif auto_create:
                # Crear nuevo mapping
                mapping = ProductoProveedorMapping.objects.create(
                    producto_interno=producto_interno,
                    codigo_proveedor=match['codigo_proveedor'],
                    proveedor=match['proveedor'],
                    nombre_en_catalogo=match['nombre_catalogo'],
                    confianza=match['confidence'],
                    mapeado_por='ml_auto',
                    activo=True,
                    notas=f"Mapeo automático ML (confianza: {match['confidence']}%)"
                )
                mappings_created.append(mapping)

        return mappings_created

    def auto_map_all_products(self, min_confidence=70, only_unmapped=True):
        """
        Mapea automáticamente todos los productos del inventario.

        Args:
            min_confidence: Confianza mínima para crear mappings
            only_unmapped: Si True, solo mapea productos sin mappings existentes

        Returns:
            Estadísticas del proceso
        """
        productos = Producto.objects.filter(activo=True)

        if only_unmapped:
            # Filtrar solo productos sin mappings activos
            productos = productos.filter(
                mappings__isnull=True
            ) | productos.filter(
                mappings__activo=False
            )
            productos = productos.distinct()

        stats = {
            'total_productos': productos.count(),
            'productos_mapeados': 0,
            'mappings_creados': 0,
            'productos_sin_match': 0,
            'errores': []
        }

        for producto in productos:
            try:
                mappings = self.auto_map_product(
                    producto,
                    min_confidence=min_confidence,
                    auto_create=True
                )

                if mappings:
                    stats['productos_mapeados'] += 1
                    stats['mappings_creados'] += len(mappings)
                    print(f"✅ {producto.codigo}: {len(mappings)} mappings creados (conf: {[m.confianza for m in mappings]})")
                else:
                    stats['productos_sin_match'] += 1
                    print(f"⚠️ {producto.codigo}: Sin matches con confianza >= {min_confidence}%")

            except Exception as e:
                stats['errores'].append({
                    'producto': producto.codigo,
                    'error': str(e)
                })
                print(f"❌ Error mapeando {producto.codigo}: {str(e)}")

        return stats


# Instancia global
mapping_service = ProductMappingService()
