import io
import os

import chess
import chess.engine
import chess.pgn
import chess.svg

STOCKFISH_PATH = f"{os.path.abspath(os.getcwd()).replace("\\", "/")}/stockfish_ex/stockfish-windows-x86-64-avx2.exe"


def analyze_game(pgn, depth):
    pgn_io = io.StringIO(pgn)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    annotations = []

    for move in game.mainline_moves():

        move_details = {
            'move': board.san(move),
            'fen': board.fen(),
            'comment': ''
        }
        board.push(move)
        move_details['fen'] = board.fen()
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info.get('score', None)
        if score is not None:
            cp = score.white().score(mate_score=10000) if score else None
            move_details['score'] = cp / 100.0 if cp else 'Mating Sequence'
            if cp and abs(cp) > 100:
                move_details['comment'] = 'Blunder' if cp < -300 else 'Mistake' if cp < -150 else 'Inaccuracy'
        annotations.append(move_details)

    engine.quit()
    return annotations


def get_stockfish_analysis(fen, level, query_type):
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    engine.configure({"Skill Level": level})
    engine.configure({"UCI_ShowWDL": "true"})

    board = chess.Board(fen)
    info = engine.analyse(board, chess.engine.Limit(depth=20))
    result = None
    if query_type == "best_move":
        result = str(info["pv"][0])
    elif query_type == "eval":
        result = str(info["score"])
    elif query_type == "wdl":
        if "wdl" in info:
            result = {"wdl": info["wdl"].relative, "turn": "WHITE" if info["wdl"].turn else "BLACK"}
        else:
            result = "WDL not available"

    engine.quit()
    return result


def generate_board_svg(fen):
    board = chess.Board(fen)
    return chess.svg.board(board=board)
