const path = require('path');
const express = require(path.join(process.argv[2], 'express'));
const { ExpressPeerServer } = require(path.join(process.argv[2], 'peer'));
const app = express(); const http = require('http').createServer(app);
app.use('/jt', ExpressPeerServer(http, { path: '/' }));
http.listen(9000, '127.0.0.1', () => console.log('peer server on 127.0.0.1:9000/jt'));
