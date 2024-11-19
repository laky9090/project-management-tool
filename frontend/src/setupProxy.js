const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://0.0.0.0:3001',
      changeOrigin: true,
      secure: false,
      timeout: 30000, // Increase proxy timeout to 30 seconds
      onProxyReq: function(proxyReq, req, res) {
        // Log proxy requests
        console.log('Proxying:', req.method, req.url, 'to', proxyReq.path);
      },
      onError: function(err, req, res) {
        console.error('Proxy error:', err);
        res.writeHead(504, {
          'Content-Type': 'text/plain',
        });
        res.end('The request timed out');
      }
    })
  );
};
