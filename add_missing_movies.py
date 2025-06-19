from app import app, db
from app import Movies, Actors, Directors  # Импорт моделей из app.py

def normalize_title(title):
    return title.strip().lower()

def add_missing_movies():
    all_actor_movies = []
    for actor in Actors.query.all():
        if actor.actor_movies:
            all_actor_movies.extend([m.strip() for m in actor.actor_movies.split(',') if m.strip()])

    all_director_movies = []
    for director in Directors.query.all():
        if director.director_movies:
            all_director_movies.extend([m.strip() for m in director.director_movies.split(',') if m.strip()])

    all_movies_titles = set(normalize_title(m) for m in all_actor_movies + all_director_movies)

    existing_movies = Movies.query.all()
    existing_titles = set(normalize_title(m.movie_title) for m in existing_movies)

    missing_titles = all_movies_titles - existing_titles

    print(f"Найдено фильмов для добавления: {len(missing_titles)}")

    for title in missing_titles:
        new_movie = Movies(movie_title=title.title(), movie_description="", movie_date=None)
        db.session.add(new_movie)

    db.session.commit()
    print("Добавление новых фильмов завершено.")

if __name__ == "__main__":
    with app.app_context():
        add_missing_movies()
