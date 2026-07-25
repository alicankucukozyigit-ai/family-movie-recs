document.querySelectorAll(".add-favorite").forEach(function (container) {
  var memberId = container.dataset.memberId;
  var input = container.querySelector(".favorite-search-input");
  var results = container.querySelector(".favorite-search-results");
  var timer;

  input.addEventListener("input", function () {
    clearTimeout(timer);
    var query = input.value.trim();
    if (!query) {
      results.innerHTML = "";
      return;
    }
    timer = setTimeout(function () {
      fetch("/api/movie-search?q=" + encodeURIComponent(query))
        .then(function (r) { return r.json(); })
        .then(function (movies) {
          results.innerHTML = "";
          movies.forEach(function (movie) {
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "favorite-result";
            btn.textContent = movie.title + (movie.year ? " (" + movie.year + ")" : "");
            btn.addEventListener("click", function () {
              var form = document.createElement("form");
              form.method = "POST";
              form.action = "/members/" + memberId + "/favorites/add";
              ["tmdb_id", "title", "poster_path", "genre_ids"].forEach(function (key) {
                var field = document.createElement("input");
                field.type = "hidden";
                field.name = key;
                field.value = movie[key] || "";
                form.appendChild(field);
              });
              document.body.appendChild(form);
              form.submit();
            });
            results.appendChild(btn);
          });
        });
    }, 300);
  });
});

document.querySelectorAll(".movie-card").forEach(function (card) {
  var memberInput = card.querySelector(".rate-member-select");
  card.querySelectorAll(".rate-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var payload = {
        member_id: memberInput.value,
        tmdb_id: card.dataset.tmdbId,
        title: card.dataset.title,
        poster_path: card.dataset.posterPath,
        genre_ids: card.dataset.genreIds,
        thumbs_up: btn.dataset.thumb,
      };
      fetch("/ratings/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(function (r) {
        if (r.ok) {
          card.querySelectorAll(".rate-btn").forEach(function (b) {
            b.classList.remove("active");
          });
          btn.classList.add("active");
        }
      });
    });
  });
});

var sortSelect = document.getElementById("sort-select");
if (sortSelect) {
  var movieGrid = document.querySelector(".movie-grid");
  var sortKeyFor = {
    default: function (card) { return Number(card.dataset.originalIndex); },
    rating: function (card) { return -Number(card.dataset.rating); },
    title: function (card) { return card.dataset.title.toLowerCase(); },
  };

  sortSelect.addEventListener("change", function () {
    var mode = sortSelect.value;
    var cards = Array.prototype.slice.call(movieGrid.querySelectorAll(".movie-card"));

    cards.sort(function (a, b) {
      if (mode === "date") {
        var dateA = a.dataset.releaseDate || "";
        var dateB = b.dataset.releaseDate || "";
        return dateB.localeCompare(dateA);
      }
      var keyFn = sortKeyFor[mode] || sortKeyFor.default;
      var keyA = keyFn(a);
      var keyB = keyFn(b);
      if (keyA < keyB) return -1;
      if (keyA > keyB) return 1;
      return 0;
    });

    cards.forEach(function (card) { movieGrid.appendChild(card); });
  });
}
