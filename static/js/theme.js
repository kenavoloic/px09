// Bascule de thème clair/sombre avec persistance dans localStorage.
// Le thème est appliqué via l'attribut data-theme sur <html> (voir les
// blocs [data-theme="dark"] / [data-theme="light"] dans base.css).
(function () {
  "use strict";

  var STORAGE_KEY = "theme";
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);

    // L'icône affichée représente le thème vers lequel on bascule :
    // en sombre on propose le soleil (passer en clair), et inversement.
    var sun = document.getElementById("icon-sun");
    var moon = document.getElementById("icon-moon");
    if (sun && moon) {
      var sombre = theme === "dark";
      sun.style.display = sombre ? "" : "none";
      moon.style.display = sombre ? "none" : "";
    }
  }

  function themeInitial() {
    var sauvegarde = null;
    try {
      sauvegarde = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      // localStorage indisponible (mode privé strict, etc.)
    }
    if (sauvegarde === "dark" || sauvegarde === "light") {
      return sauvegarde;
    }
    // À défaut, conserver le thème déclaré sur <html> (sombre par défaut).
    return root.getAttribute("data-theme") || "dark";
  }

  function init() {
    applyTheme(themeInitial());

    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    toggle.addEventListener("click", function () {
      var actuel = root.getAttribute("data-theme") === "light" ? "light" : "dark";
      var nouveau = actuel === "dark" ? "light" : "dark";
      applyTheme(nouveau);
      try {
        localStorage.setItem(STORAGE_KEY, nouveau);
      } catch (e) {
        // Ignorer si l'écriture échoue.
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
