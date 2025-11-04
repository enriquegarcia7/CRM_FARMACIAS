import pdfplumber
import re
import logging
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PDFOfferParser:
    def __init__(self, file_data, filename='unknown.pdf', metadata=None):
        self.file_data = file_data
        self.filename = filename
        self.metadata = metadata or {}
        self.offers = []

    def parse(self):
        try:
            import io
            pdf_file = io.BytesIO(self.file_data) if isinstance(self.file_data, bytes) else self.file_data
            pdf = pdfplumber.open(pdf_file)
            laboratorio = self._extract_laboratorio(pdf)

            tables_found = False
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    tables_found = True
                    for table in tables:
                        self._process_table(table, laboratorio)

            if not tables_found:
                logger.info(f"📄 No tables in {self.filename}, processing text")
                text = "".join([page.extract_text() or "" for page in pdf.pages])
                self._process_text(text, laboratorio)

            pdf.close()
            logger.info(f"✓ {len(self.offers)} offers from PDF {self.filename}")
            return self.offers
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise

    def _extract_laboratorio(self, pdf):
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        match = re.search(r'laboratorio[:\s]+([a-záéíóú\s]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        filename_clean = self.filename.lower().replace('.pdf', '')
        first_word = filename_clean.split('_')[0].split('-')[0]
        return first_word.title() if first_word else 'Laboratorio Desconocido'

    def _process_table(self, table, laboratorio):
        if not table or len(table) < 2:
            return

        headers = [str(h).lower().strip() if h else '' for h in table[0]]
        producto_idx = self._find_column_index(headers, ['producto', 'medicamento', 'item'])
        precio_normal_idx = self._find_column_index(headers, ['precio', 'pvp', 'valor'])
        precio_oferta_idx = self._find_column_index(headers, ['oferta', 'promoción', 'descuento'])

        if producto_idx is None:
            return

        for row in table[1:]:
            try:
                producto = str(row[producto_idx] if producto_idx < len(row) else '').strip()
                if not producto or producto.lower() in ['nan', 'none', '', 'null']:
                    continue

                precio_normal = 0
                precio_oferta = 0

                if precio_normal_idx is not None and precio_normal_idx < len(row):
                    precio_normal = self._parse_price(row[precio_normal_idx])
                if precio_oferta_idx is not None and precio_oferta_idx < len(row):
                    precio_oferta = self._parse_price(row[precio_oferta_idx])

                if precio_normal == 0:
                    continue
                if precio_oferta == 0:
                    precio_oferta = precio_normal

                descuento = 0
                if precio_normal > 0 and precio_oferta < precio_normal:
                    descuento = ((precio_normal - precio_oferta) / precio_normal) * 100

                self.offers.append({
                    'producto': producto,
                    'codigo': None,
                    'laboratorio': laboratorio,
                    'precio_normal': float(precio_normal),
                    'precio_oferta': float(precio_oferta),
                    'descuento': round(descuento, 2),
                    'fecha_inicio': datetime.now().date(),
                    'fecha_fin': datetime.now().date() + timedelta(days=30),
                    'activa': True,
                    'source_file': self.filename,
                    'source_email': self.metadata.get('sender', 'Unknown'),
                })
            except Exception as e:
                logger.warning(f"Error processing PDF row: {e}")
                continue

    def _process_text(self, text, laboratorio):
        pattern = r'([A-Za-záéíóúñ\s\d]+mg?)\s+\$?([\d.,]+)\s+\$?([\d.,]+)?'
        matches = re.findall(pattern, text)

        for match in matches:
            try:
                producto = match[0].strip()
                precio_normal = self._parse_price(match[1])
                precio_oferta = self._parse_price(match[2]) if len(match) > 2 and match[2] else precio_normal

                if precio_normal == 0:
                    continue

                descuento = 0
                if precio_normal > 0 and precio_oferta < precio_normal:
                    descuento = ((precio_normal - precio_oferta) / precio_normal) * 100

                self.offers.append({
                    'producto': producto,
                    'codigo': None,
                    'laboratorio': laboratorio,
                    'precio_normal': float(precio_normal),
                    'precio_oferta': float(precio_oferta),
                    'descuento': round(descuento, 2),
                    'fecha_inicio': datetime.now().date(),
                    'fecha_fin': datetime.now().date() + timedelta(days=30),
                    'activa': True,
                    'source_file': self.filename,
                    'source_email': self.metadata.get('sender', 'Unknown'),
                })
            except Exception as e:
                logger.warning(f"Error in PDF text: {e}")
                continue

    def _find_column_index(self, headers, variations):
        for i, header in enumerate(headers):
            if any(var in header for var in variations):
                return i
        return None

    def _parse_price(self, value):
        if not value:
            return 0
        price_str = str(value).strip()
        price_str = re.sub(r'[$\s]', '', price_str)
        price_str = price_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(price_str)
        except:
            return 0
