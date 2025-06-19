document.addEventListener('DOMContentLoaded', function() {
  // Обработчик лайков
  document.querySelector('.like-btn')?.addEventListener('click', function(e) {
    handleRating(e, this, 'like');
  });

  // Обработчик дизлайков
  document.querySelector('.dislike-btn')?.addEventListener('click', function(e) {
    handleRating(e, this, 'dislike');
  });

  function handleRating(e, element, type) {
    e.preventDefault();
    const reviewId = element.getAttribute('data-review-id');
    const url = type === 'like' ? `/reviews_like/${reviewId}` : `/reviews_dislike/${reviewId}`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        if(data.success) {
          // Обновляем счетчики на текущей странице
          document.querySelector('.like-btn .count').textContent = data.likes;
          document.querySelector('.dislike-btn .count').textContent = data.dislikes;
        }
      });
  }
});