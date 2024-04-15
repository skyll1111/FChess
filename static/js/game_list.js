function formatPgnToTable(pgn) {
    const moves = pgn.split(/\d+\./).slice(1); // Split into moves (ignore first empty element)
    let tableHtml = '<table>';
    for (let i = 0; i < moves.length; i += 2) {
        tableHtml += '<tr>';
        tableHtml += `<td>${moves[i].trim()}</td>`; // White move
        if (moves[i + 1]) {
            tableHtml += `<td>${moves[i + 1].trim()}</td>`; // Black move
        } else {
            tableHtml += '<td></td>'; // Empty for last move if odd number
        }
        tableHtml += '</tr>';
    }
    tableHtml += '</table>';
    return tableHtml;
}