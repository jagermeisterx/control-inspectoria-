import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

FUENTE = Path("inf_matricula_curso_0_(12-08-2026).xls")
SALIDA = Path("alumnos_organizado_(12-08-2026).xlsx")

PARTICULAS = {
    "DE", "DEL", "DE LA", "DE LAS", "SAN", "SANTA", "VAN", "VON",
    "DI", "DA", "MAC", "MC", "LA", "LAS", "LOS", "EL",
}


def separar_nombre(nombre_completo):
    tokens = [t for t in re.split(r"\s+", str(nombre_completo).strip().upper()) if t]
    apellidos, nombres, componentes = [], [], 0
    restantes = list(tokens)
    while restantes and componentes < 2:
        if restantes[0] in PARTICULAS and len(restantes) > 1:
            apellidos.append(restantes.pop(0))
            while restantes and restantes[0] in PARTICULAS:
                apellidos.append(restantes.pop(0))
        apellidos.append(restantes.pop(0))
        componentes += 1
    nombres = restantes
    return " ".join(nombres), " ".join(apellidos)


def limpiar(valor):
    texto = str(valor).strip() if not pd.isna(valor) else ""
    return "" if texto in ("-", "nan", "None") else texto


def main():
    df = pd.read_html(str(FUENTE), encoding="ISO-8859-1")[1]
    wb = Workbook()
    ws = wb.active
    ws.title = "Alumnos"
    ws.append(["nombre", "apellido", "curso", "rut (opc.)", "apoderado (opc.)", "teléfono (opc.)"])
    for _, fila in df.iterrows():
        nombre, apellido = separar_nombre(fila[2])
        ws.append([
            nombre,
            apellido,
            limpiar(fila[4]),
            limpiar(fila[3]),
            limpiar(fila[15]),
            limpiar(fila[16]),
        ])
    for col in ("A", "B", "D", "E", "F"):
        ws.column_dimensions[col].width = 30
    ws.column_dimensions["C"].width = 20
    wb.save(SALIDA)
    print(f"Guardado: {SALIDA} ({ws.max_row - 1} alumnos)")


if __name__ == "__main__":
    main()
