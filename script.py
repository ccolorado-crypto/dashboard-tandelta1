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
                    continue # Saltamos la cabecera
                
                columnas = linea.strip().split('\t')
                if len(columnas) < 10:
                    continue
                
                try:
                    # Extraer ID de variable, fecha y valor limpiando comillas
                    variable_id = int(columnas[6].replace('"', '').strip())
                    fecha_hora = columnas[7].replace('"', '').strip()
                    valor = float(columnas[9].replace('"', '').strip())
                    
                    # Quedarnos solo con el día YYYY-MM-DD
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

    # Calcular las métricas por día
    resultados = []
    for fecha, variables in datos_por_dia.items():
        tan = variables['tan_delta']
        temp = variables['temp_aceite']
        
        resultados.append({
            'fecha': fecha,
            'tan_min': round(min(tan), 2) if tan else 0,
            'tan_max': round(max(tan), 2) if tan else 0,
            'tan_prom': round(sum(tan) / len(tan), 2) if tan else 0,
            'tan_suma': round(sum(tan), 2) if tan else 0, # Tiempo de operación
            'temp_min': round(min(temp), 2) if temp else 0,
            'temp_max': round(max(temp), 2) if temp else 0,
            'temp_prom': round(sum(temp) / len(temp), 2) if temp else 0,
        })
    
    # Ordenar cronológicamente las fechas
    resultados.sort(key=lambda x: x['fecha'])

    # Construir las filas de la tabla en HTML
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

    # Convertir listas a strings en formato JSON para JavaScript
    str_fechas = json.dumps([r['fecha'] for r in resultados])
    str_promedios_tan = json.dumps([r['tan_prom'] for r in resultados])
    str_promedios_temp = json.dumps([r['temp_prom'] for r in resultados])
    str_suma_tan = json.dumps([r['tan_suma'] for r in resultados])

    print("⏳ Generando el archivo HTML...")

    # Plantilla HTML base (A prueba de fallos de strings de Python)
    html_template = """<!DOCTYPE html>
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
                        __FILAS_TABLA__
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const fechas = __FECHAS__;
        const promedios_tan = __PROMEDIOS_TAN__;
        const promedios_temp = __PROMEDIOS_TEMP__;
        const suma_tan = __SUMA_TAN__;

        const ctxPromedios = document.getElementById('graficoPromedios').getContext('2d');
        new Chart(ctxPromedios, {
            type: 'line',
            data: {
                labels: fechas,
                datasets: [
                    { label: 'Promedio Tan Delta', data: promedios_tan, borderColor: '#4f46e5', tension: 0.1 },
                    { label: 'Promedio Temp Aceite', data: promedios_temp, borderColor: '#10b981', tension: 0.1 }
                ]
            }
        });

        const ctxOperacion = document.getElementById('graficoOperacion').getContext('2d');
        new Chart(ctxOperacion, {
            type: 'bar',
            data: {
                labels: fechas,
                datasets: [{ label: 'Operación Total', data: suma_tan, backgroundColor: '#f59e0b' }]
            }
        });
    </script>
</body>
</html>"""

    # Reemplazo seguro usando etiquetas únicas
    html_final = html_template.replace("__FILAS_TABLA__", filas_tabla_html)
    html_final = html_final.replace("__FECHAS__", str_fechas)
    html_final = html_final.replace("__PROMEDIOS_TAN__", str_promedios_tan)
    html_final = html_final.replace("__PROMEDIOS_TEMP__", str_promedios_temp)
    html_final = html_final.replace("__SUMA_TAN__", str_suma_tan)

    # Escribir el archivo final index.html
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(html_final)
    
    print(f"✅ ¡Éxito! Tu dashboard ha sido creado en: {os.path.abspath(archivo_salida)}")

# ==========================================
# Punto de entrada (Estructura de Carpetas)
# ==========================================
if __name__ == "__main__":
    # 1. Asegurar que la carpeta 'public' exista
    if not os.path.exists('public'):
        os.makedirs('public')

    # 2. Buscar archivos .gz dentro de la carpeta 'data'
    archivos_gz = glob.glob('data/*.gz')
    
    if not archivos_gz:
        print("❌ ERROR: No se encontró ningún archivo comprimido (.gz) en la carpeta 'data'.")
        print("Por favor, sube tu archivo a la carpeta 'data/' antes de ejecutar.")
    else:
        # 3. Ordenar por fecha de modificación para tomar el más reciente subido
        archivos_gz.sort(key=os.path.getmtime, reverse=True)
        archivo_detectado = archivos_gz[0]
        
        print(f"🔎 ¡Archivo detectado!: {archivo_detectado}")
        # 4. Procesar y guardar directamente en public/index.html
        generar_dashboard(archivo_detectado, 'public/index.html')
