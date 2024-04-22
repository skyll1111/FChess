import os
import secrets

import chess
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{os.path.abspath(os.getcwd()).replace("\\", "/")[3:]}/database.db'
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = secrets.token_urlsafe(32)
db = SQLAlchemy(app)


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))


class chess_games(db.Model):
    __tablename__ = 'chess_games'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pgn = db.Column(db.String)  # Store the PGN data of the game


from datetime import datetime


class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    white_player_id = db.Column(db.Integer, nullable=True)
    black_player_id = db.Column(db.Integer, nullable=True)
    fen = db.Column(db.String, default="startpos")  # Starting position in FEN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/game")
def game():
    # Clear game_id from session to ensure a new game is created
    session.pop('game_id', None)

    if 'logged_in' in session:
        new_game = chess_games(user_id=session.get('user_id'), pgn="")
        db.session.add(new_game)
        db.session.commit()
        session['game_id'] = new_game.id
        return render_template("game.html")
    else:
        return redirect(url_for("login"))  # Redirect to login if not logged in


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        remember_me = request.form.get("remember_me")  # Get checkbox value

        login = user.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            session['logged_in'] = True
            session['username'] = uname
            session['user_id'] = login.id
            # Handle "Remember Me" (not implemented for security reasons)
            # ...
            return redirect(url_for("profile"))  # Redirect to profile
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = user(username=uname, email=mail, password=passw)
        db.session.add(register)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/profile")
def profile():
    if 'logged_in' in session:
        username = session['username']
        return render_template("profile.html", username=username)
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for("index"))


@app.route('/save_game', methods=['POST'])
def save_game():
    if 'logged_in' in session:
        user_id = session.get('user_id')
        game_id = session.get('game_id')
        pgn_data = request.json['pgn']

        game = chess_games.query.get(game_id)
        game.pgn = pgn_data
        db.session.commit()
        return jsonify({'message': 'Game saved'})
    else:
        return jsonify({'error': 'Not logged in'}), 401


@app.route('/game_list')
def game_list():
    if 'logged_in' in session:
        user_id = session.get('user_id')
        games = chess_games.query.filter_by(user_id=user_id).all()
        return render_template('game_list.html', games=games)
    else:
        return redirect(url_for('login'))


@app.route('/load_game/<int:game_id>')
def load_game(game_id):
    if 'logged_in' in session:
        user_id = session.get('user_id')
        game = chess_games.query.filter_by(id=game_id, user_id=user_id).first_or_404()

        # Update session's game_id to reflect the loaded game
        session['game_id'] = game_id

        print(game.pgn)
        return render_template('game.html', pgn=game.pgn)
    else:
        return redirect(url_for('login'))


games = {}


@app.route('/multiplayer/<int:game_id>')
def multiplayer(game_id):
    game = GameSession.query.get(game_id)
    if not game or (game.white_player_id and game.black_player_id and session['user_id'] not in [game.white_player_id,
                                                                                                 game.black_player_id]):
        return redirect(url_for('index'))  # Redirect to main if no game or room is full
    return render_template('multiplayer.html', game_id=game_id)


@socketio.on('join')
def on_join(data):
    game_id = data['game_id']
    game = GameSession.query.get(game_id)

    if not game:
        return  # Handle error, game does not exist
    join_room(str(game_id))
    emit('game_status', {'fen': game.fen}, room=str(game_id))


@socketio.on('move')
def on_move(data):
    print("!!!!!!!!!!!!", data)
    game_id = data['room']
    uci_move = data['move']
    print("||||||||||", data["_fen"])

    game = GameSession.query.get(game_id)
    print("!!!!!!!!!!!!!", game)
    game.fen = data["_fen"]

    if game:
        board = chess.Board(game.fen)  # Initialize the board with the current FEN
        print(board.fen())

        try:
            move = chess.Move.from_uci(uci_move)  # Convert UCI move to a chess.Move
            print(move)
            # if move in board.legal_moves:  # Check if the move is legal
            # board.push(move)  # Make the move on the board
            game.fen = board.fen()  # Update the game's FEN with the new board state
            db.session.commit()  # Save the updated game state to the database
            print("&&&&")

            emit('move', {'move': uci_move, 'fen': game.fen}, room=str(game_id))
            # else:
            #     emit('move_error', {'error': 'Illegal move'}, room=str(game_id))
        except ValueError:
            emit('move_error', {'error': 'Invalid move format'}, room=str(game_id))
    else:
        emit('move_error', {'error': 'Game not found'}, room=str(game_id))


@socketio.on('leave')
def on_leave():
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    emit('status', {'msg': username + ' has left the room.'}, room=room)


@app.route('/create_game', methods=['POST'])
def create_game():
    user_id = request.json.get('user_id')
    color = request.json.get('color', 'white')  # Default to white if not specified

    new_game = GameSession(
        white_player_id=user_id if color == 'white' else None,
        black_player_id=user_id if color == 'black' else None
    )
    db.session.add(new_game)
    db.session.commit()

    return jsonify({
        'game_id': new_game.id,
        'message': f'New game created with ID {new_game.id}, player as {color}'
    }), 201


@app.route('/join_game', methods=['POST'])
def join_game():
    user_id = request.json.get('user_id')
    game_id = request.json.get('game_id')

    game = GameSession.query.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # Assign player to game if there's a spot
    if game.white_player_id is None:
        game.white_player_id = user_id
    elif game.black_player_id is None:
        game.black_player_id = user_id
    else:
        return jsonify({'error': 'Game is full'}), 400

    db.session.commit()
    return jsonify({
        'game_id': game_id,
        'message': 'Joined game successfully'
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
    pass
