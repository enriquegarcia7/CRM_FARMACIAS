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

if messages:
    for msg in messages:
        msg_id = msg['id']
        attachments = gmail.get_attachments(msg_id)

        for att in attachments:
            filename = att['filename']
            if filename.lower().endswith(('.xlsx', '.xls')) and 'mediven' in filename.lower():
                print(f"Archivo: {filename}\n")

                # Leer Excel con la fila 8 como header
                df = pd.read_excel(BytesIO(att['data']), header=8)

                # Normalizar columnas
                df.columns = df.columns.str.lower().str.strip()

                print(f"Columnas encontradas: {list(df.columns)}\n")

                # Verificar si existe columna barcode
                if 'barcode' in df.columns:
                    print("✓ Columna 'barcode' encontrada!")

                    # Contar valores no nulos
                    total_filas = len(df)
                    con_barcode = df['barcode'].notna().sum()
                    sin_barcode = df['barcode'].isna().sum()

                    print(f"\nTotal filas: {total_filas}")
                    print(f"Con BARCODE: {con_barcode} ({con_barcode*100/total_filas:.1f}%)")
                    print(f"Sin BARCODE: {sin_barcode} ({sin_barcode*100/total_filas:.1f}%)")

                    # Mostrar primeros 20 barcodes no nulos
                    print("\n=== PRIMEROS 20 BARCODES NO NULOS ===")
                    barcodes_validos = df[df['barcode'].notna()]['barcode'].head(20)
                    for idx, barcode in enumerate(barcodes_validos, 1):
                        print(f"{idx}. {barcode}")

                    # Mostrar primeras 10 filas con descripcion y barcode
                    print("\n=== PRIMERAS 10 PRODUCTOS (Descripcion + BARCODE) ===")
                    for idx, row in df.head(10).iterrows():
                        desc = str(row.get('descripcion', 'N/A'))[:40]
                        barcode = row.get('barcode', 'N/A')
                        print(f"{desc:40} | BARCODE: {barcode}")

                else:
                    print("❌ Columna 'barcode' NO encontrada")

                exit(0)

print('No se encontró archivo de Mediven')
