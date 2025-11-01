import pandas as pd
import logging
from decimal import Decimal
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class ExcelOfferParser:
    COLUMN_MAPPINGS = {
        'producto': ['producto', 'medicamento', 'item', 'descripcion', 'nombre'],
        'codigo': ['codigo', 'código', 'sku', 'cod', 'code'],
        'precio_normal': ['precio', 'precio normal', 'pvp', 'valor'],
        'precio_oferta': ['oferta', 'precio oferta', 'promoción', 'descuento'],
        'descuento': ['desc', 'descuento', '%', 'porcentaje'],
        'laboratorio': ['laboratorio', 'lab', 'proveedor', 'marca'],
        'vigencia': ['vigencia', 'válido hasta', 'fecha', 'vencimiento']
    }

    def __init__(self, file_data, filename='unknown.xlsx', metadata=None):
        self.file_data = file_data
        self.filename = filename
        self.metadata = metadata or {}
        self.df = None
        self.offers = []

    def parse(self):
        try:
            if isinstance(self.file_data, bytes):
                self.df = pd.read_excel(self.file_data, engine='openpyxl')
            else:
                self.df = pd.read_excel(self.file_data)

            logger.info(f"📊 Excel: {len(self.df)} rows, {len(self.df.columns)} cols")
            self.df.columns = self.df.columns.str.lower().str.strip()
            column_map = self._detect_columns()

            if not column_map.get('producto'):
                raise ValueError("No 'producto' column detected")

            self.offers = self._extract_offers(column_map)
            logger.info(f"✓ {len(self.offers)} offers from {self.filename}")
            return self.offers
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise

    def _detect_columns(self):
        column_map = {}
        for key, variations in self.COLUMN_MAPPINGS.items():
            for col in self.df.columns:
                if any(var in col for var in variations):
                    column_map[key] = col
                    break
        return column_map

    def _extract_offers(self, column_map):
        offers = []
        laboratorio = self._extract_laboratorio()

        for idx, row in self.df.iterrows():
            try:
                producto = str(row.get(column_map.get('producto', ''), '')).strip()
                if not producto or producto.lower() in ['nan', 'none', '']:
                    continue

                codigo = str(row.get(column_map.get('codigo', ''), '')).strip()
                precio_normal = self._parse_price(row.get(column_map.get('precio_normal', '')))
                precio_oferta = self._parse_price(row.get(column_map.get('precio_oferta', '')))

                if precio_oferta == 0 and column_map.get('descuento'):
                    desc_pct = self._parse_percentage(row.get(column_map['descuento']))
                    if desc_pct > 0 and precio_normal > 0:
                        precio_oferta = precio_normal * (1 - desc_pct / 100)

                if precio_normal > 0 and precio_oferta > 0:
                    descuento = ((precio_normal - precio_oferta) / precio_normal) * 100
                else:
                    descuento = 0

                vigencia = self._parse_date(row.get(column_map.get('vigencia', '')))
                if not vigencia:
                    vigencia = datetime.now().date() + timedelta(days=30)

                offers.append({
                    'producto': producto,
                    'codigo': codigo if codigo and codigo != 'nan' else None,
                    'laboratorio': laboratorio,
                    'precio_normal': float(precio_normal),
                    'precio_oferta': float(precio_oferta) if precio_oferta > 0 else float(precio_normal),
                    'descuento': round(descuento, 2),
                    'fecha_inicio': datetime.now().date(),
                    'fecha_fin': vigencia,
                    'activa': True,
                    'source_file': self.filename,
                    'source_email': self.metadata.get('sender', 'Unknown'),
                })
            except Exception as e:
                logger.warning(f"Error row {idx}: {e}")
                continue

        return offers

    def _extract_laboratorio(self):
        sender = self.metadata.get('sender', '')
        if '@' in sender:
            domain = sender.split('@')[1].split('.')[0]
            return domain.title()

        filename_clean = self.filename.lower().replace('.xlsx', '').replace('.xls', '')
        known_labs = ['lab chile', 'medisupply', 'farmalab', 'pharma plus', 'biomed']

        for lab in known_labs:
            if lab in filename_clean:
                return lab.title()

        first_word = filename_clean.split('_')[0].split('-')[0]
        return first_word.title() if first_word else 'Laboratorio Desconocido'

    def _parse_price(self, value):
        if pd.isna(value):
            return 0
        price_str = str(value).strip()
        price_str = re.sub(r'[$\s]', '', price_str)
        price_str = price_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(price_str)
        except:
            return 0

    def _parse_percentage(self, value):
        if pd.isna(value):
            return 0
        pct_str = str(value).replace('%', '').strip()
        try:
            return float(pct_str)
        except:
            return 0

    def _parse_date(self, value):
        if pd.isna(value) or not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        date_str = str(value).strip()
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
