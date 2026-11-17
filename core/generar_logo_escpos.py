"""
Regenera static/img/logo_pase_escpos.bin, el logo en modo raster ESC/POS.

El agente local imprime el pase en modo texto + un logo raster. Este script
deja el logo ya empaquetado en el comando GS v 0 (203 dpi, 1 bit por punto),
así el servidor no necesita Pillow ni decodificar PNG en tiempo de ejecución.

Uso (solo en desarrollo, requiere Pillow):

    python core/generar_logo_escpos.py

El archivo generado se versiona en el repositorio.
"""
import os

ALTO_DOTS = 120         # 15 mm a 203 dpi: el mismo alto que usa el PDF
UMBRAL = 168            # gris -> negro/blanco; el logo ya es binario
SALIDA = os.path.join("static", "img", "logo_pase_escpos.bin")
ENTRADA = os.path.join("static", "img", "logo_pase.png")


def generar(entrada=ENTRADA, salida=SALIDA, alto_dots=ALTO_DOTS):
    from PIL import Image

    imagen = Image.open(entrada).convert("L")
    alto_dots = max(1, int(alto_dots))
    ancho_dots = max(1, round(alto_dots * imagen.width / imagen.height))
    imagen = imagen.resize((ancho_dots, alto_dots), Image.LANCZOS)
    # 0 = punto negro, 255 = papel. En ESC/POS 1 = punto negro.
    mono = imagen.point(lambda p: 0 if p < UMBRAL else 255, mode="1")

    ancho_bytes = (ancho_dots + 7) // 8
    filas = []
    for y in range(alto_dots):
        fila = bytearray(ancho_bytes)
        for x in range(ancho_dots):
            if mono.getpixel((x, y)) == 0:
                fila[x // 8] |= 0x80 >> (x % 8)
        filas.append(bytes(fila))
    raster = b"".join(filas)

    comando = (
        b"\x1dv0\x00"                              # GS v 0, modo normal
        + bytes([ancho_bytes & 0xFF, ancho_bytes >> 8])
        + bytes([alto_dots & 0xFF, (alto_dots >> 8) & 0xFF])
        + raster
    )
    with open(salida, "wb") as fh:
        fh.write(comando)
    return salida, ancho_dots, alto_dots, len(comando)


if __name__ == "__main__":
    ruta, ancho, alto, tam = generar()
    print(f"OK -> {ruta} | {ancho}x{alto} dots | {tam} bytes")
