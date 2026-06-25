/**
 * Backend Proxy para Reconciliador ARCA ↔ ERP
 * 
 * Uso:
 *   - Instala dependencias: npm install express cors
 *   - Ejecuta: node backend-proxy.js
 *   - En la UI, marcá "Usar Backend/Proxy" y configura:
 *     Endpoint Proxy: https://urldefense.com/v3/__http://localhost:3000/api/chat__;!!ETL5SZvLnA!889v5E6AsJT-HRWpHRh0Rw6W0-K45A3L5y06lLyf9eHmVsxma_N7IKsQkdOf0TOMeXDNvQ1DkM6UVcUFObbWjI63oVPw9oVkDhGWQA9L$ 
 */

const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;

/**
 * Endpoint principal que recibe requests del navegador
 * y los reenvia a la API de IA con las credenciales de forma segura
 */
app.post('/api/chat', async (req, res) => {
  try {
    const { targetEndpoint, provider, apiKey, request } = req.body;

    if (!targetEndpoint || !provider || !apiKey || !request) {
      return res.status(400).json({
        error: 'Faltan parámetros: targetEndpoint, provider, apiKey, request'
      });
    }

    if (provider !== 'OpenAI') {
      return res.status(400).json({
        error: 'Este servidor proxy solo soporta el proveedor OpenAI'
      });
    }

    // Construir headers para OpenAI
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    };

    console.log(`[${new Date().toISOString()}] Forwarding to ${provider}: ${targetEndpoint}`);

    // Hacer el request a la API real
    const response = await fetch(targetEndpoint, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(request)
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(`API Error (${response.status}):`, data);
      return res.status(response.status).json(data);
    }

    // Reenviar la respuesta al navegador
    res.json(data);

  } catch (error) {
    console.error('Proxy Error:', error);
    res.status(500).json({
      error: error.message,
      details: 'Error en el servidor proxy. Ve la consola para más info.'
    });
  }
});

/**
 * Endpoint de health check
 */
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

/**
 * Endpoint para obtener información del proxy
 */
app.get('/api/info', (req, res) => {
  res.json({
    name: 'Reconciliador ARCA ↔ ERP Proxy',
    version: '1.0.0',
    providers: ['OpenAI'],
    features: [
      'CORS bypass',
      'Secure key handling',
      'Request forwarding',
      'Error handling'
    ],
    endpoint: '/api/chat'
  });
});

app.listen(PORT, () => {
  console.log(`\n🚀 Proxy server running on https://urldefense.com/v3/__http://localhost:$*7BPORT*7D__;JSU!!ETL5SZvLnA!889v5E6AsJT-HRWpHRh0Rw6W0-K45A3L5y06lLyf9eHmVsxma_N7IKsQkdOf0TOMeXDNvQ1DkM6UVcUFObbWjI63oVPw9oVkDtNi0Y9S$ `);
  console.log(`📊 Health check: https://urldefense.com/v3/__http://localhost:$*7BPORT*7D/health__;JSU!!ETL5SZvLnA!889v5E6AsJT-HRWpHRh0Rw6W0-K45A3L5y06lLyf9eHmVsxma_N7IKsQkdOf0TOMeXDNvQ1DkM6UVcUFObbWjI63oVPw9oVkDnSJ77cl$ `);
  console.log(`ℹ️  Info: https://urldefense.com/v3/__http://localhost:$*7BPORT*7D/api/info__;JSU!!ETL5SZvLnA!889v5E6AsJT-HRWpHRh0Rw6W0-K45A3L5y06lLyf9eHmVsxma_N7IKsQkdOf0TOMeXDNvQ1DkM6UVcUFObbWjI63oVPw9oVkDjPTb5jD$ `);
  console.log(`\nEn la UI del Reconciliador:\n  - Marca "Usar Backend/Proxy"\n  - Endpoint Proxy: https://urldefense.com/v3/__http://localhost:$*7BPORT*7D/api/chat/n__;JSU!!ETL5SZvLnA!889v5E6AsJT-HRWpHRh0Rw6W0-K45A3L5y06lLyf9eHmVsxma_N7IKsQkdOf0TOMeXDNvQ1DkM6UVcUFObbWjI63oVPw9oVkDj2bivGM$ `);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Cerrando proxy...');
  process.exit(0);
});
