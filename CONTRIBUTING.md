# Guide de Contribution - OpenPark 🎢

Merci de votre intérêt pour OpenPark! Ce guide explique comment contribuer au projet, que vous codiez **manuellement** ou en **vibe coding avec IA**.

---

## 🚀 Avant de commencer

### État du projet

⚠️ **Le projet n'est pas encore ouvert aux contributions externes.**

Nous finalisons les features core de la roadmap avant d'accepter des Pull Requests. En attendant:
- ⭐ **Star** le repo pour suivre l'avancement
- 👀 **Watch** pour être notifié de l'ouverture
- 💡 **Créez une Issue** pour proposer des idées

### Roadmap prioritaire

Consultez le [README.md](README.md#-roadmap-avant-contributions-externes) pour voir les features à implémenter avant l'ouverture.

---

## 🤝 Deux approches de contribution

OpenPark accepte **deux styles de développement**:

### 1. 🤖 **Vibe Coding** (Développement assisté par IA)
Utilisez des assistants IA (Claude, GPT, Cursor, etc.) pour générer et modifier le code via conversation.

### 2. 💻 **Codage traditionnel** (Code manuel)
Écrivez le code vous-même en utilisant votre éditeur préféré.

**Les deux approches sont également valorisées!** Choisissez celle qui vous convient le mieux.

---

## 🤖 Contribution en Vibe Coding

### Outils recommandés

- **Claude Code** - Terminal-based, excellent pour ce projet (utilisé pour le développement initial)
- **Cursor** - IDE avec IA intégrée
- **GitHub Copilot** - Extension VS Code/JetBrains
- **ChatGPT** - Mode code avec copy/paste
- **Windsurf** - IDE avec IA
- **Aider** - CLI pour édition assistée par IA

### Workflow vibe coding

#### 1. **Setup initial**
```bash
# Cloner le projet
git clone https://github.com/Enicay/openpark.git
cd openpark

# Créer une branche
git checkout -b feature/votre-feature

# Installer les dépendances
pip install -r requirements.txt
```

#### 2. **Développement avec IA**

**Exemple de session avec Claude Code:**
```
User: "Je veux implémenter le système de départ des visiteurs mécontents.
Les visiteurs avec satisfaction < 20% doivent quitter le parc."

Claude: "Je vais implémenter ce système. Commençons par..."
[L'IA génère le code, vous testez, itérez]

User: "Il y a un bug, les visiteurs ne partent pas correctement"

Claude: "Laisse-moi débugger. Je vais ajouter des logs pour..."
[L'IA identifie et corrige le bug]
```

#### 3. **Prompts efficaces**

**✅ Bon prompt:**
```
"Implémente le système de pause du jeu dans engine.py.
Il doit:
- Ajouter une variable self.paused (bool)
- Pause avec touche SPACE
- Afficher "PAUSED" à l'écran quand actif
- Ne pas update les guests/employees/rides quand en pause
Utilise le même style que le code existant."
```

**❌ Mauvais prompt:**
```
"Ajoute la pause"
```

**Conseils:**
- Soyez **spécifique** sur les requis
- Mentionnez les **fichiers concernés**
- Demandez à l'IA de **suivre le style existant**
- Décrivez le **comportement attendu**
- Testez et **itérez** si nécessaire

#### 4. **Testing**

```bash
# Lancer le jeu pour tester
python run.py

# L'IA peut vous aider à identifier les bugs:
"Le jeu crash quand je clique sur X, voici l'erreur: [stacktrace]"
```

#### 5. **Documentation de votre contribution**

Dans votre Pull Request, incluez:
```markdown
## Contribution Details

**Feature**: Système de pause du jeu
**IA utilisée**: Claude Sonnet 4.5 via Claude Code
**Temps de dev**: ~2 heures

### Prompts clés
1. "Implémente le système de pause..."
2. "Bug: le jeu ne reprend pas correctement après pause"
3. "Ajoute un indicateur visuel PAUSED à l'écran"

### Itérations
- Tentative 1: Pause simple (bug: employees continuaient à bouger)
- Tentative 2: Fix employees (bug: timers se décalaient)
- Tentative 3: Fix timers - ✅ Fonctionnel

### Difficultés
- Gérer les timers pendant la pause (résolu en n'incrémentant pas dt)
```

---

## 💻 Contribution Traditionnelle

### Setup développement

```bash
# Cloner le projet
git clone https://github.com/Enicay/openpark.git
cd openpark

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer une branche
git checkout -b feature/votre-feature
```

### Structure du projet

```
openpark/
├── themepark_engine/
│   ├── engine.py           # Boucle principale (update, render, events)
│   ├── agents.py           # IA des visiteurs (Guest class)
│   ├── rides.py            # Système d'attractions
│   ├── shops.py            # Boutiques
│   ├── employees.py        # 4 types d'employés
│   ├── queues.py           # Files d'attente linéaires
│   ├── serpent_queue.py    # Files serpentines
│   ├── litter.py           # Système de déchets
│   ├── economy.py          # Gestion financière
│   ├── map.py              # Grille de tuiles
│   ├── pathfinding.py      # A* standard et variantes
│   ├── debug.py            # Système de logging
│   └── renderers/
│       └── iso.py          # Projection oblique
├── run.py                  # Point d'entrée
└── CLAUDE.md              # Documentation pour IA (lisez-le!)
```

### Coding Standards

#### Style Python
- **PEP 8** pour le style général
- **Type hints** encouragés mais pas obligatoires
- **Docstrings** pour les méthodes publiques
- **Comments** en français ou anglais (les deux acceptés)

#### Conventions du projet

**Nommage:**
```python
# Classes: PascalCase
class Guest:
    pass

# Méthodes/fonctions: snake_case
def find_nearest_bin(self, guest):
    pass

# Constantes: UPPER_SNAKE_CASE
TILE_WALK = 1
```

**State machines:**
```python
# Utilisez des strings pour les états
self.state = "wandering"  # ✅
self.state = State.WANDERING  # ❌ (pas utilisé dans ce projet)
```

**Logging:**
```python
from .debug import DebugConfig

# Loguez les événements importants
DebugConfig.log('category', f"Message avec {variable}")

# Catégories disponibles: 'guests', 'rides', 'employees', 'engine', 'queues', 'litter'
```

### Architecture patterns

#### 1. **Component-based entities**
```python
class Guest:
    def __init__(self, x, y):
        # Position (float pour rendu smooth)
        self.x = float(x)
        self.y = float(y)
        # Grid position (int pour logique)
        self.grid_x = int(x)
        self.grid_y = int(y)

    def tick(self, dt: float):
        """Update avec delta time"""
        # Votre logique ici
```

#### 2. **State machines**
```python
def tick(self, dt: float):
    if self.state == "wandering":
        self._tick_wandering(dt)
    elif self.state == "queuing":
        self._tick_queuing(dt)
    # etc.

def _tick_wandering(self, dt: float):
    """Logique pour état wandering"""
    pass
```

#### 3. **Satisfaction system**
```python
# Utilisez les méthodes helper pour modifier la satisfaction
guest.modify_happiness(0.15, "completed ride")
guest.modify_satisfaction(-0.08, "had to drop litter")

# Pas de modification directe:
# guest.happiness += 0.15  # ❌
```

### Testing

```bash
# Lancer le jeu
python run.py

# Test manuel des features:
# 1. Placer des chemins
# 2. Construire une attraction
# 3. Ajouter des files d'attente
# 4. Observer le comportement des visiteurs
# 5. Vérifier les logs en mode debug
```

**Checklist avant PR:**
- [ ] Le jeu lance sans erreur
- [ ] La feature fonctionne comme prévu
- [ ] Pas de régression (features existantes toujours OK)
- [ ] Logs appropriés pour debugging
- [ ] Code suit les conventions du projet

---

## 🔧 Guidelines Communes (Vibe Coding ET Traditionnel)

### Workflow Git

```bash
# 1. Créer une branche depuis main
git checkout main
git pull origin main
git checkout -b feature/nom-feature

# 2. Faire vos modifications
# ... développement ...

# 3. Commit avec message descriptif
git add .
git commit -m "feat: Implement guest departure system for unhappy visitors

- Add departure threshold (satisfaction < 20%)
- Track departing guests in engine
- Log departures for debugging
- Update park stats to show departed count"

# 4. Push votre branche
git push origin feature/nom-feature

# 5. Créer une Pull Request sur GitHub
```

### Format des commits

Utilisez [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Nouvelle feature
fix: Correction de bug
docs: Documentation
refactor: Refactoring
test: Tests
chore: Tâches diverses
```

**Exemples:**
```
feat: Add game speed controls (pause, x1, x2, x3)
fix: Maintenance workers freezing when standing on litter
docs: Update CLAUDE.md with satisfaction system details
refactor: Extract satisfaction logic into separate methods
```

### Structure d'une Pull Request

```markdown
## Description
Implémente le système de départ des visiteurs mécontents.

## Type de contribution
- [x] Vibe Coding (Claude Sonnet 4.5)
- [ ] Code traditionnel

## Changes
- Ajout de `guest.should_leave()` dans `agents.py`
- Logique de départ dans `engine.py` (_handle_guest_departures)
- Stats de départ dans le panneau UI
- Tests manuels: 50+ guests, satisfaction < 20% partent correctement

## Checklist
- [x] Le code fonctionne
- [x] Pas de régression
- [x] Logs ajoutés
- [x] Style conforme au projet
- [x] Testé manuellement

## Screenshots
[Ajouter captures d'écran si pertinent]

## Notes
Les visiteurs mécontents affichent un indicateur rouge pendant 2s avant de partir.
```

### Review process

Une fois le projet ouvert:
1. **Mainteneurs review** votre code
2. **Feedback** si changements nécessaires
3. **Merge** une fois approuvé

**Ce qu'on regarde:**
- ✅ Fonctionnalité correcte
- ✅ Pas de régression
- ✅ Code lisible et maintenable
- ✅ Style cohérent avec le projet
- ✅ Logs appropriés

---

## 🎯 Features disponibles

Consultez la [Roadmap dans le README](README.md#-roadmap-avant-contributions-externes) pour les features à implémenter.

**Labels GitHub (à venir):**
- `good first issue` - Bon pour débuter
- `good for AI` - Adapté au vibe coding
- `needs manual coding` - Requiert expertise humaine
- `help wanted` - Contributions recherchées

---

## 💡 Tips pour les contributeurs

### Vibe Coding
- **Lisez CLAUDE.md** avant de commencer - contient toute l'architecture
- **Prompts itératifs** - Commencez simple, ajoutez des détails si nécessaire
- **Testez souvent** - L'IA peut générer du code qui compile mais ne fait pas ce que vous voulez
- **Partagez vos prompts** - Aidez les autres à apprendre

### Code traditionnel
- **Explorez le code existant** - Suivez les patterns établis
- **Consultez objects.json** - Définitions des entités du jeu
- **Utilisez le debug mode** - Activez les logs pour comprendre le flow
- **Petits commits fréquents** - Plus facile à review

### Pour tous
- **Communiquez** - Commentez sur les Issues, posez des questions
- **Documentez** - Expliquez vos choix dans les PR
- **Soyez patient** - Les reviews peuvent prendre du temps
- **Amusez-vous!** - C'est un projet fun et expérimental 🎢

---

## 🐛 Reporting Bugs

### Format d'une Issue

```markdown
**Description du bug**
Les mascots ne détectent pas les foules de plus de 10 visiteurs.

**Steps to reproduce**
1. Placer 15 visiteurs dans une queue
2. Ajouter une mascot
3. Observer que la mascot reste idle

**Comportement attendu**
La mascot devrait détecter la foule et aller divertir les visiteurs.

**Comportement observé**
La mascot reste en état "idle" indéfiniment.

**Logs (si disponible)**
```
DEBUG [employees]: Mascot 1234 searching for crowds - 15 guests
DEBUG [employees]: Mascot 1234 found NO crowds
```

**Environment**
- OS: Ubuntu 22.04
- Python: 3.10.12
- Pygame: 2.5.2
```

---

## 📚 Ressources

- **README.md** - Présentation du projet, features, installation
- **CLAUDE.md** - Documentation technique pour IA (mais utile pour tous!)
- **TODO.md** - Liste des tâches en cours
- **Issues GitHub** - Bugs connus et features proposées

---

## ❓ Questions?

- 💬 **Discussions GitHub** - Pour questions générales
- 🐛 **Issues** - Pour bugs et feature requests
- 📧 **Contact** - Créez une Issue pour les questions

---

**Merci de contribuer à OpenPark!** 🎢

Que vous codiez avec une IA ou à la main, votre contribution aide à faire de ce projet une vitrine de ce qui est possible en développement moderne de jeux vidéo.

---

*Dernière mise à jour: 2025-01-XX*
