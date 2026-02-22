
# 🎧 MONOCHROME FLAC DOWNLOADER

> Descarga automática de música en formato **FLAC lossless** a partir de una lista de títulos en JSON.

---

## 🚀 Qué hace este proyecto

Este proyecto automatiza un proceso muy simple pero poderoso:

1. Lee una lista de canciones desde un archivo `.json`
    
2. Busca cada título en la web **monochrome**
    
3. Captura la URL real del audio
    
4. Descarga el archivo `.flac` automáticamente
    

Todo de forma **recursiva y automatizada**.

---

## ❗ Importante (Cómo funciona realmente)

Este proyecto **NO exporta playlists por ti**.

El flujo real es:

### Parte del usuario (manual)

El usuario debe:

1. Obtener su lista de canciones desde cualquier plataforma  
    (Spotify, YouTube Music, Apple Music, etc.)
    
2. Exportarla como quiera (ejemplo: CSV desde un plugin)
    
3. Convertir esa lista manualmente a un archivo:
    

```json
[
  "Papaoutai",
  "Do I Wanna Know?",
  "Even (I'll Still Praise)"
]
```

Ese archivo debe llamarse:

```
listado.json
```

---

### Parte del programa (automática)

Una vez tengas el JSON listo, el script hace TODO:

- Busca cada canción en la web
    
- Automatiza el navegador
    
- Intercepta la descarga real
    
- Descarga los FLAC
    
- Guarda todo en una carpeta
    

Sin intervención manual.

---

## 🧠 Filosofía del proyecto

Este proyecto está enfocado en:

- Automatización real
    
- Scraping moderno con JS dinámico
    
- Descargas autenticadas
    
- Procesamiento masivo de música lossless
    

El objetivo es convertir una simple lista de texto en una colección FLAC completa.

---

## ⚙️ Requisitos

### Python

- Python 3.10+
    

### Dependencias

```bash
pip install playwright httpx
playwright install chromium
```

---

## ▶️ Uso

### 1️⃣ Crear tu listado.json

Ejemplo:

```json
[
  "Papaoutai",
  "Jesucristo Basta",
  "Mi Universo"
]
```

---

### 2️⃣ Ejecutar el script

```bash
python musicflac.py
```

---

### 3️⃣ Resultado

```
descargas_flac/
  ├── Papaoutai.flac
  ├── Jesucristo Basta.flac
  ├── Mi Universo.flac
```

---

## 🛠 Qué hace internamente

- Automatiza un navegador real con Playwright
    
- Maneja sitios SPA con JavaScript dinámico
    
- Intercepta requests de red en tiempo real
    
- Reutiliza cookies para descargas válidas
    
- Descarga archivos grandes en streaming
    

---

## 📦 Estructura del proyecto

```
.
├── musicflac.py
├── listado.json   ← entrada del usuario
├── README.md
└── descargas_flac/
```

---

## 🎯 Casos de uso

- Convertir listas musicales en FLAC
    
- Archivar música lossless
    
- Automatizar descargas repetitivas
    
- Aprender scraping avanzado
    

---

## ⚠️ Aviso

Este proyecto es solo para fines educativos.

El usuario es responsable de:

- Cómo obtiene sus listas
    
- El uso del contenido descargado
    
- Cumplir leyes y términos de servicio
    

---

## 🧑‍💻 Autor

**Jeremy José de la Cruz Pérez**  
IT Specialist | Cybersecurity | Automation

---

## ⭐ Si te gustó

- Dale star ⭐
    
- Haz fork 🍴
    
- Mejora el proyecto 🚀
    

---
