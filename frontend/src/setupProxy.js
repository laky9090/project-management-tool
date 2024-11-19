const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://0.0.0.0:3001',
      changeOrigin: true,
      secure: false,
      timeout: 600000, // Increase proxy timeout to 10 minutes
      proxyTimeout: 600000, // Add proxy timeout
      onProxyReq: function(proxyReq, req, res) {
        // Log proxy requests
        console.log('Proxying:', req.method, req.url, 'to', proxyReq.path);
      },
      onError: function(err, req, res) {
        console.error('Proxy error:', err);
        res.writeHead(504, {
          'Content-Type': 'application/json',
        });
        res.end(JSON.stringify({
          error: 'The request timed out',
          details: err.message
        }));
      }
    })
  );
};
