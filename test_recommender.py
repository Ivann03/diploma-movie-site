import re
from collections import defaultdict
from sqlalchemy import text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
MIN_SCORE_THRESHOLD = 0.3

WEIGHTS = {
    "actors": 0.25,
    "directors": 0.2,
    "tfidf": 0.35,
    "rating": 0.1,
    "genres": 0.1
}

def normalize_title(title):
    """Приводим название фильма к нижнему регистру, убираем лишние пробелы и знаки пунктуации."""
    title = title.lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^\w\s]', '', title)
    return title

def get_user_favorite_movie_ids(user_id, db_session):
    """Получает список ID любимых фильмов пользователя из таблицы user_favorites."""
    query = text("SELECT movie_id FROM user_favorites WHERE user_id = :user_id")
    result = db_session.execute(query, {"user_id": user_id})
    rows = result.mappings().all()
    return [row['movie_id'] for row in rows]


def recommend_movies(favorite_movie_ids, db):
    if not favorite_movie_ids:
        return []

    placeholders = ', '.join(f":id{i}" for i in range(len(favorite_movie_ids)))
    params = {f"id{i}": movie_id for i, movie_id in enumerate(favorite_movie_ids)}

    # Названия любимых фильмов
    cursor = db.execute(text(f"SELECT movie_id, movie_title FROM movies WHERE movie_id IN ({placeholders})"), params)
    favorite_titles = [normalize_title(row['movie_title']) for row in cursor.mappings().all()]

    # Жанры любимых фильмов
    cursor = db.execute(text(f"SELECT movie_genre FROM movies WHERE movie_id IN ({placeholders})"), params)
    favorite_genres = set()
    for row in cursor.mappings().all():
        genres = row['movie_genre'] or ''
        favorite_genres.update(g.strip().lower() for g in genres.split(',') if g.strip())

    # Актёры и режиссёры
    actors = db.execute(text("SELECT actor_name, actor_movies FROM actors")).mappings().all()
    directors = db.execute(text("SELECT director_name, director_movies FROM directors")).mappings().all()
    raw_scores = defaultdict(lambda: {'actor_director': 0.0, 'tfidf': 0.0, 'genre': 0.0, 'rating': 0.0})

    def update_scores(people, role_weight, key):
        for person in people:
            movies_raw = person.get('actor_movies') or person.get('director_movies') or ''
            movies_list = [normalize_title(m.strip()) for m in movies_raw.split(',') if m.strip()]
            common_count = sum(1 for fav in favorite_titles if fav in movies_list)
            if common_count > 0:
                for movie in movies_list:
                    raw_scores[movie][key] += role_weight * common_count

    update_scores(actors, role_weight=1.0, key='actor_director')
    update_scores(directors, role_weight=1.5, key='actor_director')

    # TF-IDF
    cursor = db.execute(text("SELECT movie_id, movie_title, movie_description FROM movies"))
    rows = cursor.mappings().all()
    descriptions = [row['movie_description'] or '' for row in rows]
    titles = [normalize_title(row['movie_title']) for row in rows]
    ids = [row['movie_id'] for row in rows]
    id_by_title = dict(zip(titles, ids))

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(descriptions)
    favorite_indices = [titles.index(t) for t in favorite_titles if t in titles]
    if not favorite_indices:
        return []

    sim_scores = cosine_similarity(tfidf_matrix[favorite_indices], tfidf_matrix)
    tfidf_scores = sim_scores.mean(axis=0)
    for i, score in enumerate(tfidf_scores):
        title = titles[i]
        if title not in favorite_titles:
            raw_scores[title]['tfidf'] += score * 2.0

    # Учет жанров
    cursor = db.execute(text("SELECT movie_title, movie_genre FROM movies"))
    for row in cursor.mappings().all():
        title = normalize_title(row['movie_title'])
        if title in favorite_titles or title not in raw_scores:
            continue
        movie_genres = row['movie_genre'] or ''
        movie_genres_set = set(g.strip().lower() for g in movie_genres.split(',') if g.strip())
        common_genres = favorite_genres.intersection(movie_genres_set)
        if common_genres:
            raw_scores[title]['genre'] += 0.5 * len(common_genres)

    # Учет рейтинга
    cursor = db.execute(text("SELECT movie_title, movie_rating FROM movies"))
    for row in cursor.mappings().all():
        title = normalize_title(row['movie_title'])
        if title in raw_scores:
            raw_scores[title]['rating'] = (row['movie_rating'] or 0) / 10.0

    # Исключаем фильмы, которые уже в избранном
    for fav in favorite_titles:
        if fav in raw_scores:
            del raw_scores[fav]

    # Подсчет нормализованного score
    final_scores = {}
    for title, scores in raw_scores.items():
        score = (
                scores['actor_director'] * 1.0 +
                scores['tfidf'] * 1.0 +
                scores['genre'] * 1.0
        )
        score *= (1 + scores['rating'])
        if score > MIN_SCORE_THRESHOLD:
            final_scores[title] = score

    sorted_movies = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    recommended_ids = []
    for title, score in sorted_movies:
        if title in id_by_title:
            recommended_ids.append(id_by_title[title])

    print("Рекомендуемые фильмы:")
    for title, score in sorted_movies[:10]:
        print(f"{title} — score={score:.2f}")

    return recommended_ids

