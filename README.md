# OpenPark 🎢

**Clone open source du célèbre jeu Theme Park (Bullfrog Productions, 1994)**

OpenPark est une simulation de parc d'attractions en **projection oblique**, développée en Python avec Pygame. Gérez votre parc, construisez des attractions, employez du personnel, et gardez vos visiteurs heureux!

![Version](https://img.shields.io/badge/version-0.4.0--alpha-orange)
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
- ✅ **Système de besoins des visiteurs** (hunger/thirst/bladder, IA prioritaire, toilettes multi-tailles)
- ✅ **Système de temps et vitesse** (temps in-game, pause/x1/x2/x3, ouverture/fermeture parc)
- ✅ **Système de satisfaction dynamique** (15+ facteurs influençant le comportement des visiteurs)
- ✅ **Queue System V2** (placement links, flèches directionnelles, retry intelligent)
- ✅ **6 attractions variées** (Carousel, Bumper, Ferris Wheel, Train, Pirate Ship, Circus)
- ✅ **Gestion du litter** (state machine visiteurs, assignation automatique d'employés)
- ✅ **Projection oblique configurable** (math oblique, picking inverse, debug controls)
- ✅ **UI temps réel** (stats colorées, indicateurs visuels, feedback instantané, coloration tuiles)
- ✅ **Système de sprites OpenMoji** (emojis haute qualité, 30+ sprites, diversité visuelle)
- ✅ **Zoom avec molette** (centré sur curseur, limites intelligentes, sprites adaptatifs)
- ✅ **Système de sauvegarde/chargement** (sauvegardes complètes, restauration des états)

**Résultat**: Un moteur de jeu complet et fonctionnel développé entièrement via conversation avec IA! 🚀

---

## 📸 Screenshots

![OpenPark Gameplay](themepark_engine/assets/screenshots/Screenshot%20From%202025-10-21%2010-36-09.png)

*Vue d'ensemble d'OpenPark avec HUD iconographique, toolbar redesignée, attractions, chemins et visiteurs*

**Fonctionnalités visibles:**
- 🎨 HUD horizontal avec icônes OpenMoji 32x32px et tooltips
- 🎯 Toolbar icon-only avec 7 catégories (Chemins, Attractions, Boutiques, Employés, Installations, Économie, Outils)
- 🎡 Projection oblique configurable avec rendu isométrique
- 👥 Visiteurs avec indicateurs de satisfaction colorés
- 📊 Statistiques en temps réel (argent, visiteurs, besoins, employés, litter)
- 🚪 Système modal de sauvegarde/chargement

---

## 🎮 Caractéristiques

### ✅ Déjà implémenté

#### 🏗️ **Système de construction**
- **Chemins piétonniers** - Réseau de paths pour la circulation des visiteurs
- **6 Attractions variées** (Rides) - Carousel, Bumper Cars, Ferris Wheel, Park Train, Pirate Ship, Circus Show
  - Capacités: 12 à 30 visiteurs
  - Durées variées: 7 à 15 secondes
  - Thrill/Nausea: 0.1 à 0.7 (préférences visiteurs)
- **Boutiques** (Shops) - 7 types (soda, ice cream, hotdog, fries, restaurant, gift shop)
- **Toilettes** (Restrooms) - 4 tailles (1x1, 2x1, 2x2, 3x2), capacité 2 à 8 visiteurs
- **Poubelles** - Gestion de la propreté du parc
- **Queue System V2** - Placement links, flèches directionnelles N/S/E/W, retry intelligent

#### 👥 **Intelligence Artificielle des visiteurs**
- **State machine complète** - 11+ états différents (wandering, queuing, riding, shopping, eating, drinking, using_restroom, etc.)
- **Préférences personnalisées** - Tolérance au thrill et à la nausée
- **Système de satisfaction dynamique** - Happiness, Excitement, Satisfaction
  - Dégradation naturelle au fil du temps
  - Bonus: rides, shopping, propreté, queues courtes
  - Pénalités: attente, litter, pannes, queues longues
- **Système de besoins (Needs)** - Hunger, Thirst, Bladder
  - Hunger: Décroît à -0.00333/s (satisfaction si > 0.3)
  - Thirst: Décroît à -0.005/s (plus rapide que hunger)
  - Bladder: Augmente à +0.00267/s (urgent si > 0.7)
  - **IA prioritaire**: Bladder > 70% → Toilettes / Thirst < 30% → Boissons / Hunger < 30% → Nourriture
  - Pénalités de satisfaction si besoins non satisfaits
- **Gestion du litter** - Les visiteurs cherchent des poubelles ou jettent par terre
- **Budget personnel** - $75-$300 par visiteur, dépenses pour nourriture/boissons

#### 👷 **Système d'employés (4 types)**
- **Engineers** - Réparent les attractions en panne, marchent partout
- **Maintenance Workers** - Nettoient le litter, patrouillent les chemins
- **Security Guards** - Patrouillent et boostent la satisfaction des visiteurs (+5%)
- **Mascots** - Détectent les foules et augmentent l'excitement (+10%)

#### 🎨 **Rendu et Interface**
- **Projection oblique configurable** - Angle φ ajustable, taille de tuiles personnalisable
- **Feedback visuel en temps réel** - Indicateurs colorés de satisfaction (🟢🟡🔴)
- **Coloration des tuiles sur la grille** - Identification visuelle claire:
  - Rides: Bleu (100, 100, 200)
  - Shops: Marron (200, 150, 100)
  - Restrooms: Violet/Lavande (180, 130, 200)
  - Bins: Vert (100, 200, 100)
  - Park Entrance: Doré (255, 215, 0)
- **Panneau de statistiques** - Cash, visiteurs, satisfaction moyenne, employés, litter, temps, prix d'entrée
- **Caméra libre** - Pan (WASD/arrows), zoom (+/-), drag (middle-click)

#### 💰 **Système économique**
- **Prix d'entrée du parc** - Configurable via UI ($50 par défaut), refus si budget insuffisant
- **Revenus** - Prix d'entrée + boutiques + attractions
- **Dépenses** - Coûts de construction, salaires des employés
- **Gestion du cash** - Suivi en temps réel des finances
- **Stats détaillées** - Visiteurs refusés, revenus total, dépenses

#### ⏰ **Système de temps et gestion**
- **Temps in-game** - 1 jour = 12 minutes réelles (configurable)
- **Affichage jour/heure** - Format "Day X HH:MM" en temps réel
- **Ouverture/fermeture du parc** - Touche 'O' pour toggle (démarre fermé)
- **Évacuation automatique** - Visiteurs sortent à la fermeture
- **Durée de visite** - Visiteurs restent max 10 jours in-game
- **Système de vitesse du jeu**:
  - **Pause** (Space) - game_speed = 0, fige tous les entités
  - **Normal** (1) - game_speed = 1.0, vitesse standard
  - **Rapide** (2) - game_speed = 2.0, accéléré x2
  - **Très rapide** (3) - game_speed = 3.0, accéléré x3

#### 🔧 **Gameplay**
- **Pannes d'attractions** - Probabilité de breakdown, évacuation immédiate des queues
- **Assignation automatique** - Les employés trouvent automatiquement du travail
- **Pathfinding A*** - Navigation intelligente pour visiteurs et employés
- **Mouvement fluide** - Interpolation smooth des positions (60 FPS)
- **Retry intelligent** - Visiteurs ne retentent pas immédiatement une queue pleine (30s cooldown)
- **Sauvegarde/Chargement** - Système complet de save/load avec restauration des états

#### 🐛 **Debug & Development**
- **Système de logging catégorisé** - GUESTS, RIDES, EMPLOYEES, ENGINE, etc.
- **Menu debug** - Toggle des logs, réglages de projection
- **Toolbar organisée** - Placement facile par glisser-déposer

---

### 🚧 Roadmap avant contributions externes

#### 🎯 **Priorité HAUTE (Quick Wins)**

- [x] **Queue System V2** ✅
  - Placement links pour suivre l'ordre de construction
  - Flèches directionnelles sur les tiles de queue
  - Retry intelligent pour queues pleines

- [x] **6 Attractions variées** ✅
  - Ferris Wheel, Park Train, Pirate Ship, Circus Show
  - Équilibrage des capacités et durées

- [x] **Sauvegarde/chargement** ✅
  - Sérialisation JSON de l'état du parc
  - Load/Save depuis le menu

- [ ] **Améliorer le système économique**
  - Graphiques de revenus/dépenses au fil du temps
  - Équilibrage des coûts et revenus
  - Alertes pour budget bas
  - Objectifs financiers

- [ ] **Ajouter plus de shops variés**
  - Pizza, burgers, candy, popcorn
  - Boutiques de souvenirs variées
  - Stands de jeux/merchandise

#### 🚀 **Priorité MOYENNE (Améliorations majeures)**

- [ ] **Système de missions/objectifs**
  - Mode Sandbox vs Campagne
  - Objectifs: X visiteurs, Y$ revenus, Z% satisfaction
  - Progression et déblocage de contenu

- [ ] **Système météo**
  - Pluie/soleil affectant la fréquentation
  - Impact sur préférences rides (indoor vs outdoor)
  - Variations de revenus dynamiques

- [ ] **Animations des attractions**
  - Animations pendant le fonctionnement
  - Effets visuels (rotation, mouvement)
  - Indicateurs visuels de l'état (ouvert/fermé/en panne)

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
- **Molette souris** - Zoom in/out (centré sur curseur)
- **+/-** - Zoom in/out

### Construction
- **Left-click** - Placer un objet
- **Left-click + Drag** - Tracer des chemins en continu
- **Right-click** - Annuler le placement

### Gestion du parc
- **O** - Ouvrir/Fermer le parc
- **Space** - Pause
- **1** - Vitesse normale (x1)
- **2** - Vitesse rapide (x2)
- **3** - Vitesse très rapide (x3)

### Interface
- **Toolbar (bas d'écran)** - Sélectionner chemins, rides, shops, employés, outils, toilettes, poubelles
- **Debug Menu** - Toggle logs, ajuster projection oblique
- **Stats HUD** - Affichage temps, cash, visiteurs, prix d'entrée

---

## 🏗️ Architecture technique

### Composants principaux

```
openpark/
├── themepark_engine/
│   ├── engine.py           # Boucle principale du jeu
│   ├── agents.py           # IA des visiteurs (state machine)
│   ├── rides.py            # Système d'attractions
│   ├── shops.py            # Boutiques (food/drink/souvenir)
│   ├── restrooms.py        # Toilettes (4 tailles)
│   ├── employees.py        # 4 types d'employés
│   ├── queues.py           # Files d'attente (linéaires)
│   ├── serpent_queue.py    # Files serpentines
│   ├── litter.py           # Système de déchets et poubelles
│   ├── economy.py          # Gestion financière
│   ├── map.py              # Grille de tuiles
│   ├── pathfinding.py      # Algorithme A*
│   ├── debug.py            # Système de debug centralisé
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
- **Icônes/Sprites**: [OpenMoji](https://openmoji.org/) - Open source emojis sous licence [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
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
