const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:3001',
      changeOrigin: true,
      secure: false,
      timeout: 600000, // 10 minutes timeout
      proxyTimeout: 600000,
      onProxyReq: function(proxyReq, req, res) {
        console.log('Proxying:', req.method, req.url, 'to', proxyReq.path);
      },
      onError: function(err, req, res) {
        console.error('Proxy error:', err);
        if (!res.headersSent) {
          res.writeHead(504, {
            'Content-Type': 'application/json',
          });
        }
        res.end(JSON.stringify({
          error: 'The request timed out',
          details: err.message
        }));
      },
      headers: {
        Connection: 'keep-alive'
      },
      pathRewrite: {
        '^/api': '/api'
      }
    })
  );
};
