"""
╔══════════════════════════════════════════════════════════════════╗
║           MONOCHROME FLAC DOWNLOADER                             ║
║                                                                  ║
║  Descarga automática de archivos FLAC desde monochrome.tf        ║
║  usando Playwright para automatizar el navegador.                ║
║                                                                  ║
║  Requisitos:                                                     ║
║    pip install playwright httpx                                  ║
║    playwright install chromium                                   ║
║                                                                  ║
║  Uso:                                                            ║
║    1. Crea un archivo listado.json con los títulos a buscar      ║
║    2. Ejecuta: python musicflac.py                               ║
║    3. Los archivos se guardan en la carpeta descargas_flac/      ║
╚══════════════════════════════════════════════════════════════════╝

"""

import asyncio   # Para ejecutar código asíncrono (async/await)
import os        # Para crear carpetas y manejar rutas de archivos
import re        # Para limpiar nombres de archivo con expresiones regulares
import json      # Para leer el archivo listado.json
import httpx     # Cliente HTTP para descargar los archivos FLAC
from playwright.async_api import async_playwright  # Automatización del navegador
from urllib.parse import quote                     # Para codificar URLs correctamente (%20 en vez de +)


# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════

# Lee los títulos de canciones desde listado.json
# Formato esperado del JSON: ["Canción 1", "Canción 2", ...]
with open("listado.json", "r", encoding="utf-8") as f:
    TITULOS = json.load(f)

CARPETA = "descargas_flac"        # Carpeta donde se guardarán los archivos descargados
BASE_URL = "https://monochrome.tf" # URL base del sitio de streaming


# ══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════

def limpiar_nombre(nombre):
    """
    Elimina caracteres inválidos para nombres de archivo en Windows/Linux.
    
    Los caracteres  \\ / * ? : " < > |  no están permitidos en nombres de archivo.
    Los reemplaza por guion bajo (_).
    
    Args:
        nombre (str): Nombre original de la canción.
    
    Returns:
        str: Nombre limpio y seguro para usar como nombre de archivo.
    
    Ejemplo:
        "Do I Wanna Know?" → "Do I Wanna Know_"
        "AC/DC: Rock" → "AC_DC_ Rock"
    """
    return re.sub(r'[\\/*?:"<>|]', "_", nombre)


# ══════════════════════════════════════════════════════════════════
# DESCARGA DEL ARCHIVO FLAC
# ══════════════════════════════════════════════════════════════════

async def descargar_flac(url, titulo, cookies=None):
    """
    Descarga un archivo FLAC desde una URL y lo guarda en disco.
    
    Usa httpx en modo streaming para no cargar todo el archivo en memoria
    de una sola vez, lo que permite descargar archivos grandes sin problemas.
    
    Si ya existe un archivo con el mismo nombre, agrega un contador
    al final para no sobreescribir (_1, _2, etc.).
    
    Args:
        url (str):     URL directa del archivo FLAC a descargar.
        titulo (str):  Título de la canción (se usa como nombre del archivo).
        cookies (dict): Cookies de sesión del navegador, necesarias para
                        autenticar la descarga con el servidor.
    
    Returns:
        bool: True si la descarga fue exitosa, False si hubo un error.
    """
    # Construir la ruta del archivo de destino
    nombre = limpiar_nombre(titulo) + ".flac"
    ruta = os.path.join(CARPETA, nombre)

    # Evitar sobreescribir archivos existentes agregando sufijo numérico
    contador = 1
    base = ruta.replace(".flac", "")
    while os.path.exists(ruta):
        ruta = f"{base}_{contador}.flac"
        contador += 1

    print(f"  ⬇️  Descargando: {url[:80]}...")
    try:
        # Abre un cliente HTTP con timeout de 2 minutos y seguimiento de redirecciones
        async with httpx.AsyncClient(timeout=120, follow_redirects=True, cookies=cookies) as client:
            # stream=True descarga en trozos sin cargar todo en RAM
            async with client.stream("GET", url) as r:
                if r.status_code == 200:
                    # Escribe el archivo en disco trozo a trozo (8KB por vez)
                    with open(ruta, "wb") as f:
                        async for chunk in r.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                    size = os.path.getsize(ruta) / 1024 / 1024
                    print(f"  ✅ Guardado: {ruta} ({size:.2f} MB)")
                    return True
                else:
                    print(f"  ❌ Error HTTP {r.status_code}")
                    return False
    except Exception as e:
        print(f"  ❌ Error descargando: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# BÚSQUEDA Y CAPTURA DE URL
# ══════════════════════════════════════════════════════════════════

async def buscar_y_descargar(titulo, page, context):
    """
    Busca una canción en monochrome.tf y captura la URL del archivo FLAC.
    
    El proceso es:
      1. Navega a la URL de búsqueda del título.
      2. Instala un interceptor de red para capturar URLs de audio.
      3. Hace click derecho en el primer resultado de búsqueda.
      4. Selecciona "Download" en el menú contextual del sitio.
      5. El sitio genera una petición al servidor de audio → el interceptor la captura.
      6. Retorna las URLs capturadas.
    
    Por qué este enfoque:
      Monochrome.tf es una SPA (Single Page App) que renderiza todo con JavaScript.
      Scrapy o requests simples no pueden ejecutar JS, por eso se usa Playwright
      (navegador real). Las URLs de audio son temporales y se generan dinámicamente,
      por eso hay que interceptar las peticiones de red en tiempo real.
    
    Args:
        titulo (str):    Título de la canción a buscar.
        page:            Objeto Page de Playwright (la pestaña del navegador).
        context:         Contexto del navegador (para acceder a cookies).
    
    Returns:
        list: Lista de URLs FLAC capturadas. Normalmente contiene 1 elemento.
              Retorna lista vacía si no se encontró nada.
    """
    flac_urls = []  # Acumula las URLs de audio interceptadas

    # ── Interceptor de red ──────────────────────────────────────
    # Esta función se ejecuta automáticamente cada vez que el navegador
    # hace cualquier petición HTTP mientras estamos en la página.
    async def capturar_request(request):
        url = request.url
        # Filtra solo peticiones que parezcan archivos de audio FLAC
        if ".flac" in url or ("audio" in url.lower() and "tidal" in url.lower()):
            print(f"  🎯 URL capturada: {url[:80]}")
            if url not in flac_urls:  # Evitar duplicados
                flac_urls.append(url)

    # Registrar el interceptor antes de navegar
    page.on("request", capturar_request)

    # ── Navegación a la búsqueda ────────────────────────────────
    # quote() codifica el título para URL: "Afro Soul" → "Afro%20Soul"
    # (el sitio requiere %20 en vez de + para los espacios)
    query = quote(titulo)
    url_busqueda = f"{BASE_URL}/search/{query}"
    print(f"\n🔍 Buscando: {titulo}")

    # Espera a que la página cargue completamente (incluyendo el JS)
    await page.goto(url_busqueda, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(3)  # Pausa extra para asegurar que el JS terminó de renderizar

    # ── Interacción con el primer resultado ─────────────────────
    try:
        # Selector CSS: ".track-item" coincide con cada fila de resultado de búsqueda
        # (visto en el HTML: <div class="track-item" data-track-id="...">)
        primer_track = page.locator(".track-item").first
        count = await primer_track.count()

        if count == 0:
            print(f"  ❌ No se encontraron resultados para: {titulo}")
            page.remove_listener("request", capturar_request)
            return []

        # Click derecho abre el menú contextual personalizado del sitio
        # (definido en el HTML como <div id="context-menu">)
        await primer_track.click(button="right")
        print(f"  🖱️  Click derecho en primer resultado")
        await asyncio.sleep(1)  # Esperar que aparezca el menú

        # Buscar la opción "Download" dentro del menú contextual
        # Selector exacto tomado del HTML: <li data-action="download">Download</li>
        download_option = page.locator('#context-menu li[data-action="download"]')
        if await download_option.count() > 0:
            await download_option.click()
            print(f"  📥 Click en 'Download' del menú")
            # Esperar a que el sitio genere y ejecute la petición de descarga
            await asyncio.sleep(5)
        else:
            print(f"  ⚠️ No se encontró opción Download en el menú")

    except Exception as e:
        print(f"  ❌ Error al interactuar: {e}")

    # Desregistrar el interceptor para no acumular listeners entre canciones
    page.remove_listener("request", capturar_request)
    return flac_urls


# ══════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════

async def main():
    """
    Función principal que orquesta todo el proceso de descarga.
    
    Flujo:
      1. Crea la carpeta de destino si no existe.
      2. Abre un navegador Chromium visible (headless=False).
      3. Carga la página principal del sitio para inicializar cookies/sesión.
      4. Itera sobre cada título del listado.json.
      5. Para cada título: busca, captura la URL y descarga el FLAC.
      6. Cierra el navegador al terminar.
    
    Por qué headless=False (navegador visible):
      Permite ver qué está pasando en tiempo real para depurar problemas.
      También algunos sitios bloquean navegadores headless; visible es más confiable.
    """
    # Crear carpeta de descargas si no existe
    os.makedirs(CARPETA, exist_ok=True)
    print(f"📋 {len(TITULOS)} canciones cargadas desde listado.json\n")

    async with async_playwright() as p:
        # Lanza Chromium con interfaz visual
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Cargar la página principal primero para inicializar la sesión del sitio
        # (cookies, tokens internos, etc.)
        await page.goto(BASE_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # ── Procesar cada canción del listado ───────────────────
        for titulo in TITULOS:
            try:
                # Buscar la canción y capturar la URL del FLAC
                flac_urls = await buscar_y_descargar(titulo, page, context)

                if flac_urls:
                    # Extraer las cookies actuales del navegador
                    # (necesarias para autenticar la descarga con httpx)
                    cookies = {c["name"]: c["value"] for c in await context.cookies()}
                    # Descargar solo la primera URL encontrada
                    await descargar_flac(flac_urls[0], titulo, cookies)
                else:
                    print(f"  ❌ No se capturó URL para: {titulo}")

            except Exception as e:
                # Si una canción falla, continúa con la siguiente en vez de parar todo
                print(f"  ❌ Error con '{titulo}': {e}")

            # Pausa entre canciones para no saturar el servidor
            await asyncio.sleep(2)

        await browser.close()

    print(f"\n🎉 Terminado. Archivos guardados en: {CARPETA}/")


# ══════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # asyncio.run() ejecuta la función async main() en el event loop
    asyncio.run(main())
