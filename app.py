from flask import render_template,request,redirect,flash,Flask, url_for, session
from flask_sqlalchemy import SQLAlchemy as sq
import bcrypt
import re
from sqlalchemy import text
from flask import jsonify, session, g
import sqlite3
from recommender import get_user_favorite_movie_ids, recommend_movies
app = Flask(__name__)
app.secret_key = '228337'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
db = sq(app)
DATABASE = 'instance/web.db'


class Cameramen(db.Model):
    cameraman_id = db.Column(db.Integer, primary_key=True)
    cameraman_name = db.Column(db.Text, nullable=False)
    cameraman_movies = db.Column(db.Text, nullable=False)
    cameraman_biography = db.Column(db.Text, nullable=False)


class Editors(db.Model):
    editor_id = db.Column(db.Integer, primary_key=True)
    editor_name = db.Column(db.Text, nullable=False)
    editor_movies = db.Column(db.Text, nullable=False)
    editor_biography = db.Column(db.Text, nullable=False)


class Screenwriters(db.Model):
    screenwriter_id = db.Column(db.Integer, primary_key=True)
    screenwriter_name = db.Column(db.Text, nullable=False)
    screenwriter_movies = db.Column(db.Text, nullable=False)
    screenwriter_biography = db.Column(db.Text, nullable=False)


class Composers(db.Model):
    composer_id = db.Column(db.Integer, primary_key=True)
    composer_name = db.Column(db.Text, nullable=False)
    composer_movies = db.Column(db.Text, nullable=False)
    composer_biography = db.Column(db.Text, nullable=False)


class Actors(db.Model):
    actor_id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.Text, nullable=False)
    actor_movies = db.Column(db.Text, nullable=False)
    actor_biography = db.Column(db.Text, nullable=False)


class Artists(db.Model):
    artist_id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.Text, nullable=False)
    artist_movies = db.Column(db.Text, nullable=False)
    artist_biography = db.Column(db.Text, nullable=False)


class Directors(db.Model):
    director_id = db.Column(db.Integer, primary_key=True)
    director_name = db.Column(db.Text, nullable=False)
    director_movies = db.Column(db.Text, nullable=False)
    director_biography = db.Column(db.Text, nullable=False)


class Reviews(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    movie_title = db.Column(db.Text, nullable=False)
    review_title = db.Column(db.Text, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    reviewusername = db.Column(db.Text,nullable=False)
    review_likes = db.Column(db.Integer, nullable=False)
    review_dislikes = db.Column(db.Integer, nullable=False)


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    user_email = db.Column(db.Text, nullable=False)
    user_password = db.Column(db.LargeBinary, nullable=False)
    first_name = db.Column(db.String(80),nullable=False)
    last_name = db.Column(db.String(80),nullable=False)

class Movies(db.Model):
    movie_id = db.Column(db.Integer, primary_key=True)
    movie_title = db.Column(db.String, nullable=False)
    movie_description = db.Column(db.Text, nullable=False)
    movie_date = db.Column(db.Text, nullable=False)
    movie_rating = db.Column(db.Float, nullable=False)
    movie_genre = db.Column(db.String, nullable=False)
    movie_country = db.Column(db.String, nullable=False)
    movie_budget = db.Column(db.Text, nullable=False)
    movie_box_office = db.Column(db.Text, nullable=False)

class Comments(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    comment_username = db.Column(db.Text, nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    comment_review_id = db.Column(db.Integer, nullable=False)

class UserFavorites(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), primary_key=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@app.route('/home')
@app.route('/')
def home():
    if 'loggedin' in session:
        if session['loggedin']==True:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('home.html',username=username,loggedin=True)
    else:
        return render_template('home.html',loggedin=False)

@app.route('/about')
def about():
    if 'loggedin' in session:
        if session['loggedin'] == True:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('about.html', username=username, loggedin=True)
    else:
        return render_template('about.html', loggedin=False)

@app.route('/reviews_like/<int:review_id>')
def reviews_like(review_id):
    review = Reviews.query.filter_by(review_id=review_id).first()
    if review:
        review.review_likes += 1
        db.session.commit()
        return jsonify({
            'success': True,
            'likes': review.review_likes,
            'dislikes': review.review_dislikes
        })
    return jsonify({'success': False}), 404

@app.route('/reviews_dislike/<int:review_id>')
def reviews_dislike(review_id):
    review = Reviews.query.filter_by(review_id=review_id).first()
    if review:
        review.review_dislikes += 1
        db.session.commit()
        return jsonify({
            'success': True,
            'likes': review.review_likes,
            'dislikes': review.review_dislikes
        })
    return jsonify({'success': False}), 404

@app.route('/reviews_post', methods=['POST','GET'])
def reviews_post():
    if 'loggedin' in session:
        user_id = session['id']
        username = Users.query.filter_by(user_id=user_id).first().username
        if request.method=='POST':
                post_movie_title = request.form['movie_title']
                post_review_title = request.form['review_title']
                post_review_text = request.form['review_text']
                user_id = session['id']
                username = Users.query.filter_by(user_id=user_id).first().username
                post = Reviews(movie_title=post_movie_title,review_title=post_review_title,review_text=post_review_text,reviewusername=username,review_likes=0,review_dislikes=0)
                if Movies.query.filter_by(movie_title=post_movie_title).first()==None:
                    return render_template('reviews_post_error.html',username=username,loggedin=True,message='Фильм не найден')
                if post_review_text!='' and post_review_title!='' and post_movie_title!='':
                    try:
                        db.session.add(post)
                        db.session.commit()
                        return render_template('reviews_post_success.html',username=username,loggedin=True,message='Отзыв добавлен')
                    except:
                        message = 'При добавлении отзыва произошла ошибка, попробуйте позже'
                        return render_template('reviews_post_error.html',username=username,loggedin=True,message=message)
                else:
                    message = 'Пожалуйста, заполните все поля'
                    return render_template('reviews_post_error.html',username=username,loggedin=True,message=message)
        else:
            return render_template('reviews_post.html',username=username,loggedin=True)
    else:
        return redirect(url_for('login'))

@app.route('/popular')
def popular():
    sort_by = request.args.get('sort_by', 'movie_rating')
    order = request.args.get('order', 'desc')

    query = Movies.query.order_by(
        getattr(Movies, sort_by).desc() if order == 'desc' else getattr(Movies, sort_by).asc()
    )
    movies = query.all()

    liked_movie_ids = set()
    if 'loggedin' in session and session['loggedin'] == True:
        user_id = session['id']
        username = Users.query.filter_by(user_id=user_id).first().username

        liked = db.session.execute(
            text('SELECT movie_id FROM user_favorites WHERE user_id = :user_id'),
            {'user_id': user_id}
        ).fetchall()
        liked_movie_ids = set(row[0] for row in liked)

        return render_template(
            'popular.html',
            username=username,
            popular=movies,
            order=order,
            sort_by=sort_by,
            loggedin=True,
            liked_movie_ids=liked_movie_ids
        )

    return render_template(
        'popular.html',
        popular=movies,
        order=order,
        sort_by=sort_by,
        loggedin=False,
        liked_movie_ids=liked_movie_ids
    )


@app.route('/search', methods=['GET', 'POST'])
def search():
    loggedin = session.get('loggedin', False)
    username = None
    if loggedin:
        user_id = session['id']
        user = Users.query.filter_by(user_id=user_id).first()
        if user:
            username = user.username

    if request.method == 'POST':
        requested = request.form['movie_title']
        # Сначала ищем точное совпадение по названию фильма
        movie = Movies.query.filter_by(movie_title=requested).first()
        if movie:
            return render_template('movie.html', movie=movie, username=username, loggedin=loggedin)

        # Проверяем по всем ролям (актер, режиссер и т.д.)
        role_models = [
            (Actors, 'actor_name', 'actor_movies'),
            (Artists, 'artist_name', 'artist_movies'),
            (Directors, 'director_name', 'director_movies'),
            (Cameramen, 'cameraman_name', 'cameraman_movies'),
            (Composers, 'composer_name', 'composer_movies'),
            (Screenwriters, 'screenwriter_name', 'screenwriter_movies'),
            (Editors, 'editor_name', 'editor_movies'),
        ]

        for model, name_field, movies_field in role_models:
            person = model.query.filter(getattr(model, name_field) == requested).first()
            if person:
                movie_titles = getattr(person, movies_field).split(', ')
                for title in movie_titles:
                    movie = Movies.query.filter_by(movie_title=title).first()
                    if movie:
                        return render_template('movie.html', movie=movie, username=username, loggedin=loggedin)

        # Если ничего не найдено
        return render_template('search.html', username=username, loggedin=loggedin, msg='Ничего не найдено')

    return render_template('search.html', username=username, loggedin=loggedin)


@app.route('/review/<int:review_id>', methods=['POST','GET'])
def review(review_id):
    if 'loggedin' in session:
        if session['loggedin']==True:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            if request.method == 'POST':
                comment_text = request.form['comment_text']
                comment = Comments(comment_text=comment_text, comment_review_id=review_id,comment_username=username)
                db.session.add(comment)
                db.session.commit()
            review = Reviews.query.filter_by(review_id=review_id).first()
            comments = Comments.query.filter_by(comment_review_id=review_id).all()
            return render_template('review.html',review=review,username=username,loggedin=True,comments=comments)
    else:
        comments = Comments.query.filter_by(comment_review_id=review_id).all()
        if request.method == 'POST': return redirect(url_for('login'))
        review = Reviews.query.filter_by(review_id=review_id).first()
        return render_template('review.html',review=review,loggedin=False,comments=comments)

@app.route('/reviews')
def reviews():
    if 'loggedin' in session:
        if session['loggedin']==True:
            user_id=session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            reviews=Reviews.query.all()
            return render_template('reviews.html',reviews=reviews,username=username,loggedin=True)
    else:
        reviews = Reviews.query.all()
        return render_template('reviews.html', reviews=reviews,loggedin=False)

@app.route('/register', methods=['POST','GET'])
def register():
    msg = ''
    if 'loggedin' in session:
        if session['loggedin']==True:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('register.html',username=username,loggedin=True)
    elif request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        account = Users.query.filter_by(username=username).first()
        if account:
            msg = 'Аккаунт с таким именем уже существует.'
        elif not username or not password or not email:
            msg = 'Пожалуйста, заполните все поля.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Такой почты не существует.'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Имя пользователя должно содержать только латиницу и цифры!'
        else:
            passwordhash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            post = Users(username=username, user_password=passwordhash, user_email=email)
            try:
                db.session.add(post)
                db.session.commit()
                account = Users.query.filter_by(username=username).first()
                session['loggedin'] = True
                session['id'] = account.user_id
                session['username'] = account.username
                return render_template('register.html',loggedin=True,username=username)
            except:
                msg='Что-то пошло не так.'
    elif request.method == 'POST':
        msg = 'Пожалуйста, заполните все поля.'
    return render_template('register.html', msg=msg,loggedin=False)

@app.route('/login',methods=['GET','POST'])
def login():
    msg = ''
    if 'loggedin' in session:
        if session['loggedin']==True:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('login.html',username=username,loggedin=True)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = Users.query.filter_by(username=username).first()
        if account and bcrypt.checkpw(password.encode('utf-8'), account.user_password):
            session['loggedin']=True
            session['id'] =account.user_id
            session['username']=account.username
            return redirect(url_for('home'))
        else:
            msg = 'Неверное имя пользователя/пароль!'
    return render_template('login.html',msg=msg,loggedin=False)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template('home.html',loggedin=False)


@app.route('/account', methods=['GET', 'POST'])
def account():
    user_id = session['id']
    user = Users.query.filter_by(user_id=user_id).first()
    username = user.username
    reviews = Reviews.query.filter_by(reviewusername=username).all()
    msg = ''
    password_msg = ''

    # Получаем избранные фильмы
    favorite_movie_ids = db.session.query(UserFavorites.movie_id).filter_by(user_id=user_id).all()
    favorite_movie_ids = [mid for (mid,) in favorite_movie_ids]
    favorite_movies = Movies.query.filter(Movies.movie_id.in_(favorite_movie_ids)).all()

    if request.method == 'POST':
        if 'first_name' in request.form:  # Обновление имени/фамилии
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            user.first_name = first_name
            user.last_name = last_name
            try:
                db.session.commit()
                msg = 'Данные успешно обновлены.'
            except Exception as e:
                db.session.rollback()
                msg = 'Ошибка при обновлении данных.'

        elif 'current_password' in request.form:  # Смена пароля
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Проверяем текущий пароль с bcrypt
            stored_hash = user.user_password
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
                password_msg = 'Текущий пароль введён неверно.'
            elif len(new_password) < 6:
                password_msg = 'Новый пароль должен содержать не менее 6 символов.'
            elif new_password != confirm_password:
                password_msg = 'Новые пароли не совпадают.'
            else:
                # Хешируем новый пароль и сохраняем как строку
                new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.user_password = new_hash.decode('utf-8')
                try:
                    db.session.commit()
                    password_msg = 'Пароль успешно изменён.'
                except:
                    db.session.rollback()
                    password_msg = 'Ошибка при изменении пароля.'

    return render_template('account.html',
                           username=username,
                           email=user.user_email,
                           first_name=user.first_name or '',
                           last_name=user.last_name or '',
                           reviews=reviews,
                           favorite_movies=favorite_movies,
                           msg=msg,
                           password_msg=password_msg,
                           loggedin=True)

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movies.query.get_or_404(movie_id)
    title = movie.movie_title

    directors = Directors.query.filter(Directors.director_movies.contains(title)).all()
    artists = Artists.query.filter(Artists.artist_movies.contains(title)).all()
    editors = Editors.query.filter(Editors.editor_movies.contains(title)).all()
    actors = Actors.query.filter(Actors.actor_movies.contains(title)).all()
    composers = Composers.query.filter(Composers.composer_movies.contains(title)).all()
    cameramen = Cameramen.query.filter(Cameramen.cameraman_movies.contains(title)).all()
    screenwriters = Screenwriters.query.filter(Screenwriters.screenwriter_movies.contains(title)).all()
    loggedin = session.get('loggedin', False)
    username = None

    if loggedin:
        user_id = session.get('id')
        user = Users.query.filter_by(user_id=user_id).first()
        if user:
            username = user.username
    return render_template(
        'movie_detail.html',
        movie=movie,
        directors=directors,
        artists=artists,
        editors=editors,
        actors=actors,
        composers=composers,
        cameramen=cameramen,
        screenwriters=screenwriters,
        loggedin=loggedin,
        username=username
    )





@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    movie = Movies.query.get_or_404(movie_id)
    editors = Editors.query.filter(Editors.editor_movies.ilike(f'%{movie.movie_title}%')).all()
    directors = Directors.query.filter(Directors.director_movies.ilike(f'%{movie.movie_title}%')).all()
    artists = Artists.query.filter(Artists.artist_movies.ilike(f'%{movie.movie_title}%')).all()
    composers = Composers.query.filter(Composers.composer_movies.ilike(f'%{movie.movie_title}%')).all()
    cameramen = Cameramen.query.filter(Cameramen.cameraman_movies.ilike(f'%{movie.movie_title}%')).all()
    actors = Actors.query.filter(Actors.actor_movies.ilike(f'%{movie.movie_title}%')).all()
    screenwriters = Screenwriters.query.filter(Screenwriters.screenwriter_movies.ilike(f'%{movie.movie_title}%')).all()
    if 'loggedin' in session and session['loggedin']:
        user_id = session['id']
        username = Users.query.filter_by(user_id=user_id).first().username
        return render_template('movie_detail.html', movie=movie, username=username,directors=directors, editors=editors,
                               cameramen=cameramen,artists=artists,actors=actors,screenwriters=screenwriters,composers=composers,loggedin=True)
    else:
        return render_template('movie_detail.html', movie=movie,directors=directors, editors=editors,
                               cameramen=cameramen,artists=artists,actors=actors,screenwriters=screenwriters,composers=composers,loggedin=False)

@app.route('/person_detail/<int:type>/<int:numb>')
def person_detail(type,numb):
    if type==1:
        director=Directors.query.filter(Directors.director_id.ilike(f'%{numb}%')).first()
        name=director.director_name
        biography=director.director_biography
        movies=director.director_movies
        upper = 'Режиссёр'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==2:
        artist=Artists.query.filter(Artists.artist_id.ilike(f'%{numb}%')).first()
        name = artist.artist_name
        biography = artist.artist_biography
        movies = artist.artist_movies
        upper='Художник'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==3:
        editor=Editors.query.filter(Editors.editor_id.ilike(f'%{numb}%')).first()
        name = editor.editor_name
        biography = editor.editor_biography
        movies = editor.editor_movies
        upper='Монтажёр'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==4:
        actor=Actors.query.filter(Actors.actor_id.ilike(f'%{numb}%')).first()
        name = actor.actor_name
        biography = actor.actor_biography
        movies = actor.actor_movies
        upper='Актёр'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==5:
        composer=Composers.query.filter(Composers.composer_id.ilike(f'%{numb}%')).first()
        name = composer.composer_name
        biography = composer.composer_biography
        movies = composer.composer_movies
        upper='Композитор'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==6:
        cameraman=Cameramen.query.filter(Cameramen.cameraman_id.ilike(f'%{numb}%')).first()
        name = cameraman.cameraman_name
        biography = cameraman.cameraman_biography
        movies = cameraman.cameraman_movies
        upper='Оператор'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)
    elif type==7:
        screenwriter=Screenwriters.query.filter(Screenwriters.screenwriter_id.ilike(f'%{numb}%')).first()
        name = screenwriter.screenwriter_name
        biography = screenwriter.screenwriter_biography
        movies = screenwriter.screenwriter_movies
        upper='Сценарист'
        if 'loggedin' in session and session['loggedin']:
            user_id = session['id']
            username = Users.query.filter_by(user_id=user_id).first().username
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,username=username,loggedin=True)
        else:
            return render_template('person_detail.html', name=name, type=type, biography=biography, movies=movies,
                                   upper=upper,loggedin=False)


@app.route('/toggle_favorite/<int:movie_id>', methods=['POST'])
def toggle_favorite(movie_id):
    if 'id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['id']
    conn = get_db()

    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user_favorites WHERE user_id = ? AND movie_id = ?', (user_id, movie_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('DELETE FROM user_favorites WHERE user_id = ? AND movie_id = ?', (user_id, movie_id))
        conn.commit()
        return jsonify({'liked': False})
    else:
        cursor.execute('INSERT INTO user_favorites (user_id, movie_id) VALUES (?, ?)', (user_id, movie_id))
        conn.commit()
        return jsonify({'liked': True})




@app.route('/recommender')
def recommender():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))

    user_id = session['id']

    favorite_movie_ids = get_user_favorite_movie_ids(user_id, db.session)
    print("Избранные фильмы пользователя (ID):", favorite_movie_ids)

    recommended_movie_ids = recommend_movies(favorite_movie_ids, db.session)
    print("Рекомендуемые фильмы (ID):", recommended_movie_ids)

    if not recommended_movie_ids:
        print("Нет рекомендаций, возвращаем пустой список.")
        recommended_movies_sorted = []
    else:
        recommended_movies = Movies.query.filter(Movies.movie_id.in_(recommended_movie_ids)).all()
        recommended_movies_sorted = sorted(
            recommended_movies,
            key=lambda x: recommended_movie_ids.index(x.movie_id)
        )
        print(f"Получено из базы рекомендованных фильмов: {len(recommended_movies_sorted)}")

    thematic_collections = {
        "Лучшие комедии": Movies.query.filter(
            (Movies.movie_genre == "Комедия") & (Movies.movie_rating > 7.5)
        ).limit(6).all(),

        "Драмы": Movies.query.filter(
            (Movies.movie_genre == "Драма") & (Movies.movie_rating > 7.5)
        ).limit(6).all(),
    }

    username = Users.query.filter_by(user_id=user_id).first().username

    return render_template('recommender.html',
                           recommended_movies=recommended_movies_sorted,
                           thematic_collections=thematic_collections,
                           username=username,
                           loggedin=True)




if __name__ == '__main__':
    app.run(debug=True)