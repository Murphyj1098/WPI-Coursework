var zmq = require("zeromq");
var fs  = require("fs");

var sock = zmq.socket("pull");

sock.connect("tcp://127.0.0.1:7000");
console.log("Worker connected to port 7000");

sock.on("message", function(msg) {
    fs.appendFile('sample.dat', msg, function (err) {
        if (err) throw err;
    });
});