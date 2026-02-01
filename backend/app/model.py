from app import db

def get_bcrypt():
    """Get bcrypt instance from app"""
    from app import flask_bcrypt
    return flask_bcrypt
from datetime import datetime

class User(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    age = db.Column(db.Integer, nullable=False, default=-1)
    gender = db.Column(db.String(10), nullable=False, default='-')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    movies = db.relationship('Interaction', back_populates='user')

    def set_password(self, password):
        """Hash and set password"""
        from app import flask_bcrypt
        self.password_hash = flask_bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if provided password matches hash"""
        from app import flask_bcrypt
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return "<user '{}'>".format(self.id)


class Movie(db.Model):
    __tablename__ = "Movie"

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    title = db.Column(db.String(50))
    genre = db.Column(db.String(50))
    date = db.Column(db.Date)
    users = db.relationship('Interaction', back_populates='movie')
    poster = db.Column(db.String(100))

    def __repr__(self):
        return "<movie '{}'>".format(self.title)

class Interaction(db.Model):
    __tablename__ = "Interaction"

    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movie.id'), primary_key=True)
    rating = db.Column(db.Integer)  
    timestamp = db.Column(db.Integer, nullable=True)
    interaction_type = db.Column(db.String(20), nullable=False, default='view')  # view, select, recommend, rate
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', back_populates='movies')
    movie = db.relationship('Movie', back_populates='users')

    def to_dict(self):
        """Convert interaction to dictionary"""
        return {
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'rating': self.rating,
            'interaction_type': self.interaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return "<User {} - Movie {} - Rating {}>".format(self.user.id, self.movie.title, self.rating)