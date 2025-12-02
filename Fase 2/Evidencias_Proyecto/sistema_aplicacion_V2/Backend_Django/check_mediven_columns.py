#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')
django.setup()

from core.services.gmail_service import GmailService
import pandas as pd
from io import BytesIO

gmail = GmailService()
gmail._authenticate()

# Buscar emails con attachments
messages = gmail.get_messages('has:attachment (xlsx OR xls)', max_results=5)
print(f'Encontrados {len(messages)} emails con attachments')

if messages:
    for msg in messages:
        msg_id = msg['id']
        print(f'\n=== Analizando email: {msg_id} ===')

        attachments = gmail.get_attachments(msg_id)

        for att in attachments:
            filename = att['filename']
            if filename.lower().endswith(('.xlsx', '.xls')):
                print(f"\nArchivo: {filename}")
                print(f"Tamaño: {len(att['data'])} bytes")

                # Solo analizar archivos que parezcan de Mediven
                if 'mediven' not in filename.lower():
                    print('  -> No es de Mediven, skip')
                    continue

                # Leer Excel
                df = pd.read_excel(BytesIO(att['data']), header=None, nrows=30)

                print('\n=== PRIMERAS 20 FILAS (primeras 10 columnas) ===')
                for idx in range(min(20, len(df))):
                    row_values = []
                    for v in df.iloc[idx].values[:10]:
                        if pd.notna(v):
                            row_values.append(str(v)[:25])
                        else:
                            row_values.append('...')
                    if any(v != '...' for v in row_values):
                        print(f'{idx:2d}: {" | ".join(row_values)}')

                # Buscar fila con BARCODE
                print('\n=== BUSCANDO FILA CON "BARCODE" ===')
                for idx in range(min(30, len(df))):
                    row_text = ' '.join([str(v).upper() for v in df.iloc[idx].values if pd.notna(v)])
                    if 'BARCODE' in row_text:
                        print(f'✓ Encontrado en fila {idx}!')
                        print(f'Valores: {[str(v)[:30] for v in df.iloc[idx].values[:15] if pd.notna(v)]}')

                exit(0)
else:
    print('No se encontraron emails con attachments')
