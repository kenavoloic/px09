# Django Template Project

Template de projet Django moderne utilisant uv, ruff, mypy et pytest avec approche TDD.

## 🚀 Fonctionnalités

- ✅ Django 5.0+
- ✅ Gestion des dépendances avec **uv** (dependency-groups moderne)
- ✅ Linting et formatage avec **ruff**
- ✅ **Typage strict avec mypy** + django-stubs
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
├── pyproject.toml           # Configuration uv, ruff, mypy, pytest
├── ruff.toml                # Configuration ruff (linting/formatage)
└── manage.py               # Script Django (typé)
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

# Vérification de typage
uv run mypy .

# Linting et formatage
uv run ruff check .
uv run ruff format .
```

### Production

1. Configurer les variables d'environnement dans `.env.prod`
2. Définir `DJANGO_ENVIRONMENT=prod`
3. Vérifier le typage :
```bash
uv run mypy .
```

4. Collecter les fichiers statiques :
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

# Vérification mypy strict
uv run mypy .
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
- **mypy** : Vérification de typage strict avec django-stubs
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
# Vérifier le typage
uv run mypy .
# Vérifier le linting
uv run ruff check .
```

### Exigences de qualité

- **Couverture de tests** : >95% obligatoire
- **Typage** : mypy --strict sans erreurs
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
- [ ] Typage OK : `uv run mypy .`
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
uv run mypy .          # Typage  
uv run ruff check .    # Linting
uv run ruff format .   # Formatage
```

La sélection dev/prod se fait automatiquement via la variable `DJANGO_ENVIRONMENT` dans les fichiers .env.