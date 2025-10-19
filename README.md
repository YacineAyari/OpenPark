# OpenPark 🎢

**Clone open source du célèbre jeu Theme Park (Bullfrog Productions, 1994)**

OpenPark est une simulation de parc d'attractions en **projection oblique**, développée en Python avec Pygame. Gérez votre parc, construisez des attractions, employez du personnel, et gardez vos visiteurs heureux!

![Version](https://img.shields.io/badge/version-0.3.0--alpha-orange)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![AI-Powered](https://img.shields.io/badge/AI--Powered-Claude%20%26%20GPT-purple)
![Vibe Coding](https://img.shields.io/badge/Vibe%20Coding-100%25-ff69b4)

### 🤖 **Projet "Vibe Coding" avec IA**

Ce projet a été entièrement développé en **vibe coding** avec **Claude Sonnet 4.5** et **GPT-5**, démontrant la puissance de la collaboration humain-IA dans le développement de jeux vidéo complexes.

**Philosophie du projet:**
- ✨ Développement collaboratif assisté par IA de bout en bout
- 🧠 Tous les contributeurs (humains et IA) sont les bienvenus
- 🎯 **Challenge**: Maintenir une approche "full vibe coding" - tout le code peut être généré et modifié via conversation avec des IA
- 📚 Documentation et architecture pensées pour être "IA-friendly"

Ce projet est une vitrine de ce qu'on peut accomplir avec les outils d'IA modernes en développement de jeux!

#### 💡 Exemples d'accomplissements en vibe coding (sessions de quelques heures):

- ✅ **Système d'employés complet** (4 types avec IA complexe, pathfinding personnalisé)
- ✅ **Système de satisfaction dynamique** (15+ facteurs influençant le comportement des visiteurs)
- ✅ **Files d'attente serpentines** (détection automatique de patterns, mouvements directionnels)
- ✅ **Gestion du litter** (state machine visiteurs, assignation automatique d'employés)
- ✅ **Projection oblique configurable** (math oblique, picking inverse, debug controls)
- ✅ **UI temps réel** (stats colorées, indicateurs visuels, feedback instantané)

**Résultat**: Un moteur de jeu complet et fonctionnel développé entièrement via conversation avec IA! 🚀

---

## 📸 Screenshots

*Coming soon - Captures d'écran du jeu en action*

**Screenshots à ajouter:**
- 🎡 Vue d'ensemble d'un parc avec attractions, chemins, files d'attente
- 👥 Indicateurs de satisfaction colorés au-dessus des visiteurs (🟢🟡🔴)
- 📊 Panneau de statistiques en temps réel (top-left)
- 👷 Employés en action (maintenance worker cleaning, engineer repairing, mascot entertaining)
- 🔧 Menu debug montrant les réglages de projection oblique
- 🎢 Queue serpentine connectée à une attraction

---

## 🎮 Caractéristiques

### ✅ Déjà implémenté

#### 🏗️ **Système de construction**
- **Chemins piétonniers** - Réseau de paths pour la circulation des visiteurs
- **Attractions** (Rides) - Placement multi-tuiles avec entrées/sorties
- **Boutiques** (Shops) - Génération de revenus et de litter
- **Poubelles** - Gestion de la propreté du parc
- **Files d'attente** - Système de queues linéaires et serpentines

#### 👥 **Intelligence Artificielle des visiteurs**
- **State machine complète** - 11 états différents (wandering, queuing, riding, shopping, etc.)
- **Préférences personnalisées** - Tolérance au thrill et à la nausée
- **Système de satisfaction dynamique** - Happiness, Excitement, Satisfaction
  - Dégradation naturelle au fil du temps
  - Bonus: rides, shopping, propreté, queues courtes
  - Pénalités: attente, litter, pannes, queues longues
- **Gestion du litter** - Les visiteurs cherchent des poubelles ou jettent par terre

#### 👷 **Système d'employés (4 types)**
- **Engineers** - Réparent les attractions en panne, marchent partout
- **Maintenance Workers** - Nettoient le litter, patrouillent les chemins
- **Security Guards** - Patrouillent et boostent la satisfaction des visiteurs (+5%)
- **Mascots** - Détectent les foules et augmentent l'excitement (+10%)

#### 🎨 **Rendu et Interface**
- **Projection oblique configurable** - Angle φ ajustable, taille de tuiles personnalisable
- **Feedback visuel en temps réel** - Indicateurs colorés de satisfaction (🟢🟡🔴)
- **Panneau de statistiques** - Cash, visiteurs, satisfaction moyenne, employés, litter
- **Caméra libre** - Pan (WASD/arrows), zoom (+/-), drag (middle-click)

#### 💰 **Système économique**
- **Revenus** - Income des boutiques quand les visiteurs achètent
- **Dépenses** - Coûts de construction, salaires des employés
- **Gestion du cash** - Suivi en temps réel des finances

#### 🔧 **Gameplay**
- **Pannes d'attractions** - Probabilité de breakdown, évacuation des queues
- **Assignation automatique** - Les employés trouvent automatiquement du travail
- **Pathfinding A*** - Navigation intelligente pour visiteurs et employés
- **Mouvement fluide** - Interpolation smooth des positions (60 FPS)

#### 🐛 **Debug & Development**
- **Système de logging catégorisé** - GUESTS, RIDES, EMPLOYEES, ENGINE, etc.
- **Menu debug** - Toggle des logs, réglages de projection
- **Toolbar organisée** - Placement facile par glisser-déposer

---

### 🚧 Roadmap avant contributions externes

#### 🎯 **Priorité HAUTE (Quick Wins)**

- [ ] **Départ des visiteurs mécontents**
  - Les visiteurs avec satisfaction < 20% quittent le parc
  - Perte de revenus potentiels, indicateur de performance

- [ ] **Prix d'entrée du parc / Tickets de rides**
  - Décision: entrée unique OU tickets par attraction
  - Revenue stream régulier
  - Impact sur satisfaction si trop cher

- [ ] **Besoins des visiteurs (faim, soif, toilettes)**
  - Système de needs avec dégradation temporelle
  - Nouveaux bâtiments: toilettes, restaurants
  - Pénalités de satisfaction si besoins non satisfaits

- [ ] **Système de pause/vitesse**
  - Pause, vitesse x1, x2, x3
  - Gestion plus facile aux moments critiques

- [ ] **Sauvegarde/chargement**
  - Sérialisation JSON de l'état du parc
  - Load/Save depuis le menu

#### 🚀 **Priorité MOYENNE (Améliorations majeures)**

- [ ] **Système de missions/objectifs**
  - Mode Sandbox vs Campagne
  - Objectifs: X visiteurs, Y$ revenus, Z% satisfaction
  - Progression et déblocage de contenu

- [ ] **Système météo**
  - Pluie/soleil affectant la fréquentation
  - Impact sur préférences rides (indoor vs outdoor)
  - Variations de revenus dynamiques

- [ ] **Restaurants et stands de nourriture**
  - Différents types: fast-food, restaurant, stands
  - Satisfont la faim et génèrent revenus
  - Différents des shops actuels

#### 🎨 **Priorité BASSE (Polish)**

- [ ] **Décoration et ambiance**
  - Arbres, fleurs, bancs, lampes
  - Zones thématiques
  - Impact sur satisfaction générale

- [ ] **Amélioration UI/UX**
  - Sélection d'entités pour voir stats détaillées
  - Graphiques de revenus/satisfaction dans le temps
  - Système d'alertes (ride cassé, visiteur mécontent)
  - Tooltips et tutoriel

---

## 🚀 Installation et Lancement

### Prérequis
- Python 3.8 ou supérieur
- Pygame

### Installation

```bash
# Cloner le repository
git clone https://github.com/Enicay/openpark.git
cd openpark

# Installer les dépendances
pip install -r requirements.txt

# Lancer le jeu
python run.py
```

---

## 🎮 Contrôles

### Caméra
- **WASD / Flèches** - Déplacer la caméra
- **Middle-click + Drag** - Pan
- **+/-** - Zoom in/out

### Construction
- **Left-click** - Placer un objet
- **Left-click + Drag** - Tracer des chemins en continu
- **Right-click** - Annuler le placement

### Interface
- **Toolbar (bas d'écran)** - Sélectionner chemins, rides, shops, employés, outils
- **Debug Menu** - Toggle logs, ajuster projection oblique

---

## 🏗️ Architecture technique

### Composants principaux

```
openpark/
├── themepark_engine/
│   ├── engine.py           # Boucle principale du jeu
│   ├── agents.py           # IA des visiteurs (state machine)
│   ├── rides.py            # Système d'attractions
│   ├── shops.py            # Boutiques
│   ├── employees.py        # 4 types d'employés
│   ├── queues.py           # Files d'attente (linéaires)
│   ├── serpent_queue.py    # Files serpentines
│   ├── litter.py           # Système de déchets
│   ├── economy.py          # Gestion financière
│   ├── map.py              # Grille de tuiles
│   ├── renderers/
│   │   └── iso.py          # Projection oblique
│   └── data/
│       └── objects.json    # Définitions des objets du jeu
├── run.py                  # Point d'entrée
└── requirements.txt
```

### Système de projection oblique

OpenPark utilise une **projection oblique** (pas isométrique!) inspirée de Theme Park (1994):
- **Axe X**: Horizontal à l'écran
- **Axe Y**: Skewed par angle de tilt φ (défaut: 10°)
- **Formules de transformation**:
  ```python
  screen_x = (grid_x + grid_y * tan(φ)) * tile_width - camera_x
  screen_y = grid_y * tile_height - camera_y
  ```

Configuration via debug menu: tile_width, tile_height, angle φ

---

## 🤝 Contribution

**⚠️ Le projet n'est pas encore ouvert aux contributions externes.**

Nous finalisons les features core (voir Roadmap ci-dessus) avant d'ouvrir le projet à la communauté.

### 🤖 Contribution en "Vibe Coding"

**Tous les contributeurs sont les bienvenus**, qu'ils codent manuellement ou utilisent des IA!

**Le challenge**: Maintenir ce projet comme un exemple de **"full vibe coding"** - tout le code peut être généré et modifié via conversation avec des assistants IA (Claude, GPT, etc.).

#### Comment contribuer en vibe coding:
1. **Utilisez votre IA préférée** (Claude Code, Cursor, GitHub Copilot, ChatGPT, etc.)
2. **Conversez avec l'IA** pour implémenter des features de la roadmap
3. **Partagez vos prompts** - documentez comment vous avez guidé l'IA
4. **Testez et itérez** - l'IA peut aussi débugger!

#### Pourquoi c'est intéressant:
- 🚀 **Vitrine technologique**: Démonstration des capacités des IA en développement de jeux
- 📚 **Documentation IA-friendly**: Code et architecture pensés pour être compris par les IA
- 🧠 **Apprentissage**: Voir comment différentes IA abordent les mêmes problèmes
- ⚡ **Rapidité**: Les features peuvent être implémentées en quelques heures au lieu de jours

### Vous voulez contribuer plus tard?
- ⭐ **Star le repo** pour suivre les mises à jour
- 👀 **Watch** pour être notifié de l'ouverture aux contributions
- 💡 Créez une **Issue** pour proposer des idées ou partager vos expériences de vibe coding

Une fois ouvert, nous fournirons:
- Guidelines de contribution détaillées (humain ET IA)
- Architecture et coding standards
- Labels pour "good first issue" et "good for AI"
- Exemples de prompts efficaces pour les features courantes

---

## 📝 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Crédits

- **Inspiration**: Theme Park (Bullfrog Productions, 1994)
- **Développement**: Projet open source communautaire en "vibe coding"
- **Assistants IA**: Claude Sonnet 4.5 (Anthropic) & GPT-5 (OpenAI)
- **Engine**: Python + Pygame
- **Méthodologie**: Full AI-assisted development

### 🤖 IA Contributors
Ce projet démontre la puissance de la collaboration humain-IA:
- **Claude Sonnet 4.5**: Architecture système, implémentation des features core, debugging
- **GPT-5**: Optimisations, suggestions de design, documentation

Tous les contributeurs futurs (humains ou IA) seront crédités dans cette section!

---

## ❓ FAQ - Vibe Coding

### Qu'est-ce que le "vibe coding"?
Le vibe coding est une approche de développement où vous **conversez avec une IA** pour créer du code plutôt que de l'écrire manuellement. Vous décrivez ce que vous voulez, l'IA génère le code, vous testez, itérez, et débugguez en continuant la conversation.

### Pourquoi faire un projet entier en vibe coding?
- 🧪 **Expérimentation**: Tester les limites des IA modernes sur un projet complexe
- 📚 **Apprentissage**: Voir comment structurer un projet pour qu'il soit "IA-friendly"
- 🚀 **Rapidité**: Features complexes implémentées en heures au lieu de jours/semaines
- 🌍 **Accessibilité**: Permet à des non-programmeurs de contribuer à des projets techniques

### Les IA ont vraiment TOUT fait?
Oui! De l'architecture initiale aux bugs complexes, tout a été implémenté via conversation. Le rôle humain:
- Définir la vision et les features
- Tester le jeu et identifier les bugs
- Guider l'IA avec des prompts clairs
- Valider que le code correspond aux attentes

### Quel outil utiliser pour contribuer?
N'importe quel assistant IA capable de coder:
- **Claude Code** (terminal-based, excellent pour ce projet)
- **Cursor** (IDE avec IA intégrée)
- **GitHub Copilot** (extension VS Code)
- **ChatGPT** (mode code avec copy/paste)
- **Windsurf**, **Aider**, etc.

### Comment documenter mes contributions vibe coding?
Partagez dans votre PR:
1. L'IA utilisée (Claude/GPT/etc.)
2. Un résumé des prompts clés
3. Les difficultés rencontrées et comment vous les avez résolues
4. Le nombre d'itérations nécessaires

---

## 📧 Contact

Pour questions ou suggestions: [Créer une Issue](https://github.com/Enicay/openpark/issues)

---

**Fait avec ❤️ par la communauté open source (humaine ET IA)**

*OpenPark est un projet fan-made non affilié à Bullfrog Productions ou Electronic Arts.*
