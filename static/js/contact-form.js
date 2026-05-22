/**
 * Contact Form Enhanced - Option A: Moderne & minimaliste
 * Features: Labels flottants, validation temps réel, compteur de caractères
 */

document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.querySelector('.contact-form');
    if (!contactForm) return;

    // Éléments du formulaire
    const inputs = contactForm.querySelectorAll('.floating-input');
    const messageField = contactForm.querySelector('textarea[name="message"]');
    const submitButton = contactForm.querySelector('.btn-loading');
    const charCounter = contactForm.querySelector('.char-counter');
    
    // Configuration
    const config = {
        messageMaxLength: 1000,
        validationDelay: 500,
        messages: {
            required: 'Ce champ est requis',
            email: 'Adresse email invalide',
            minLength: 'Minimum 10 caractères requis',
            tooLong: 'Trop de caractères'
        }
    };

    // Initialisation
    init();

    function init() {
        setupFloatingLabels();
        setupRealTimeValidation();
        setupCharacterCounter();
        setupFormSubmission();
        setupFieldInteractions();
        setupCustomSelect();
    }

    // Labels flottants
    function setupFloatingLabels() {
        inputs.forEach(input => {
            // Vérifier si le champ a déjà du contenu au chargement
            checkFloatingLabel(input);
            
            // Écouter les changements
            input.addEventListener('input', () => checkFloatingLabel(input));
            input.addEventListener('focus', () => checkFloatingLabel(input));
            input.addEventListener('blur', () => checkFloatingLabel(input));
        });
    }

    function checkFloatingLabel(input) {
        const label = input.nextElementSibling;
        if (!label || !label.classList.contains('floating-label')) return;

        // Activer le label si le champ a du contenu ou est en focus
        if (input.value.trim() !== '' || input === document.activeElement) {
            label.classList.add('active');
        } else {
            label.classList.remove('active');
        }
    }

    // Validation en temps réel
    function setupRealTimeValidation() {
        inputs.forEach(input => {
            let validationTimeout;
            
            input.addEventListener('input', () => {
                clearTimeout(validationTimeout);
                validationTimeout = setTimeout(() => {
                    validateField(input);
                }, config.validationDelay);
            });
            
            input.addEventListener('blur', () => {
                validateField(input);
            });
        });
    }

    function validateField(input) {
        const statusElement = getStatusElement(input);
        const fieldName = input.name;
        const value = input.value.trim();
        
        // Reset
        const group = input.closest('.floating-group');
        input.classList.remove('valid', 'invalid');
        if (group) {
            group.classList.remove('field-valid', 'field-invalid');
        }
        if (statusElement) {
            statusElement.className = 'form-status';
            statusElement.textContent = '';
        }
        
        // Si le champ est vide, ne pas valider sauf si requis
        if (!value && !input.hasAttribute('required')) {
            return true;
        }
        
        // Validation spécifique par champ
        let isValid = true;
        let message = '';
        
        switch (fieldName) {
            case 'nom':
                if (!value) {
                    isValid = false;
                    message = config.messages.required;
                }
                break;
                
            case 'email':
                if (!value) {
                    isValid = false;
                    message = config.messages.required;
                } else if (!isValidEmail(value)) {
                    isValid = false;
                    message = config.messages.email;
                }
                break;
                
            case 'sujet':
                if (!value) {
                    isValid = false;
                    message = config.messages.required;
                }
                break;
                
            case 'message':
                if (!value) {
                    isValid = false;
                    message = config.messages.required;
                } else if (value.length < 10) {
                    isValid = false;
                    message = config.messages.minLength;
                }
                break;
        }
        
        // Appliquer le style et message
        if (isValid && value) {
            input.classList.add('valid');
            if (group) {
                group.classList.add('field-valid');
            }
            if (statusElement) {
                statusElement.classList.add('valid');
                statusElement.textContent = '✓';
            }
        } else if (!isValid) {
            input.classList.add('invalid');
            if (group) {
                group.classList.add('field-invalid');
            }
            if (statusElement) {
                statusElement.classList.add('invalid');
                statusElement.textContent = message;
            }
        }
        
        return isValid;
    }

    function getStatusElement(input) {
        const group = input.closest('.floating-group');
        return group ? group.querySelector('.form-status') : null;
    }

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Compteur de caractères
    function setupCharacterCounter() {
        if (!messageField || !charCounter) return;
        
        const charCount = charCounter.querySelector('.char-count');
        const charMax = charCounter.querySelector('.char-max');
        
        if (!charCount || !charMax) return;
        
        // Initialiser
        updateCharCounter();
        
        // Écouter les changements
        messageField.addEventListener('input', updateCharCounter);
        
        function updateCharCounter() {
            const length = messageField.value.length;
            const maxLength = config.messageMaxLength;
            
            charCount.textContent = length;
            
            // Changer la couleur selon le seuil
            charCounter.classList.remove('warning', 'danger');
            
            if (length > maxLength * 0.9) {
                charCounter.classList.add('danger');
            } else if (length > maxLength * 0.75) {
                charCounter.classList.add('warning');
            }
        }
    }

    // Soumission du formulaire
    function setupFormSubmission() {
        contactForm.addEventListener('submit', handleFormSubmit);
    }

    function handleFormSubmit(event) {
        // Valider tous les champs
        let isFormValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isFormValid = false;
            }
        });
        
        if (!isFormValid) {
            event.preventDefault();
            // Scroll vers le premier champ invalide
            const firstInvalid = contactForm.querySelector('.invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                firstInvalid.focus();
            }
            return;
        }
        
        // Montrer l'état de chargement
        showLoadingState();
    }

    function showLoadingState() {
        if (submitButton) {
            submitButton.classList.add('loading');
            submitButton.disabled = true;
        }
        
        // Auto-reset après 10 secondes (sécurité)
        setTimeout(() => {
            hideLoadingState();
        }, 10000);
    }

    function hideLoadingState() {
        if (submitButton) {
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
        }
    }

    // Interactions des champs
    function setupFieldInteractions() {
        inputs.forEach(input => {
            // Effet de focus amélioré
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
            });
        });
    }

    // Custom Select Component
    function setupCustomSelect() {
        const customSelect = contactForm.querySelector('.custom-select-wrapper');
        if (!customSelect) return;

        const trigger = customSelect.querySelector('.custom-select-trigger');
        const options = customSelect.querySelector('.custom-select-options');
        const hiddenSelect = customSelect.querySelector('.hidden-select');
        const placeholderText = trigger.querySelector('.placeholder-text');
        const selectedText = trigger.querySelector('.selected-text');

        if (!trigger || !options || !hiddenSelect) return;

        // Handle click on trigger
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            toggleDropdown();
        });

        // Handle keyboard navigation
        trigger.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleDropdown();
            } else if (e.key === 'Escape') {
                closeDropdown();
            }
        });

        // Handle option selection
        options.addEventListener('click', (e) => {
            const option = e.target.closest('.select-option');
            if (!option) return;

            selectOption(option);
        });

        // Handle keyboard navigation in options
        options.addEventListener('keydown', (e) => {
            const currentOption = options.querySelector('.select-option:focus');
            let nextOption = null;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    nextOption = currentOption ? 
                        currentOption.nextElementSibling : 
                        options.querySelector('.select-option');
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    nextOption = currentOption ? 
                        currentOption.previousElementSibling : 
                        options.querySelector('.select-option:last-child');
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    if (currentOption) selectOption(currentOption);
                    break;
                case 'Escape':
                    closeDropdown();
                    trigger.focus();
                    break;
            }

            if (nextOption) {
                nextOption.focus();
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!customSelect.contains(e.target)) {
                closeDropdown();
            }
        });

        function toggleDropdown() {
            const isOpen = trigger.getAttribute('aria-expanded') === 'true';
            
            if (isOpen) {
                closeDropdown();
            } else {
                openDropdown();
            }
        }

        function openDropdown() {
            trigger.setAttribute('aria-expanded', 'true');
            options.classList.remove('hidden');
            
            // Focus first option if none selected
            const selectedOption = options.querySelector('.select-option.selected');
            const firstOption = options.querySelector('.select-option');
            
            if (selectedOption) {
                selectedOption.focus();
            } else if (firstOption) {
                firstOption.focus();
            }
        }

        function closeDropdown() {
            trigger.setAttribute('aria-expanded', 'false');
            options.classList.add('hidden');
        }

        function selectOption(option) {
            const value = option.dataset.value;
            const text = option.querySelector('.option-text').textContent;

            // Update hidden select
            hiddenSelect.value = value;

            // Update visual state
            selectedText.textContent = text;
            trigger.classList.add('has-selection');

            // Update selected option
            options.querySelectorAll('.select-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            option.classList.add('selected');

            // Close dropdown
            closeDropdown();
            trigger.focus();

            // Trigger validation
            validateField(hiddenSelect);

            // Trigger change event for form handling
            const changeEvent = new Event('change', { bubbles: true });
            hiddenSelect.dispatchEvent(changeEvent);
        }

        // Initialize with existing value if any
        const initialValue = hiddenSelect.value;
        if (initialValue) {
            const option = options.querySelector(`[data-value="${initialValue}"]`);
            if (option) {
                selectOption(option);
            }
        }
    }

    // API publique pour le debug
    window.ContactForm = {
        validate: () => {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            return isValid;
        },
        reset: () => {
            hideLoadingState();
            inputs.forEach(input => {
                const group = input.closest('.floating-group');
                input.classList.remove('valid', 'invalid');
                if (group) {
                    group.classList.remove('field-valid', 'field-invalid');
                }
                const statusElement = getStatusElement(input);
                if (statusElement) {
                    statusElement.className = 'form-status';
                    statusElement.textContent = '';
                }
            });
        }
    };
});