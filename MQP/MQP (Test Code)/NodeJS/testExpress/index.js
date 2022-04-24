var express    = require('express')
var serveIndex = require('serve-index')
 
var app = express()
 
const dir = `${__dirname}/public/`;

app.use('/data', express.static(dir + 'data'), serveIndex(dir + 'data'))

app.get('/', function(req, res) {
    res.sendFile(dir + 'index.html');
  });
  app.listen(3000);