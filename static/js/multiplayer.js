var socket = io();
var board = null;
var game = new Chess();
var game_id = document.getElementById('game_id').value;  // Assume this value is injected into the HTML from the Flask template

socket.on('connect', function () {
    socket.emit('join', {game_id: game_id});
});

socket.on('joined_room', function (data) {
    game.reset();
    game.load(data.fen);
    // board.position(game.fen());
});

socket.on('move', function (data) {
    game.move(data.move); // Make the move on the local chess.js board
    board.position(data.fen); // Update the chessboard.js visualization
});

var config = {
    draggable: true,
    position: 'start',
    onDrop: function (source, target, piece, newPos, oldPos, orientation) {
        var move = game.move({
            from: source,
            to: target,
            promotion: 'q' // Assume queen promotion for simplicity
        });

        if (move === null) return 'snapback'; // Invalid move, snap piece back

        // Construct UCI string manually if necessary:
        var uciString = move.from + move.to;
        if (move.promotion) {
            uciString += move.promotion;
        }

        console.log('Sending move:', uciString); // Log to ensure format is correct
        socket.emit('move', {move: uciString, room: game_id, _fen: game.fen()}); // Send UCI string
        console.log(game.fen())
    }

};

socket.on('game_status', function (data) {
    game.load(data.fen);
    board.position(game.fen());
});
board = Chessboard('board', config);
