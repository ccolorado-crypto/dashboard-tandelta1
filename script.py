import json
import gzip
from collections import defaultdict
import os
import glob 

def generar_dashboard(archivo_entrada, archivo_salida):
    datos_por_dia = defaultdict(lambda: {
        'tan_delta': [],
        'temp_aceite': []
    })

    print(f"⏳ Descomprimiendo y leyendo datos de: {archivo_entrada}...")

    try:
        with gzip.open(archivo_entrada, 'rt', encoding='utf-8') as f:
            for linea in f:
                if "datetimestamp" in linea:
                    continue 
                
                columnas = linea.strip().split('\t')
                if len(columnas) < 10:
                    continue
                
                try:
                    variable_id = int(columnas[6].replace('"', '').strip())
                    fecha_hora = columnas[7].replace('"', '').strip()
                    valor = float(columnas[9].replace('"', '').strip())
                    
                    fecha = fecha_hora.split(' ')[0]
                    
                    if variable_id == 4500:
                        datos_por_dia[fecha]['tan_delta'].append(valor)
                    elif variable_id == 61:
                        datos_por_dia[fecha]['temp_aceite'].append(valor)
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f"❌ ERROR al leer el archivo: {e}")
        return

    # Calcular las métricas
    resultados = []
    for fecha, variables in datos_por_dia.items():
        tan = variables['tan_delta']
        temp = variables['temp_aceite']
        
        resultados.append({
            'fecha': fecha,
            'tan_min': round(min(tan), 2) if tan else 0,
            'tan_max': round(max(tan), 2) if tan else 0,
            'tan_prom': round(sum(tan) / len(tan), 2) if tan else 0,
            'tan_suma': round(sum(tan), 2) if tan else 0,
            'temp_min': round(min(temp), 2) if temp else 0,
            'temp_max': round(max(temp), 2) if temp else 0,
            'temp_prom': round(sum(temp) / len(temp), 2) if temp else 0,
        })
    
    resultados.sort(key=lambda x: x['fecha'])

    # Crear las filas de la tabla
    filas_tabla_html = ""
    for r in resultados:
        filas_tabla_html += f"""
        <tr class="border-b text-center hover:bg-gray-50">
            <td class="p-3 font-semibold text-gray-700">{r['fecha']}</td>
            <td class="p-3 text-indigo-600">{r['tan_min']}</td>
            <td class="p-3 text-indigo-600">{r['tan_max']}</td>
            <td class="p-3 text-emerald-600">{r['temp_min']}</td>
            <td class="p-3 text-emerald-600">{r['temp_max']}</td>
        </tr>
        """

    # Extraemos los datos a formato JSON
    str_fechas = json.dumps([r['fecha'] for r in resultados])
    str_promedios_tan = json.dumps([r['tan_prom'] for r in resultados])
    str_promedios_temp = json.dumps([r['temp_prom'] for r in resultados])
    str_suma_tan = json.dumps([r['tan_suma'] for r in resultados])

    print("⏳ Generando el archivo HTML...")

    # Plantilla HTML inyectada directamente (sin replaces)
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Operación</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 p-8 font-sans">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-800 mb-8">Dashboard de Operación de Máquina</h1>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-bold text-gray-700 mb-4">Promedios Diarios</h2>
                <canvas id="graficoPromedios"></canvas>
            </div>
            <div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-bold text-gray-700 mb-4">Tiempo de Operación (Suma Tan Delta)</h2>
                <canvas id="graficoOperacion"></canvas>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="bg-gray-800 text-white p-4">
                <h2 class="text-xl font-bold">Resumen de Extremos por Día</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left">
                    <thead class="bg-gray-200 text-gray-600 uppercase text-center">
                        <tr>
                            <th class="p-3">Fecha</th>
                            <th class="p-3">Min Tan Delta</th>
                            <th class="p-3">Max Tan Delta</th>
                            <th class="p-3">Min Temp Aceite</th>
                            <th class="p-3">Max Temp Aceite</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_tabla_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const fechas = {str_fechas};
        const promedios_tan = {str_promedios_tan};
        const promedios_temp = {str_promedios_temp};
        const suma_tan = {str_suma_tan};

        const ctxPromedios = document.getElementById('graficoPromedios').getContext('2d');
        new Chart(ctxPromedios, {{
            type: 'line',
            data: {{
                labels: fechas,
                datasets: [
                    {{ label: 'Promedio Tan Delta', data: promedios_tan, borderColor: '#4f46e5', tension: 0.1 }},
                    {{ label: 'Promedio Temp Aceite', data: promedios_temp, borderColor: '#10b981', tension: 0.1 }}
                ]
            }}
        }});

        const ctxOperacion = document.getElementById('graficoOperacion').getContext('2d');
        new Chart(ctxOperacion, {{
            type: 'bar',
            data: {{
                labels: fechas,
                datasets: [{{ label: 'Operación Total', data: suma_tan, backgroundColor: '#f59e0b' }}]
            }}
        }});
    </script>
</body>
</html>"""

    # Guardar el HTML final
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ ¡Éxito! Tu dashboard ha sido creado en: {os.path.abspath(archivo_salida)}")

# ==========================================
# Punto de entrada
# ==========================================
if __name__ == "__main__":
    archivos_gz = glob.glob('*.gz')
    if not archivos_gz:
        print("❌ ERROR: No se encontró ningún archivo comprimido (.gz) en esta carpeta.")
    else:
        archivo_detectado = archivos_gz[0]
        print(f"🔎 ¡Archivo detectado automáticamente!: {archivo_detectado}")
        generar_dashboard(archivo_detectado, 'dashboard.html')