// Modale d'accès aux galeries privées : ouverture/fermeture et envoi du
// formulaire (email + code) en AJAX vers la vue d'accueil, qui répond en JSON.
(function () {
  "use strict";

  var backdrop = document.getElementById("modal-backdrop");

  function openModal() {
    if (!backdrop) {
      return;
    }
    backdrop.classList.add("open");
    document.body.style.overflow = "hidden";
    var email = document.getElementById("email-input");
    if (email) {
      email.focus();
    }
  }

  function closeModal() {
    if (!backdrop) {
      return;
    }
    backdrop.classList.remove("open");
    document.body.style.overflow = "";
  }

  // Exposée globalement : le bouton de fermeture l'appelle via onclick.
  window.closePrivateModal = closeModal;

  function afficherErreur(message) {
    var champ = document.getElementById("code-error");
    if (champ) {
      champ.textContent = message;
      champ.style.display = "block";
    }
  }

  function setupSubmit() {
    var form = document.getElementById("private-form");
    if (!form) {
      return;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var endpoint = form.getAttribute("data-endpoint") || window.location.pathname;
      var bouton = form.querySelector("button[type=submit]");
      if (bouton) {
        bouton.disabled = true;
      }

      fetch(endpoint, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
      })
        .then(function (reponse) {
          return reponse.json();
        })
        .then(function (data) {
          if (data.success) {
            var contenu = document.getElementById("modal-form-content");
            var succes = document.getElementById("modal-success");
            if (contenu) {
              contenu.style.display = "none";
            }
            if (succes) {
              succes.style.display = "block";
            }
            if (data.redirect_url) {
              window.location.href = data.redirect_url;
            }
          } else {
            afficherErreur(data.error || "Une erreur est survenue. Réessayez.");
            if (bouton) {
              bouton.disabled = false;
            }
          }
        })
        .catch(function () {
          afficherErreur("Erreur de connexion. Veuillez réessayer.");
          if (bouton) {
            bouton.disabled = false;
          }
        });
    });
  }

  function init() {
    // Déclencheurs d'ouverture : tout élément portant [data-open-private].
    document.querySelectorAll("[data-open-private]").forEach(function (el) {
      el.addEventListener("click", function (event) {
        event.preventDefault();
        openModal();
      });
    });

    // Fermeture en cliquant sur le fond, hors de la boîte.
    if (backdrop) {
      backdrop.addEventListener("click", function (event) {
        if (event.target === backdrop) {
          closeModal();
        }
      });
    }

    // Fermeture avec la touche Échap.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeModal();
      }
    });

    setupSubmit();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
