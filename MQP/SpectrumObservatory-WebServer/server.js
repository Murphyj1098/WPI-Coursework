/* ---- Global Variables ---- */
// Default packages
const fs = require('fs');
const http = require('http');
const path = require('path');
const url = require('url');
const {Worker} = require('worker_threads');

// Third party npm packages
const finalhandler = require('finalhandler');
const serveIndex = require('serve-index');
const serveStatic = require('serve-static');

const port = 80;
const mime = {
    html: 'text/html',
    txt:  'text/plain',
    css:  'text/css',
    gif:  'image/gif',
    jpg:  'image/jpeg',
    png:  'image/png',
    svg:  'image/svg+xml',
    js:   'application/javascript'
};

// Point to the static directory to serve
const index = serveIndex('public');
const serve = serveStatic('public');

// Hold radio frequency values for remote control
let freqVal1 = '900000000';
let freqVal2 = '900000000';
let freqVal3 = '900000000';
let freqVal4 = '900000000';


/* ---- HTTP Server Processing & Event Loop ---- */
const server = http.createServer(function (req, res) {

    const pathname = url.parse(req.url).pathname;
    switch (req.method) {
        case "GET":
            console.log("GET: %s", pathname);

            // Filter and format path name and serve any static file matching
            let dir = path.join(__dirname, 'public');
            let req_path = req.url.toString().split('?')[0];
            let filteredPath = req_path.replace(/\/$/, '/index.html');
            let file = path.join(dir, filteredPath);

            if (file.indexOf(dir + path.sep) !== 0) {
                sendCode(res, 403, "403 forbidden");
                break;
            }

            let type = mime[path.extname(file).slice(1)] || 'text/plain';
            let s = fs.createReadStream(file);

            s.on('open', function () {
                res.setHeader('Content-Type', type);
                s.pipe(res);
            });

            // if not serving static file/directory
            s.on('error', function () {
                switch (pathname) {
                    case '/freq1':
                        console.log("Sending frequency request on /freq1");
                        res.end(freqVal1);
                        sendCode(res, 200, "OK");
                        break;

                    case '/freq2':
                        console.log("Sending frequency request on /freq2");
                        res.end(freqVal2);
                        sendCode(res, 200, "OK");
                        break;

                    case '/freq3':
                        console.log("Sending frequency request on /freq3");
                        res.end(freqVal3);
                        sendCode(res, 200, "OK");
                        break;

                    case '/freq4':
                        console.log("Sending frequency request on /freq4");
                        res.end(freqVal4);
                        sendCode(res, 200, "OK");
                        break;

                    // Called when front-end requests contents of public/data
                    case '/data1/':
                        const done = finalhandler(req, res);    // handler to write response
                        serve(req, res, function onNext(err) {  // serve the indexes of the files in directory
                            if (err) return done(err);
                            index(req, res, done);
                        })
                        break;

                    case '/data2/':
                        done = finalhandler(req, res);          // handler to write response
                        serve(req, res, function onNext(err) {  // serve the indexes of the files in directory
                            if (err) return done(err);
                            index(req, res, done);
                        })
                        break;

                    default:
                        console.log("Client made GET to %s and invoked 404", url.parse(req.url).pathname);
                        sendCode(res, 404, "404 not found");
                        break;
                }
            });
            break;

        case "POST":
            console.log("POST: %s", pathname);

            // Data upload handling (full pathname is used in filename)
            if (pathname.startsWith('/data')) {
                let reqBody = '';
                req.on('data', function (data) {
                    reqBody += data;
                    if (reqBody.length > 1e7 /*10MB*/ ) {
                        sendCode(res, 413, "Request too large");
                    }
                });
                req.on('end', function () {
                    sendCode(res, 200, "OK");
                    console.log("Received %d bytes", req.socket.bytesRead);
                    // This function returns a promise that resolves when its worker thread finishes
                    processData(pathname, reqBody).then(console.log("Worker finished"));
                });

            } else {

            let freq;
            switch (pathname) {
                case '/post1':
                    freq = '';
                    req.on('data', function (rcdata) {
                        freq += rcdata;
                    });
                    req.on('end', () => {
                        // Need to remove "CenterFreq="
                        freqVal1 = freq.toString().split("=")[1];
                        console.log("Logged a frequency of %s on /post1", freqVal1);
                        // Respond with "204 No Content" to avoid page redirecting
                        res.writeHead(204)
                        res.end()
                    });
                    break;

                case '/post2':
                    freq = '';
                    req.on('data', function (rcdata) {
                        freq += rcdata;
                    });
                    req.on('end', () => {
                        freqVal2 = freq.toString().split("=")[1];
                        console.log("Logged a frequency of %s on /post2", freqVal2);
                        res.writeHead(204)
                        res.end()
                    });
                    break;

                case '/post3':
                    freq = '';
                    req.on('data', function (rcdata) {
                        freq += rcdata;
                    });
                    req.on('end', () => {
                        freqVal3 = freq.toString().split("=")[1];
                        console.log("Logged a frequency of %s on /post3", freqVal3);
                        res.writeHead(204)
                        res.end()
                    });
                    break;

                case '/post4':
                    freq = '';
                    req.on('data', function (rcdata) {
                        freq += rcdata;
                    });
                    req.on('end', () => {
                        freqVal = freq.toString().split("=")[1];
                        console.log("Logged a frequency of %s on /post4", freqVal);
                        res.writeHead(204)
                        res.end()
                    });
                    break;

                default:
                    console.log("Client made POST to %s and invoked 404", url.parse(req.url).pathname);
                    sendCode(res, 404, "Not found");
                    break;
            }}
            break;
        
        default:
            sendCode(res, 405, "Incorrect Method");
            break;
    }
}).listen(port);
console.log("Server started on port %d\n", port);

/* ---- Helper Functions ---- */
// Spawn a worker thread that runs the file worker.js
function processData(pathname, reqBody) {
    return new Promise((resolve, reject) => {
        const worker = new Worker('./worker.js', { workerData: { pathname, reqBody } });
        worker.on('message', resolve);
        worker.on('error',   reject);
        worker.on('exit', (code) => { 
            if (code !== 0) 
                reject(new Error(`Worker stopped with exit code ${code}`)); 
        });
    });
};

function sendCode(res, code, msg) {
    fs.readFile('public/status/' + code + '.html', function (error, content) {
        if (error) throw error;
        res.writeHead(code, msg, {'Content-type': 'text/html'});
        res.end(content, 'utf-8');
    })
}
