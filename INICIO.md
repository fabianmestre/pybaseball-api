# 🚀 INICIO RÁPIDO - PyBaseball API en Coolify

**Lee esto primero. Son 3 pasos simples.**

---

## 📁 Tu carpeta está lista

```
pybaseball/  ← Todo está aquí
├── pybaseball_api.py       API completa
├── requirements.txt        Dependencias
├── Dockerfile             Para Docker
├── docker-compose.yml     Para desarrollo
├── COOLIFY_RAPIDO.md      👈 GUÍA PRINCIPAL
├── COOLIFY_STEPS.md       Versión detallada
├── README.md              Descripción general
├── ESTRUCTURA.md          Explicación de archivos
└── .gitignore, .dockerignore, etc
```

---

## ⚡ 3 PASOS PARA COOLIFY

### PASO 1: Subir a GitHub (2 minutos)

Abre terminal en la carpeta `pybaseball/`:

```bash
cd "g:/My Drive/APTIVA-LABS/Automatizacion/pybaseball"

git init
git add .
git commit -m "PyBaseball API"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/pybaseball-api.git
git push -u origin main
```

**⚠️ Reemplaza `TU_USUARIO` con tu usuario GitHub**

---

### PASO 2: Crear en Coolify (2 minutos)

1. Login en `https://tu-coolify.com`

2. **Projects** → **New Project**
   - Nombre: `PyBaseball API`
   - Click **Create**

3. En el proyecto → **New Application**
   - Tipo: **Docker**
   - Repository: `https://github.com/TU_USUARIO/pybaseball-api.git`
   - Branch: `main`
   - Dockerfile: `./Dockerfile`
   - Click **Save**

4. **Ports section** (importante):
   - Container Port: `8000`
   - Public Port: `8000`
   - Click **Save**

---

### PASO 3: Deploy (1 minuto)

Click botón rojo **"Deploy"** → Esperar 2-3 minutos

---

## ✅ Verificar que funciona

Cuando veas ✅ en Coolify, ve a:

```
https://tu-coolify.com/pybaseball-api/docs
```

Deberías ver una página azul/roja con todos los endpoints 📚

---

## 🎉 ¡LISTO!

Tu API está en vivo. Ejemplos:

```bash
# Swagger interactivo
https://tu-coolify.com/pybaseball-api/docs

# Endpoint de ejemplo
https://tu-coolify.com/pybaseball-api/batting-stats-bref/2023

# Con curl
curl https://tu-coolify.com/pybaseball-api/batting-stats-bref/2023
```

---

## 📖 Documentación

| Necesidad | Archivo |
|-----------|---------|
| Más detalles | `COOLIFY_STEPS.md` |
| Entender estructura | `ESTRUCTURA.md` |
| Info general | `README.md` |

---

## 🆘 Si algo falla

**Error en deploy?**
1. Ver **"Logs"** en Coolify
2. Leer error
3. Buscar en `COOLIFY_STEPS.md` → Troubleshooting

**Necesitas cambiar algo?**
1. Editar archivo (ej: `pybaseball_api.py`)
2. Hacer commit y push
3. Automáticamente redeploy en Coolify

---

## 💡 BONUS: Auto-deploy en cada push

Quieres que se actualice solo sin hacer nada?

1. En Coolify → tu app → **"Deployments"**
2. Copiar **Webhook URL**
3. GitHub repo → **Settings** → **Webhooks** → **Add webhook**
4. Pegar URL, elegir **"Push events"**, **Add**

Listo. Cada `git push` = redeploy automático

---

## 📝 Checklist

- [ ] Código subido a GitHub
- [ ] Proyecto creado en Coolify
- [ ] Aplicación Docker configurada
- [ ] Deploy completado (status ✅)
- [ ] API responde en `/docs`
- [ ] Webhook configurado (opcional)

---

**Todo listo. ¡A por ello!** 🎯

Cualquier duda → ver `COOLIFY_STEPS.md`
