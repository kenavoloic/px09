/* modal.js — modal d'accès aux galeries privées
   Branche le formulaire à l'endpoint Django (POST avec CSRF). */
(function() {
  const backdrop = document.getElementById('modal-backdrop');
  const form = document.getElementById('private-form');
  const successEl = document.getElementById('modal-success');
  const formContent = document.getElementById('modal-form-content');
  const emailInput = document.getElementById('email-input');
  const codeInput = document.getElementById('code-input');
  const emailError = document.getElementById('email-error');
  const codeError = document.getElementById('code-error');
  
  if (!backdrop) return;

  window.openPrivateModal = function() {
    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
    setTimeout(() => emailInput && emailInput.focus(), 300);
  };
  window.closePrivateModal = function() {
    backdrop.classList.remove('open');
    document.body.style.overflow = '';
    setTimeout(() => {
      if (successEl) successEl.style.display = 'none';
      if (formContent) formContent.style.display = 'block';
      if (form) form.reset();
      if (emailError) emailError.classList.remove('visible');
      if (codeError) codeError.classList.remove('visible');
    }, 350);
  };

  // Triggers
  document.querySelectorAll('[data-open-private]').forEach(el => {
    el.addEventListener('click', (e) => { e.preventDefault(); window.openPrivateModal(); });
  });

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) window.closePrivateModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.classList.contains('open')) window.closePrivateModal();
  });

  // Submit (à brancher sur endpoint Django)
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = emailInput.value.trim();
      const code = codeInput.value.trim();
      let valid = true;

      const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRe.test(email)) {
        emailError.classList.add('visible'); valid = false;
      } else { emailError.classList.remove('visible'); }
      if (code.length < 4) {
        codeError.classList.add('visible'); valid = false;
      } else { codeError.classList.remove('visible'); }
      if (!valid) return;

      // CSRF token Django
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      const endpoint = form.dataset.endpoint || '/';

      try {
        // Préparer les données de formulaire
        const formData = new FormData();
        formData.append('email', email);
        formData.append('code', code);
        formData.append('csrfmiddlewaretoken', csrfToken);

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken 
          },
          body: formData,
        });
        
        const data = await res.json();
        
        if (data.success && data.redirect_url) {
          formContent.style.display = 'none';
          successEl.style.display = 'block';
          setTimeout(() => { window.location.href = data.redirect_url; }, 800);
        } else {
          if (codeError) {
            codeError.textContent = data.error || 'Code ou email invalide.';
            codeError.classList.add('visible');
            codeError.style.display = 'block';
            codeError.style.color = 'red';
          } else {
            alert(data.error);
          }
        }
      } catch (err) {
        if (codeError) {
          codeError.textContent = 'Erreur de connexion. Veuillez réessayer.';
          codeError.classList.add('visible');
          codeError.style.display = 'block';
          codeError.style.color = 'red';
        } else {
          alert('Erreur de connexion. Veuillez réessayer.');
        }
      }
    });
  }
})();
