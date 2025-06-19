// static/js/popular.js

// Функция для обработки избранного
function toggleFavorite(el, isLoggedIn, movieId) {
  if (!isLoggedIn) {
    alert("Авторизуйтесь, чтобы добавить в избранное.");
    return;
  }

  fetch(`/toggle_favorite/${movieId}`, {
    method: 'POST'
  })
  .then(response => response.json())
  .then(data => {
    if (data.liked) {
      el.classList.add('fas');
      el.classList.remove('far');
      el.classList.add('active');
    } else {
      el.classList.add('far');
      el.classList.remove('fas');
      el.classList.remove('active');
    }
  })
  .catch(error => {
    console.error('Ошибка при отправке запроса:', error);
  });
}

// Функция для обработки сортировки
function initSorting() {
  const urlParams = new URLSearchParams(window.location.search);
  const sortBy = urlParams.get('sort_by');
  const order = urlParams.get('order');

  // Определяем какой тип сортировки активен
  let activeSort = '';
  if (sortBy === 'movie_rating' && order === 'desc') activeSort = 'rating-desc';
  if (sortBy === 'movie_rating' && order === 'asc') activeSort = 'rating-asc';
  if (sortBy === 'movie_date' && order === 'desc') activeSort = 'date-desc';
  if (sortBy === 'movie_date' && order === 'asc') activeSort = 'date-asc';

  // Если сортировка не указана, по умолчанию считаем rating-desc
  if (!activeSort && !sortBy && !order) activeSort = 'rating-desc';

  // Подсвечиваем активную кнопку
  if (activeSort) {
    const activeBtn = document.querySelector(`.sort-btn[data-sort="${activeSort}"]`);
    if (activeBtn) {
      // Сначала убираем активные классы у всех кнопок
      document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.opacity = '0.7';
      });

      // Затем добавляем активному
      activeBtn.classList.add('active');
      activeBtn.style.opacity = '1';

      // Добавляем анимацию для визуального подтверждения
      activeBtn.style.transform = 'scale(1.05)';
      setTimeout(() => {
        activeBtn.style.transform = 'scale(1)';
      }, 200);
    }
  }

  // Добавляем обработчики для плавного перехода
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      // Плавное затемнение перед переходом
      document.querySelector('.movies-grid').style.opacity = '0.7';
      document.querySelector('.movies-grid').style.transition = 'opacity 0.3s ease';
    });
  });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  initSorting();
});

// Восстанавливаем прозрачность после загрузки
window.addEventListener('load', function() {
  document.querySelector('.movies-grid').style.opacity = '1';
});