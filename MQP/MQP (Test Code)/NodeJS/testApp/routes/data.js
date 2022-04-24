var express = require('express');
var fs = require('fs');
var router = express.Router();

/* Handle GET */
router.get('/', function(req, res, next) {
  res.send('data');
});

/* Handle POST */
router.post('/', function(req, res, next) {  
  console.log(req.body.metadata);
  // writeFile(JSON.stringify(req.body));
  res.status(200).send();
});

module.exports = router;


function writeFile(data) {
  fs.writeFile('fullSample.json', data, function (err) {
    if (err) throw err;
  });
}