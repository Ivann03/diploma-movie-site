document.addEventListener('DOMContentLoaded', function() {
  // Обработчик для всех лайков
  document.querySelectorAll('.like-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      handleRating(e, this, 'like');
    });
  });

  // Обработчик для всех дизлайков
  document.querySelectorAll('.dislike-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      handleRating(e, this, 'dislike');
    });
  });

  function handleRating(e, element, type) {
    e.preventDefault();
    const reviewId = element.getAttribute('data-review-id');
    const url = type === 'like' ? `/reviews_like/${reviewId}` : `/reviews_dislike/${reviewId}`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        if(data.success) {
          // Обновляем только счетчики у текущей рецензии
          const reviewActions = element.closest('.review-actions');
          reviewActions.querySelector('.like-btn .count').textContent = data.likes;
          reviewActions.querySelector('.dislike-btn .count').textContent = data.dislikes;
        }
      });
  }
});