# Fragmento que cargan los hooks de este directorio: define PYTHON con el intérprete del
# entorno virtual del proyecto, que es el que tiene instalado Ruff. Git ejecuta los hooks
# desde la raíz del repositorio y con sh, también en Windows.
if [ -x .venv/Scripts/python.exe ]; then
    PYTHON=.venv/Scripts/python.exe
elif [ -x .venv/bin/python ]; then
    PYTHON=.venv/bin/python
else
    echo "No se encontró el entorno virtual .venv; ver la puesta en marcha en README.md." >&2
    exit 1
fi
