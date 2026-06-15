# Django Template Project

Template de projet Django moderne utilisant uv, ruff et pytest avec approche TDD.

## 🚀 Fonctionnalités

- ✅ Django 5.0+
- ✅ Gestion des dépendances avec **uv** (dependency-groups moderne)
- ✅ Linting et formatage avec **ruff**
- ✅ Tests avec **pytest** + couverture >95%
- ✅ **Approche TDD** (Test-Driven Development)
- ✅ Configuration multi-environnements (dev/prod)
- ✅ Variables d'environnement avec python-dotenv
- ✅ Static files avec WhiteNoise
- ✅ Configuration sécurisée pour la production
- ✅ **Git repository** avec workflow de branches

## 📁 Structure du projet

```
├── configurations/          # Configuration Django
│   ├── settings/
│   │   ├── __init__.py      # Sélection auto dev/prod
│   │   ├── base.py          # Configuration commune
│   │   ├── dev.py           # Développement
│   │   └── prod.py          # Production
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── tests/                   # Tests
├── static/                  # Fichiers statiques
├── templates/               # Templates Django
├── media/                   # Fichiers média
├── .env.example             # Variables d'environnement exemple
├── .env.dev                 # Config développement
├── .env.prod                # Config production
├── pyproject.toml           # Configuration uv, ruff, pytest
├── ruff.toml                # Configuration ruff (linting/formatage)
└── manage.py               # Script Django
```

## 🛠 Installation

1. Installer uv si ce n'est pas fait :
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Créer l'environnement virtuel et installer les dépendances :
```bash
uv sync
```

3. Appliquer les migrations :
```bash
uv run manage.py migrate
```

4. Créer un superutilisateur :
```bash
uv run manage.py createsuperuser
```

## 🏃‍♂️ Utilisation

### Développement

```bash
# Démarrer le serveur de développement
uv run manage.py runserver

# Lancer les tests
uv run pytest

# Linting et formatage
uv run ruff check .
uv run ruff format .
```

### Production

1. Configurer les variables d'environnement dans `.env.prod`
2. Définir `DJANGO_ENVIRONMENT=prod`
3. Collecter les fichiers statiques :
```bash
uv run manage.py collectstatic
```

## 🧪 Tests

Les tests sont configurés avec pytest-django :

```bash
# Lancer tous les tests
uv run pytest

# Tests avec couverture (objectif >95%)
uv run pytest --cov

# Tests spécifiques
uv run pytest tests/test_settings.py
```

## 📝 Configuration

### Variables d'environnement

Copier `.env.example` vers `.env.dev` ou `.env.prod` et configurer :

- `SECRET_KEY` : Clé secrète Django
- `DJANGO_ENVIRONMENT` : `dev` ou `prod`
- `DB_*` : Configuration base de données
- `ALLOWED_HOSTS` : Hosts autorisés (production)

### Sélection automatique des settings

Le module `configurations.settings.__init__.py` sélectionne automatiquement les bonnes configurations selon la variable `DJANGO_ENVIRONMENT`.

## 🔧 Outils de développement

- **uv** : Gestionnaire de dépendances moderne et rapide
- **ruff** : Linting et formatage ultra-rapide
- **pytest** : Framework de tests moderne avec couverture
- **django-debug-toolbar** : Debug en développement
- **django-extensions** : Commandes utiles pour Django

## 🧪 Méthodologie TDD (Test-Driven Development)

### Workflow TDD recommandé

1. **🔴 RED** : Écrire un test qui échoue
```bash
# Créer un test pour la nouvelle fonctionnalité
uv run pytest tests/test_nouvelle_feature.py
# ❌ Le test doit échouer
```

2. **🟢 GREEN** : Écrire le code minimal pour faire passer le test
```bash
# Implémenter le code minimal
uv run pytest tests/test_nouvelle_feature.py  
# ✅ Le test doit maintenant passer
```

3. **🔵 REFACTOR** : Améliorer le code en gardant les tests verts
```bash
# Vérifier que tous les tests passent
uv run pytest
# Vérifier le linting
uv run ruff check .
```

### Exigences de qualité

- **Couverture de tests** : >95% obligatoire
- **Linting** : ruff check sans warnings
- **Git** : Commit à chaque étape TDD

## 🔀 Workflow Git

### Gestion des branches

```bash
# Nouvelle fonctionnalité
git checkout -b feature/nouvelle-fonctionnalite

# Correction de bug  
git checkout -b fix/correction-bug

# Après validation des tests
git checkout main
git merge feature/nouvelle-fonctionnalite
```

### Commits recommandés

- **Petits commits fréquents** plutôt que gros commits
- **Un commit par fichier** maximum
- **Format conventionnel** :
  - `feat:` nouvelles fonctionnalités
  - `fix:` corrections de bugs
  - `test:` ajout/modification de tests
  - `refactor:` refactoring sans changement fonctionnel

## 📋 Checklist avant commit

- [ ] Tests passent : `uv run pytest`
- [ ] Couverture >95% : `uv run pytest --cov`
- [ ] Linting OK : `uv run ruff check .`
- [ ] Formatage OK : `uv run ruff format .`

## 🚀 Pour commencer

```bash
# Installer les dépendances
uv sync

# Lancer les migrations
uv run manage.py migrate

# Démarrer le serveur
uv run manage.py runserver

# Workflow qualité complet
uv run pytest          # Tests
uv run ruff check .    # Linting
uv run ruff format .   # Formatage
```

La sélection dev/prod se fait automatiquement via la variable `DJANGO_ENVIRONMENT` dans les fichiers .env.

## 🎨 Interface utilisateur

Le projet utilise un système d'interface moderne v2 avec :
- **CSS modulaire** : Variables CSS et architecture componentisée
- **Animations reveal** : Animations d'apparition échelonnées
- **Système de thème** : Dark/light mode avec persistance localStorage
- **Responsive design** : Grilles adaptatives et mobile-first
- **Lightbox** : Galerie photos avec navigation au clavier

### Architecture CSS
```
static/css/
├── base.css        # Variables, typographie, composants de base
├── home.css        # Page d'accueil
├── gallery.css     # Pages galeries
├── collection.css  # Pages collections avec lightbox
└── photo.css       # Pages photos détaillées
```

## ⚙️ Administration Django

### Gestion de l'ordre avec django-admin-sortable2

Le projet utilise `django-admin-sortable2` pour l'ordonnancement par drag & drop :

#### 🎯 **Avantages**
- **Interface intuitive** : Drag & drop directement sur les éléments
- **Multi-niveaux** : Galeries, collections et photos
- **Vignettes** : Ordonnancement visuel des photos via thumbnails
- **Cohérence UX** : Même interface pour tous les niveaux

#### 🛡️ **Considérations de sécurité**

**Architecture sécurisée :**
- **JavaScript côté client uniquement** (SortableJS)
- **Validation serveur obligatoire** : Toutes les modifications vérifiées en Python
- **Protection Django native** : CSRF tokens, permissions admin, authentification

**Risques potentiels JavaScript côté client :**
- XSS, manipulation DOM, vulnérabilités dépendances tierces
- MITM, contournement CSP

**Mitigations intégrées :**
- Session admin requise + permissions Django
- Validation serveur systématique même si JS manipulé
- CSRF protection automatique
- Surface d'attaque limitée à l'admin Django

#### 📋 **Installation recommandée**
```bash
# Installation django-admin-sortable2
uv add django-admin-sortable2

# Plus librairie vignettes au choix :
uv add django-admin-thumbnails  # Simple
uv add sorl-thumbnail           # Avancée
```

#### 💡 **Décision architecturale**

Pour un portfolio photographique, django-admin-sortable2 offre le meilleur équilibre :
- **UX optimale** pour l'ordonnancement visual
- **Sécurité acceptable** avec les protections Django
- **Architecture unifiée** sur tous les niveaux (galeries→collections→photos)

Alternative sans JS disponible si niveau sécurité critique requis.