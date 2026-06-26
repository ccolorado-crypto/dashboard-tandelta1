name: Actualizar Dashboard Automáticamente

# Esto le dice al robot que se active SOLAMENTE cuando subas un archivo .gz
on:
  push:
    paths:
      - '**/*.gz'

permissions:
  contents: write # Permiso para que el robot guarde el nuevo HTML en tu repositorio

jobs:
  procesar-datos:
    runs-on: ubuntu-latest

    steps:
      - name: Clonar el repositorio
        uses: actions/checkout@v3

      - name: Instalar Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Ejecutar tu script de Python
        run: python script.py

      - name: Guardar y subir el nuevo index.html
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action Bot"
          git add index.html
          git commit -m "🤖 Dashboard actualizado con nuevos datos" || echo "No hay cambios"
          git push
