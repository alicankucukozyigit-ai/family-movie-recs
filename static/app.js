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
