"""
Script to find the correct header row in Provefarma Excel files
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')
django.setup()

from core.models import ArchivoProcesado
import pandas as pd
from io import BytesIO

# Get a Provefarma file
archivo = ArchivoProcesado.objects.filter(nombre_archivo__icontains='provefarma', nombre_archivo__icontains='.xlsx').first()

if archivo:
    print(f"\n📄 Analyzing: {archivo.nombre_archivo}")

    # Read file from database (assuming it's stored)
    # For now, let's try reading the first sheet with different header rows

    # Try to find the file in the email attachments
    from core.etl.gmail_connector import GmailConnector
    connector = GmailConnector()
    # ... this approach won't work easily

    print("\n⚠️ Need to check actual file structure")
    print("Expected headers: MUNDO | NOMBRE OFERTA O CAMPAÑA | CÓDIGO PROV | DESCRIPTOR | MACROCATEGORIA")
    print("\nCurrent header=8 gives: FARMA | OFERTA 72 HORAS - FARMA - VARIOS | ...")
    print("\nThe header row index needs to be adjusted!")

else:
    print("❌ No Provefarma .xlsx files found in database")

# Based on the debug output, let me analyze:
print("\n🔍 Analysis:")
print("- header=8 reads row index 8 as column names")
print("- This gives us product data as column names: 'FARMA', 'OFERTA 72 HORAS', 'METROPAST COM.500MG.20'")
print("- These are clearly DATA values, not headers")
print("\n💡 Solution: The actual header row with 'DESCRIPTOR', 'CÓDIGO PROV', etc. is at a DIFFERENT row")
print("   Try header=7, 6, 5, or even 9, 10 to find the real column names")
