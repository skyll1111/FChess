import uuid

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room

from config import AppConfig
from models import db, User, chess_games, GameRoom, ChatMessage
from utils import analyze_game, get_stockfish_analysis, generate_board_svg

app = Flask(__name__)
app.config.from_object(AppConfig)
socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)
CORS(app)


@app.route("/game")
def game():
    session.pop('game_id', None)

    if 'logged_in' in session:
        new_game = chess_games(user_id=session.get('user_id'), pgn="")
        db.session.add(new_game)
        db.session.commit()
        session['game_id'] = new_game.id
        return render_template("game.html")
    else:
        return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        remember_me = request.form.get("remember_me")

        login = User.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            session['logged_in'] = True
            session['username'] = uname
            session['user_id'] = login.id
            return redirect(url_for("profile"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = User(username=uname, email=mail, password=passw)
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

        session['game_id'] = game_id

        return render_template('game.html', pgn=game.pgn)
    else:
        return redirect(url_for('login'))


@app.route('/create_room', methods=['GET'])
def create_room():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    room_id = str(uuid.uuid4())
    new_room = GameRoom(room_id=room_id, fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                        player_one_id=user_id)

    db.session.add(new_room)
    db.session.commit()
    return redirect(url_for('room', room_id=room_id))


@app.route('/room/<room_id>')
def room(room_id):
    user_id = session.get('user_id')
    game_room = GameRoom.query.filter_by(room_id=room_id).first()

    if not game_room:
        return redirect(url_for('index'))

    if (game_room.player_one_id and game_room.player_two_id and
            str(user_id) not in [game_room.player_one_id, game_room.player_two_id]):
        return redirect(url_for('index'))

    if str(user_id) in [game_room.player_one_id, game_room.player_two_id]:
        print("user allowed")
    elif not game_room.player_one_id:
        game_room.player_one_id = user_id
    elif not game_room.player_two_id and user_id != game_room.player_one_id:
        game_room.player_two_id = user_id

    db.session.commit()
    player_color = "white" if str(user_id) in game_room.player_one_id else "black"
    fen = game_room.fen if game_room else 'start'
    waiting_for_player = False
    if not game_room.player_two_id and game_room.player_one_id != user_id:
        waiting_for_player = True
    return render_template('room.html', room_id=room_id, fen=fen, user_id=user_id,
                           user_color=player_color, waiting_for_player=waiting_for_player)


@socketio.on('join')
def on_join(data):
    room = data['room']
    user_id = data['user_id']
    join_room(room)
    emit('joined_room', {'room_id': room}, room=room)
    game_room = GameRoom.query.filter_by(room_id=room).first()

    if game_room.player_one_id and game_room.player_two_id:
        emit('player_joined', {'start_game': True}, room=room)
    else:
        if not game_room.player_two_id and game_room.player_one_id != user_id:
            game_room.player_two_id = user_id
            db.session.commit()
            emit('player_joined', {'start_game': True}, room=room)
        else:
            emit('waiting_for_player', {'waiting': True}, room=room)


@socketio.on('move')
def on_move(data):
    room = data['room']
    fen = data['fen']
    game_room = GameRoom.query.filter_by(room_id=room).first()
    if game_room:
        game_room.fen = fen
    else:
        game_room = GameRoom(room_id=room, fen=fen)
        db.session.add(game_room)
    db.session.commit()
    emit('move', data, to=room, include_self=False)


@app.route('/api/stockfish', methods=['POST'])
def stockfish_api():
    data = request.get_json()
    fen = data.get("fen")
    level = data.get("level")
    query_type = data.get("query_type")

    if not fen or not level or not query_type:
        return jsonify({"error": "Missing required parameters"}), 400

    result = get_stockfish_analysis(fen, level, query_type)
    return jsonify({query_type: result})


@app.route('/join_room_by_id', methods=['POST'])
def join_room_by_id():
    room_id = request.form.get('room_id')
    if not room_id:
        flash('No room ID provided!', 'error')
        return redirect(url_for('index'))

    return redirect(url_for('room', room_id=room_id))


@app.route('/online_games')
def online_games():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    games = GameRoom.query.filter((GameRoom.player_one_id == user_id) | (GameRoom.player_two_id == user_id)).all()
    return render_template('online_games.html', games=games)


@app.route('/get_messages/<room_id>')
def get_messages(room_id):
    messages = ChatMessage.query.filter_by(room_id=room_id).all()
    return jsonify(
        [{'user_id': msg.user_id, 'message': msg.message, 'timestamp': msg.timestamp.isoformat()} for msg in messages])


@app.route('/post_message', methods=['POST'])
def post_message():
    data = request.get_json()
    new_message = ChatMessage(room_id=data['room_id'], user_id=data['user_id'], message=data['message'])
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('new_message', {
        'user_id': data['user_id'],
        'message': data['message'],
        'room_id': data['room_id']
    }, room=data['room_id'])

    return jsonify({'status': 'success'})


@app.route('/api/board_svg', methods=['POST'])
def board_svg():
    data = request.get_json()
    fen = data.get("fen")
    if not fen:
        return jsonify({"error": "Missing FEN parameter"}), 400

    svg = generate_board_svg(fen)
    return Response(svg, mimetype='image/svg+xml')


@app.route('/api/review_game', methods=['POST'])
def review_game():
    data = request.get_json()
    pgn = data.get('pgn')
    depth = int(data.get('depth', 20))

    if not pgn:
        return jsonify({'error': 'No PGN provided'}), 400

    analysis = analyze_game(pgn, depth)
    return jsonify(analysis)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
