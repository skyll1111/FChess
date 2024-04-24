function getStockfishData(queryType) {
    const fen = game.fen();  // Получаем текущее состояние доски в формате FEN
    const level = document.getElementById('stockfish-level').value;

    fetch('http://localhost:5000/api/stockfish', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fen: fen,
            level: level,
            query_type: queryType
        })
    }).then(response => response.json())
        .then(data => {
            console.log(data)
            if (queryType === "best_move") {
                document.getElementById('best-move-result').innerText = 'Лучший ход: ' + data.best_move;
            } else if (queryType === "eval") {
                document.getElementById('evaluation-result').innerText = 'Оценка: ' + data.eval;
            } else if (queryType === "wdl") {
                console.log(data.wdl)
                document.getElementById('wdl-result').innerText = `WDL - Победа: ${data.wdl.wdl.wins}, Ничья: ${data.wdl.wdl.draws}, Поражение: ${data.wdl.wdl.losses}`;
            }
        })
        .catch(error => console.error('Ошибка при запросе данных Stockfish:', error));
}

function getBestMove() {
    getStockfishData("best_move");
}

function getEvaluation() {
    getStockfishData("eval");
}

function getWDL() {
    getStockfishData("wdl");
}
