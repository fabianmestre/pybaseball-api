# PyBaseball API REST

API profesional para acceder a datos de béisbol MLB usando [pybaseball](https://github.com/jldbc/pybaseball)

---

## 📦 Contenido

```
pybaseball/
├── pybaseball_api.py      # Código de la API (FastAPI)
├── requirements.txt        # Dependencias Python
├── Dockerfile             # Imagen Docker
├── docker-compose.yml     # Compose para desarrollo
├── .dockerignore          # Archivos excluidos
├── COOLIFY_STEPS.md       # 👈 LEER ESTO PRIMERO (pasos para Coolify)
└── README.md              # Este archivo
```

---

## 🚀 Empezar rápido

### Opción A: En Coolify (RECOMENDADO)

👉 **Ver archivo: `COOLIFY_STEPS.md`** (5 minutos)

### Opción B: Localmente con Docker

```bash
# Windows
docker-compose up -d

# Ver logs
docker-compose logs -f

# Acceder a: http://localhost:8000/docs
```

### Opción C: Python directo (sin Docker)

```bash
pip install -r requirements.txt
python pybaseball_api.py

# Acceder a: http://localhost:8000/docs
```

---

## 📚 Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/docs` | Swagger UI (todos los endpoints) |
| GET | `/batting-stats-bref/{season}` | Stats de bateo para año |
| GET | `/pitching-stats-bref/{season}` | Stats de pitcheo para año |
| POST | `/statcast` | Datos pitch-by-pitch |
| POST | `/player-lookup` | Buscar jugador por nombre |
| GET | `/standings/{season}` | Clasificaciones |

**Ver `/docs` en vivo para lista completa**

---

## 🔗 URLs (después de publicar)

- **Swagger UI:** `https://tu-coolify.com/pybaseball-api/docs`
- **ReDoc:** `https://tu-coolify.com/pybaseball-api/redoc`
- **Root:** `https://tu-coolify.com/pybaseball-api/`

---

## 📖 Documentación

- **Guía Coolify:** Ver `COOLIFY_STEPS.md`
- **API completa:** Ir a `/docs` después de ejecutar
- **pybaseball:** https://github.com/jldbc/pybaseball

---

## ✨ Características

✅ API REST completa con FastAPI  
✅ Swagger UI automático en `/docs`  
✅ 25+ endpoints documentados  
✅ Dockerizada y lista para Coolify  
✅ Validación de parámetros  
✅ CORS habilitado  
✅ Error handling profesional  

---

## 🛠️ Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Librería datos:** pybaseball
- **Contenedor:** Docker
- **Plataforma:** Coolify

---

**Crear por Claudio - Agente n8n**  
**Última actualización: 2026-04-29**
