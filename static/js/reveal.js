// Animation « reveal on scroll » : ajoute la classe .visible aux éléments
// .reveal lorsqu'ils entrent dans la zone visible, ce qui déclenche leur
// apparition (voir les règles .reveal / .reveal.visible dans base.css).
(function () {
  "use strict";

  function revealAll(elements) {
    elements.forEach(function (el) {
      el.classList.add("visible");
    });
  }

  function init() {
    var elements = document.querySelectorAll(".reveal");
    if (elements.length === 0) {
      return;
    }

    // Repli pour les navigateurs sans IntersectionObserver : tout afficher.
    if (!("IntersectionObserver" in window)) {
      revealAll(elements);
      return;
    }

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -10% 0px" }
    );

    elements.forEach(function (el) {
      observer.observe(el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
