var board = null;
var game = new Chess();

// Function to update FEN and PGN displays
function updateFenPgn() {
    document.getElementById('fen').innerHTML = '<b>FEN:</b> ' + game.fen();
    document.getElementById('pgn').innerHTML = '<b>PGN:</b> ' + game.pgn();
}

// Function to handle piece drag start
function onDragStart(source, piece, position, orientation) {
    // Only allow moves for the side to move
    if (game.game_over() === true ||
        (game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
    }
}

// Function to handle piece drop
function onDrop(source, target) {
    // See if the move is legal
    var move = game.move({
        from: source,
        to: target,
        promotion: 'q' // NOTE: always promote to a queen for example simplicity
    });

    // Illegal move
    if (move === null) return 'snapback';
    fetch('/save_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'  // Add this header
        },
        body: JSON.stringify({
            pgn: game.pgn()
        })
    });

    updateStatus();
    updateFenPgn(); // Update FEN and PGN displays
}

// Update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd() {
    board.position(game.fen());
}

function loadPgn(pgn) {
    game.load_pgn(pgn);
    board.position(game.fen());
    updateFenPgn();
    updateStatus();
}

// Function to update game status
function updateStatus() {
    var status = '';

    var moveColor = 'White';
    if (game.turn() === 'b') {
        moveColor = 'Black';
    }

    // Checkmate?
    if (game.in_checkmate() === true) {
        status = 'Game over, ' + moveColor + ' is in checkmate.';
    }

    // Draw?
    else if (game.in_draw() === true) {
        status = 'Game over, drawn position';
    }

    // Game still on
    else {
        status = moveColor + ' to move';

        // Check?
        if (game.in_check() === true) {
            status += ', ' + moveColor + ' is in check';
        }
    }

    // Display the status
    document.getElementById('status').innerHTML = status;
}

// Configure and initialize chessboard
var config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd
};
board = Chessboard('board', config);
window.onload = function () {
    var pgnElement = document.getElementById('pgn_data');
    if (pgnElement) {
        var pgnData = pgnElement.textContent;
        console.log("PGN Data:", pgnData); // Check if PGN is present
        loadPgn(pgnData);
    } else {
        console.error("pgn_data element not found!");
    }
};
// Initialize FEN and PGN displays
updateFenPgn();
updateStatus();
