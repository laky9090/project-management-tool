const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://0.0.0.0:3001',
      changeOrigin: true,
      secure: false,
      onProxyReq: function(proxyReq, req, res) {
        // Log proxy requests
        console.log('Proxying:', req.method, req.url, 'to', proxyReq.path);
      }
    })
  );
};
