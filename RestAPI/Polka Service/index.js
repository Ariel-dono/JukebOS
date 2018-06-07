const polka = require('polka');
var zmq = require('zmq');

const app = polka();

// socket to talk to server
console.log("Connecting to zmq server…");

function getConnection(port){
  var mqueue = zmq.socket('req');
  mqueue.connect(`tcp://localhost:${port}`);
  return mqueue;
}

let user = "";

let playerConnections = new Map();

let player;

getter = getConnection(5500);
getter.on("message", function(reply) {
  sessioned_user = user
  raw_response = String.fromCharCode(...reply).replace(/ /g,"").replace('\0', '').replace(/\0/g, '');
  responseJson = JSON.parse(raw_response);
  playerConnections.set(sessioned_user, {"zmq_conn":getConnection(responseJson.zmq_port), "gst_conn":responseJson.gst_port});
});

function response(mqueuemessage, res, message){
  mqueuemessage.send(message);
  res.end(message);
}

app.post('/dispatcher/:username', (req, res) => {
  user = req.params.username;
  response(getter, res, "./Stalemate.mp3");
});

app.post('/connection/:username', (req, res) => {
  user = req.params.username;
  res.end(`{"port":${playerConnections.get(user).gst_conn}}`);
});

app.post('/play/:username', (req, res) => {
  user = req.params.username;
  response(playerConnections.get(user).zmq_conn, res, `0`);
});

app.post('/pause/:username', (req, res) => {
  user = req.params.username;
  response(playerConnections.get(user).zmq_conn, res, `1`);
});

app.post('/stop/:username', (req, res) => {
  user = req.params.username;
  response(playerConnections.get(user).zmq_conn, res, `2`);
});

app.listen(4200).then(_ => {
    console.log(`> Running on localhost:4200`);
})
