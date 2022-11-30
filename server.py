from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
import functions
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
database = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = "jwt-secret-string"
jwt = JWTManager(app)


@dataclass()
class Users(database.Model):
    __tablename__ = "users"

    id: int
    login: str
    password: str

    id = database.Column(database.Integer, primary_key=True)
    login = database.Column(database.String(64))
    password = database.Column(database.String(64))


@dataclass()
class Links(database.Model):
    __tablename__ = "links"

    id: int
    user_id: int
    short_link: str
    long_link: str
    access_level: int
    alias: str
    count: int

    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer)
    short_link = database.Column(database.String(12))
    long_link = database.Column(database.String(64))
    access_level = database.Column(database.Integer)
    alias = database.Column(database.String(64), nullable=True)
    count = database.Column(database.Integer)


# РАБОТАЕТ
@app.route("/register_user", methods=["POST", "GET"])
def registration():
    return functions.register_user(database, Users)


# РАБОТАЕТ
@app.route("/auth_user", methods=["POST", "GET"])
def authentication():
    return functions.auth_user(database, Users)


# РАБОТАЕТ
@app.route("/add_link_authed", methods=["POST", "GET"])
@jwt_required()
def add_link_auth():
    return functions.add_link_auth(database, Links, Users)


# РАБОТАЕТ
@app.route("/add_link_unauthed", methods=["POST", "GET"])
def add_link_unauthed():
   return functions.add_link_unauth()


@app.route("/edit_link/<link>", methods=["POST", "GET"])
@jwt_required()
def editing_link(link):
   return functions.edit_link(database, Links, Users, link)


@app.route("/delete_link/<link>", methods=["POST", "GET"])
@jwt_required()
def deleting_link(link):
   return functions.delete_link(database, Links, Users, link)


@app.route("/counting/<link>", methods=["POST", "GET"])
def counting_by_redirect(link):
   return functions.counting(database, Links, link)


if __name__ == "__main__":
    app.run()
