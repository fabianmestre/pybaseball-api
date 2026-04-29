# ⚡ COOLIFY EN 5 PASOS

**Guía ultra rápida sin tecnicismos**

---

## 1️⃣ Subir código a GitHub

```bash
cd pybaseball

git init
git add .
git commit -m "PyBaseball API"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/pybaseball-api.git
git push -u origin main
```

**Reemplaza `TU_USUARIO` con tu usuario de GitHub**

---

## 2️⃣ Entrar a Coolify

```
https://tu-coolify.com
```

Login con tu usuario

---

## 3️⃣ Crear proyecto

1. Menú izquierdo → **"Projects"**
2. Botón **"New Project"**
3. Nombre: `PyBaseball API`
4. Click **"Create"**

---

## 4️⃣ Crear aplicación

En el proyecto recién creado:

1. Botón **"New Application"**
2. Elegir **"Docker"**
3. Llenar:
   - **Repository:** `https://github.com/TU_USUARIO/pybaseball-api.git`
   - **Branch:** `main`
   - **Dockerfile:** `./Dockerfile`
4. Click **"Save"**
5. En **"Ports"** → Container Port: `8000`, Public Port: `8000`
6. Click **"Save"** de nuevo

---

## 5️⃣ Deploy

1. Click en el botón rojo grande **"Deploy"**
2. Esperar 2-3 minutos (ver logs)
3. Cuando veas ✅, ¡está listo!

---

## ✅ Verificar

Ir a:
```
https://tu-coolify.com/pybaseball-api/docs
```

Deberías ver una página azul con endpoints

---

## 🎉 ¡LISTO!

Tu API está en vivo. Ejemplos:

```bash
# Ver documentación
https://tu-coolify.com/pybaseball-api/docs

# Llamar un endpoint
https://tu-coolify.com/pybaseball-api/batting-stats-bref/2023
```

---

## 💡 BONUS: Updates automáticos

Si quieres que se actualice solo cada vez que hagas `git push`:

1. En Coolify → tu app → **"Deployments"**
2. Copiar **Webhook URL**
3. En GitHub repo → **Settings** → **Webhooks** → **Add webhook**
4. Pegar URL, elegir **"Push events"**, click **"Add"**

**Ahora:** cada push = redeploy automático en Coolify

---

**Listo. API en producción en 5 minutos.** 🚀
