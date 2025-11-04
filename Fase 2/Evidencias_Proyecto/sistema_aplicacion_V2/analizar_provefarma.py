import pandas as pd

archivo = '/tmp/provefarma.xlsx'

try:
    all_sheets = pd.read_excel(archivo, sheet_name=None, header=None)

    print(f'\n📄 Archivo analizado\n')
    print(f'📊 Total de hojas: {len(all_sheets)}\n')

    for sheet_name, df in list(all_sheets.items())[:3]:  # Solo primeras 3 hojas
        print(f'\n🔍 Hoja: "{sheet_name}"')
        print(f'   Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas\n')

        # Mostrar primeras 5 filas
        print('   Primeras 5 filas:')
        for idx in range(min(5, len(df))):
            row_data = [str(cell)[:30] for cell in df.iloc[idx].tolist()[:10]]
            print(f'   Fila {idx}: {row_data}')

        # Buscar la fila de headers
        print('\n   🔎 Buscando header...')
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            non_empty = row.notna().sum()
            if non_empty >= 3:
                row_lower = str(row.tolist()).lower()
                if any(keyword in row_lower for keyword in ['codigo', 'descriptor', 'precio', 'producto', 'laboratorio']):
                    row_text = ' | '.join([str(cell)[:25] for cell in row[:10] if pd.notna(cell)])
                    print(f'   ✅ POSIBLE HEADER EN FILA {idx} ({non_empty} cols): {row_text}')

        print('\n' + '=' * 100)

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
