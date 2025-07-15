from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import MySQLdb
from flask_sqlalchemy import SQLAlchemy
from models import db, Post, User, Comment, Like
from flask import flash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey")
CORS(app)

def get_db_connection():
    return MySQLdb.connect(
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        db=os.getenv("DB_NAME"),
        charset='utf8'
    )

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()  # 테이블 없으면 생성

# ---------------- 기본 라우트 ---------------- #
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
    return jsonify(response.json())

@app.route("/db")
def db_test():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 'Flask에서 MySQL 연결 성공!'")
    result = cursor.fetchone()
    conn.close()
    return jsonify({"result": result[0]})

# ---------------- 게시판 기능 ---------------- #

# 임시 게시글 목록 (DB 연동 전까지는 메모리로 유지)
posts = [
    {"id": 1, "title": "첫 번째 글", "author": "admin", "created_at": "2025-07-15"}
]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = user.username
            return redirect(url_for("board"))
        else:
            return "로그인 실패", 401
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 이미 존재하는 사용자 체크
        existing = User.query.filter_by(username=username).first()
        if existing:
            return "이미 존재하는 사용자입니다", 400

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/board")
def board():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("board.html", posts=posts)

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        username = session.get("user", "익명")

        # 작성자 찾기 (없으면 오류처리)
        user = User.query.filter_by(username=username).first()
        if not user:
            return "작성자 정보 없음", 400

        new_post = Post(title=title, content=content, user_id=user.id)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("board"))

    return render_template("create_post.html")


@app.route("/board/<int:post_id>")
def board_detail(post_id):
    post = Post.query.get(post_id)
    if post is None:
        return "글을 찾을 수 없습니다.", 404
    return render_template("board_detail.html", post=post)


@app.route("/board/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return "글을 찾을 수 없습니다.", 404

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        db.session.commit()
        return redirect(url_for("board_detail", post_id=post.id))

    return render_template("board_edit.html", post=post)


@app.route("/board/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

    content = request.form.get("content")
    if not content:
        # 간단한 유효성 검사
        flash("댓글 내용을 입력해주세요.")
        return redirect(url_for("board_detail", post_id=post_id))

    post = Post.query.get(post_id)
    if not post:
        return "게시글이 없습니다.", 404

    username = session.get("user")
    user = User.query.filter_by(username=username).first()
    if not user:
        return "사용자 정보가 없습니다.", 400

    comment = Comment(content=content, user_id=user.id, post_id=post.id)
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for("board_detail", post_id=post_id))


@app.route("/board/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["user"]).first()
    post = Post.query.get(post_id)
    if not post:
        return "글을 찾을 수 없습니다", 404

    # 이미 좋아요 눌렀는지 확인
    existing_like = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
    if existing_like:
        # 좋아요 취소
        db.session.delete(existing_like)
    else:
        # 좋아요 추가
        new_like = Like(user_id=user.id, post_id=post_id)
        db.session.add(new_like)

    db.session.commit()
    return redirect(url_for("board_detail", post_id=post_id))
