# Reconciliador ARCA ↔ ERP - Backend Proxy

Este directorio contiene el reconciliador ARCA ↔ ERP y un servidor proxy backend opcional para mejorar la seguridad.

## Archivos

- **arca-reconciliador.html** - Aplicación web principale
- **backend-proxy.js** - Servidor proxy Node.js (opcional)
- **package.json** - Dependencias del proxy

## Uso Rápido

### 1. Modo directo (sin proxy)
Simplemente abre `arca-reconciliador.html` en tu navegador:
- No requiere instalación
- Llamadas directas a las APIs (Anthropic, OpenAI, etc.)
- La clave se guarda en sessionStorage del navegador

### 2. Modo Backend/Proxy (recomendado para producción)

**Instalación:**

```bash
# Instala Node.js si no lo tienes: https://nodejs.org

# En esta carpeta, instala las dependencias:
npm install
```

**Inicia el proxy:**

```bash
npm start
```

Verás algo como:
```
🚀 Proxy server running on http://localhost:3000
📊 Health check: http://localhost:3000/health
ℹ️  Info: http://localhost:3000/api/info
```

**Configura en la UI:**

1. Abre `arca-reconciliador.html` en tu navegador
2. En la pantalla de configuración, marca: **"Usar Backend/Proxy (evitar CORS)"**
3. Ingresa el **Endpoint Proxy**: `http://localhost:3000/api/chat`
4. Ingresa el resto de la config (proveedor, modelo, API key)
5. Conecta

## Ventajas del Proxy

✅ **Seguridad:** Tu API key se envía solo al servidor backend, nunca exponerse en el navegador  
✅ **CORS:** Evita problemas de origen cruzado  
✅ **Control:** Puedes agregar logs, autenticación, límites de rate, etc.  
✅ **Privacidad:** Los datos no se almacenan en el navegador del cliente  

## Ejemplificación de Cabeceras Personalizadas

Si necesitas enviar headers extra con cada request (ej: autenticación custom, tracking):

1. En la UI, desmarca "Usar Backend/Proxy" (modo directo)
2. Aparecerá un campo **"Cabeceras Personalizadas (JSON)"**
3. Ingresa JSON válido:
```json
{
  "X-API-Version": "2024-01",
  "X-Client-ID": "reconciliador-arca",
  "X-Request-ID": "tracking-id"
}
```

## Almacenamiento Seguro de Claves

El reconciliador:
- Guarda la API key en **sessionStorage** (se borra al cerrar el navegador)
- Muestra un indicador visual
- NO registra las claves en console o logs del navegador

Si usas el proxy backend, puedes guardar las claves en:
- Variables de entorno del servidor
- Vault (HashiCorp Vault)
- AWS Secrets Manager
- Base de datos encriptada

## Troubleshooting

### Error "CORS"
- Si ves error CORS sin usar proxy: cambia a modo proxy
- Si el proxy falla: verifica que esté corriendo en `http://localhost:3000`

### Error "API key inválida"
- Anthropic: debe comenzar con `sk-ant-`
- OpenAI: debe comenzar con `sk-`
- En proxy mode: la validación ocurre en el servidor

### El proxy no responde
```bash
# Verifica health:
curl http://localhost:3000/health

# Verifica info:
curl http://localhost:3000/api/info
```

## Configuración Avanzada

Puedes editar `backend-proxy.js`:

```javascript
// Cambiar puerto
const PORT = process.env.PORT || 3000;

// Agregar autenticación
app.use((req, res, next) => {
  const token = req.headers['x-proxy-token'];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  next();
});

// Agregar logging
console.log(`Request: ${req.method} ${req.path}`);
```

## Preguntas Frecuentes

**¿Necesito usar el proxy?**  
No, pero es recomendado si usas esto en producción o compartes la herramienta con otros usuarios.

**¿Mi API key es segura en sessionStorage?**  
Más segura que en localStorage, pero no perfecta. El proxy es más seguro.

**¿Puedo usar cabeceras custom en proxy mode?**  
Sí, en el proxy puedes servir headers adicionales antes de reenviar.

**¿Qué hace exactamente el proxy?**  
1. Recibe el request del navegador
2. Extrae los parámetros (proveedor, modelo, etc.)
3. Construye el request correcto para la API real
4. Envía la solicitud con la API key de forma segura
5. Reenvia la respuesta al navegador

---

**¿Dudas o problemas?** Revisa la consola del navegador (F12 → Console) y los logs del proxy.
