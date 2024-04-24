import os
import secrets
import uuid

import chess
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{os.path.abspath(os.getcwd()).replace("\\", "/")[3:]}/database.db'
# app.config['SQLALCHEMY_ECHO'] = True
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
class GameRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(80), unique=True, nullable=False)
    fen = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<GameRoom %r>' % self.room_id
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
@app.route('/create_room')
def create_room():
    # Generate a unique room ID
    room_id = str(uuid.uuid4())
    # Redirect to the room page or return the room ID
    return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>')
def room(room_id):
    game_room = GameRoom.query.filter_by(room_id=room_id).first()
    fen = game_room.fen if game_room else 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    print(fen)
    return render_template('room.html', room_id=room_id, fen=fen)

@socketio.on('join')
def on_join(data):
    print(data)
    room = data
    join_room(room)
    emit('joined_room', {'room': room}, to=room)

@socketio.on('move')
def on_move(data):
    room = data['room']
    fen = data['fen']  # Make sure to send this from client
    game_room = GameRoom.query.filter_by(room_id=room).first()
    if game_room:
        game_room.fen = fen
    else:
        game_room = GameRoom(room_id=room, fen=fen)
        db.session.add(game_room)
    db.session.commit()
    emit('move', data, to=room, include_self=False)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
