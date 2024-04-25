import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))


class chess_games(db.Model):
    __tablename__ = 'chess_games'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pgn = db.Column(db.String)


class GameRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(80), unique=True, nullable=False)
    fen = db.Column(db.String(255), nullable=False)
    player_one_id = db.Column(db.String(80), nullable=True)
    player_two_id = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return '<GameRoom %r>' % self.room_id


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC))

    def __repr__(self):
        return f"<ChatMessage {self.room_id} {self.user_id} {self.message}>"
