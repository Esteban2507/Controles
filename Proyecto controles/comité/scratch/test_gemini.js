const fetch = require('node-fetch'); // wait, node 18+ has fetch built-in, but let's write vanilla JS that runs in node

async function test() {
  const model = 'gemini-1.5-pro-latest';
  const apiKey = 'AIzaSyDUMMYKEYDUMMYKEYDUMMYKEYDUMMYKEY';
  const geminiEndpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
  
  try {
    const response = await fetch(geminiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: "You are a test helper." }] },
        contents: [{ role: 'user', parts: [{ text: "Hello" }] }],
        generationConfig: { maxOutputTokens: 800 }
      })
    });
    
    console.log('Status with systemInstruction:', response.status);
    const data = await response.json();
    console.log('Response with systemInstruction:', JSON.stringify(data, null, 2));
  } catch (err) {
    console.error('Error:', err);
  }
}

test();
