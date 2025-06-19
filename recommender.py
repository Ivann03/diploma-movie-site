import re
from collections import defaultdict
from sqlalchemy import text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
embedding_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")

MIN_SCORE_THRESHOLD = 0.3
N_CLUSTERS = 10

WEIGHTS = {
    "actors": 0.25,
    "directors": 0.2,
    "tfidf": 0.3,
    "rating": 0.1,
    "genres": 0.1,
    "cluster": 0.05
}

def normalize_title(title):
    title = title.lower().strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^\w\s]', '', title)
    return title

def get_user_favorite_movie_ids(user_id, db_session):
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
    raw_scores = defaultdict(lambda: {'actor_director': 0.0, 'tfidf': 0.0, 'genre': 0.0, 'rating': 0.0, 'cluster': 0.0})

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

    # TF-IDF + кластеризация
    cursor = db.execute(text("SELECT movie_id, movie_title, movie_description FROM movies"))
    rows = cursor.mappings().all()
    descriptions = [row['movie_description'] or '' for row in rows]
    titles = [normalize_title(row['movie_title']) for row in rows]
    ids = [row['movie_id'] for row in rows]
    id_by_title = dict(zip(titles, ids))

    tfidf = TfidfVectorizer(max_features=5000)
    tfidf_matrix = tfidf.fit_transform(descriptions)

    # Embedding-модель по описаниям
    desc_embeddings = embedding_model.encode(descriptions, show_progress_bar=False)
    favorite_embed_indices = [titles.index(t) for t in favorite_titles if t in titles]
    if favorite_embed_indices:
        sim_embed = cosine_similarity(desc_embeddings[favorite_embed_indices], desc_embeddings)
        embed_scores = sim_embed.mean(axis=0)
        for i, score in enumerate(embed_scores):
            title = titles[i]
            if title not in favorite_titles:
                raw_scores[title]['embedding'] = score

    # Кластеризация
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init='auto')
    cluster_labels = kmeans.fit_predict(tfidf_matrix)

    title_to_cluster = dict(zip(titles, cluster_labels))

    # Индексы любимых фильмов
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

    # Учет кластеров
    favorite_clusters = set(title_to_cluster[t] for t in favorite_titles if t in title_to_cluster)
    for title in raw_scores:
        cluster = title_to_cluster.get(title)
        if cluster in favorite_clusters:
            raw_scores[title]['cluster'] += 1.0

    # Исключаем фильмы, которые уже в избранном
    for fav in favorite_titles:
        if fav in raw_scores:
            del raw_scores[fav]

    # Подсчет финального нормализованного score
    final_scores = {}
    for title, scores in raw_scores.items():
        combined_score = (
                WEIGHTS['actors'] * scores['actor_director'] +
                WEIGHTS['directors'] * scores['actor_director'] +  # можно разделить отдельно при желании
                WEIGHTS['tfidf'] * scores['tfidf'] +
                WEIGHTS['genres'] * scores['genre'] +
                WEIGHTS['rating'] * scores['rating'] +
                0.25 * scores.get('embedding', 0.0)
        )
        if combined_score > MIN_SCORE_THRESHOLD:
            final_scores[title] = combined_score

    sorted_movies = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    recommended_ids = []
    for title, score in sorted_movies:
        if title in id_by_title:
            recommended_ids.append(id_by_title[title])

    print("Рекомендуемые фильмы:")
    for title, score in sorted_movies[:10]:
        print(f"{title} — score={score:.2f}")

    return recommended_ids
