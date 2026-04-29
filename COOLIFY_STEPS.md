# 🚀 PyBaseball API en Coolify - Pasos Simples

**Tiempo total: ~5 minutos**

---

## ✅ PASO 1: Preparar código en GitHub

### 1.1 Subir carpeta a GitHub

En tu carpeta `pybaseball/`:

```bash
cd pybaseball

git init
git add .
git commit -m "Initial: PyBaseball API con Docker"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/pybaseball-api.git
git push -u origin main
```

**Resultado:** Carpeta `pybaseball` completa en `github.com/TU_USUARIO/pybaseball-api`

---

## 🔧 PASO 2: Configurar en Coolify

### 2.1 Login en Coolify

```
https://tu-coolify.com
```

**Login con tu usuario**

### 2.2 Crear nuevo Proyecto

1. Click en **"Projects"** (en el menú izquierdo)
2. Click en **"New Project"**
3. Nombre: `PyBaseball API`
4. Click **"Create"**

### 2.3 Crear Aplicación Docker

1. En el proyecto → Click **"New Application"**
2. Elegir **"Docker"** como tipo
3. Configurar:

```
Repository:     https://github.com/TU_USUARIO/pybaseball-api.git
Branch:         main
Dockerfile:     ./Dockerfile
Build Pack:     Dockerfile
```

4. Click **"Save"**

### 2.4 Configurar Puertos

En la sección **"Ports"**:
- **Container Port:** 8000
- **Public Port:** 8000

Click **"Save"**

### 2.5 Deploy (¡Listo!)

1. Click en **"Deploy"** (botón grande rojo)
2. Esperar 2-3 minutos
3. Ver logs en tiempo real en **"Logs"** tab
4. Cuando veas ✅ y la URL aparezca, ¡está listo!

---

## 🎉 PASO 3: Verificar que funciona

### 3.1 Acceder a la API

```
https://tu-coolify.com/pybaseball-api/docs
```

Deberías ver Swagger UI con todos los endpoints.

### 3.2 Test simple

```bash
curl https://tu-coolify.com/pybaseball-api/batting-stats-bref/2023
```

---

## 🔄 PASO 4: Updates automáticos (Webhook - OPCIONAL)

Si quieres que cada push a GitHub redeploy automáticamente:

### 4.1 Copiar Webhook URL

En Coolify Dashboard → tu app → **"Deployments"**
- Copiar **Webhook URL**

### 4.2 Agregar a GitHub

En GitHub repo → **Settings** → **Webhooks**
1. Click **"Add webhook"**
2. **Payload URL:** [Pegar webhook de Coolify]
3. **Content type:** `application/json`
4. **Events:** `Push events`
5. Click **"Add webhook"**

**Ahora:** Cada vez que hagas `git push` → redeploy automático en Coolify ✨

---

## 📊 Monitoreo en Coolify

### Ver logs
Dashboard → tu app → **"Logs"** (ver en vivo)

### Reiniciar
Dashboard → tu app → **"Actions"** → **"Restart"**

### Ver stats (CPU, memoria)
Dashboard → tu app → **"Stats"**

---

## ❌ Troubleshooting

| Problema | Solución |
|----------|----------|
| Build fails | Ver logs en "Logs" tab → buscar error |
| Port already in use | En Coolify: cambiar "Public Port" a 8001 |
| "Connection refused" | Esperar a que termine build + restart |
| Container crashes | Checar logs, verificar `requirements.txt` |

---

## 📝 Información importante

- **URL de API:** `https://tu-coolify.com/pybaseball-api`
- **Documentación:** `/docs` o `/redoc`
- **Health check:** `/`
- **Logs:** En dashboard, tab "Logs"

---

## 🎯 Checklist Final

- [ ] Código en GitHub
- [ ] Proyecto creado en Coolify
- [ ] Aplicación Docker configurada
- [ ] Deploy completado (status ✅)
- [ ] API responde en `/docs`
- [ ] Webhook configurado (opcional)

---

**¡Listo! Tu API está en vivo en Coolify** 🎉
