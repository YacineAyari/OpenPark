# TODO List - OpenPark Development

## Tâches terminées ✅

### Système de base
1. **Vue oblique par défaut avec Phi à 10°** ✅
   - Mode isométrique supprimé
   - Projection oblique par défaut

2. **Système de placement de chemins en continu** ✅
   - Maintenir le clic pour placer plusieurs tuiles
   - Suivi du curseur de la souris

3. **Système de placement des attractions** ✅
   - Placement des entrées/sorties autour des attractions
   - Preview de placement
   - Vérification des connexions aux chemins

### Système de files d'attente
4. **Système de files d'attente linéaire (Proposition 1)** ✅
   - Files d'attente simples et efficaces
   - Visiteurs se déplacent tuile par tuile
   - Connexion aux entrées d'attractions

5. **Correction du mouvement fluide des visiteurs** ✅
   - Plus de téléportation
   - Déplacement horizontal et vertical sur la grille

6. **Gestion de la capacité des files d'attente** ✅
   - 4 visiteurs par tuile verticale
   - 5 visiteurs par tuile horizontale
   - Visiteurs espacés sur chaque tuile

### Système de debug
7. **Commutateurs de debug par entité** ✅
   - Système centralisé avec `DebugConfig`
   - Commutateurs par catégorie (guests, rides, queues, engine, employees, etc.)
   - Bouton dans le menu debug

8. **Correction du crash lors de l'activation des logs** ✅
   - Suppression des `print()` excessifs
   - Logs optimisés

### Système d'attractions
9. **Capacité normale des attractions restaurée** ✅
   - Utilisation de `self.defn.capacity`
   - Lancement automatique à 50% ou après 5 secondes

10. **Sélection intelligente des attractions** ✅
    - Préférences des visiteurs (thrill, nausea)
    - Système de scoring
    - Facteur aléatoire pour la variété

### Interface utilisateur
11. **Toolbar améliorée** ✅
    - Toolbar en bas de l'écran, au premier plan
    - Groupement par catégorie (shops, attractions, chemins)
    - Sous-menus avec prix affichés

### Système de shops
12. **Implémentation des shops** ✅
    - Placement 2x2, 3x3, 3x5, 5x5
    - Connexion aux chemins
    - Visiteurs attirés par les shops
    - Indicateurs visuels de connexion

### Système d'employés
13. **Implémentation des ingénieurs** ✅
    - Placement libre sur n'importe quelle tuile
    - Déplacement vers les attractions en panne
    - Réparation des attractions
    - Déplacement fluide sans téléportation (vers l'attraction ET vers la position proche après réparation)

14. **Système de pannes d'attractions** ✅
    - Pannes aléatoires basées sur `breakdown_chance`
    - Fermeture de la file d'attente lors de la panne
    - Évacuation des visiteurs en file
    - Appel automatique des ingénieurs disponibles

15. **Implémentation des agents de maintenance** ✅
    - Placement sur chemins (nettoyage) ou pelouse (tonte)
    - Nettoyage des détritus sur chemins ET files d'attente
    - Tonte de pelouse en pattern horizontal/vertical continu
    - Gestion intelligente des obstacles et bords de carte
    - Patrouille autonome sans délai
    - Indicateurs visuels pour tous les états (cleaning, mowing, patrolling, etc.)
    - Travail continu 24/7 sans pause

### Système de détritus et propreté
16. **Système de détritus (Litter)** ✅
    - Visiteurs génèrent des détritus après shopping (soda, trash, vomit)
    - Recherche de poubelles dans un rayon dynamique
    - Détritus déposés au sol si pas de poubelle trouvée
    - Types de détritus avec couleurs différentes
    - Positions aléatoires sur les tuiles

17. **Système de poubelles (Bins)** ✅
    - Placement sur pelouse adjacente aux chemins
    - Capacité de stockage
    - Intégration avec le système économique
    - Sprite visuel
    - Coloration verte sur la grille

### Système de temps et vitesse
18. **Système de temps du jeu** ✅
    - 1 jour in-game = 12 minutes réelles (configurable)
    - Affichage Day X HH:MM
    - Ouverture/fermeture du parc avec touche 'O'
    - Visiteurs restent maximum 10 jours in-game
    - Évacuation automatique à la fermeture

19. **Système de vitesse du jeu** ✅
    - Pause (Space) : game_speed = 0
    - Normal (1) : game_speed = 1.0
    - Rapide (2) : game_speed = 2.0
    - Très rapide (3) : game_speed = 3.0
    - Affectation correcte aux visiteurs, employés, attractions

### Système de besoins des visiteurs
20. **Système de besoins (Hunger/Thirst/Bladder)** ✅
    - Hunger : décroît à -0.00333/s (0.0 = affamé, 1.0 = rassasié)
    - Thirst : décroît à -0.005/s (plus rapide)
    - Bladder : augmente à +0.00267/s (0.0 = vide, 1.0 = urgent)
    - Pénalités de satisfaction si besoins non satisfaits
    - Affichage dans le HUD avec codes couleur

21. **Système de priorité des besoins** ✅
    - Priorité 1 : Bladder > 70% → Cherche toilettes
    - Priorité 2 : Thirst < 30% → Cherche boisson
    - Priorité 3 : Hunger < 30% → Cherche nourriture
    - Pathfinding intelligent vers installations

22. **Implémentation des toilettes (Restrooms)** ✅
    - 4 tailles : Small (1x1, 2), Medium (2x1, 4), Large (2x2, 6), XL (3x2, 8)
    - Placement adjacent aux chemins (comme bins)
    - Gestion de la capacité
    - Système d'occupation/libération
    - Coloration violette sur la grille
    - Prévisualisation correcte de la taille

23. **Types de shops par catégorie** ✅
    - shop_type : "food", "drink", "souvenir"
    - Pathfinding vers shops spécifiques selon besoin
    - Revenus générés par nourriture et boissons
    - Déduction du budget visiteur

24. **Prix d'entrée du parc** ✅
    - Prix d'entrée configurable (défaut $50)
    - Budget visiteurs : $75-$300
    - Refus d'entrée si budget insuffisant
    - UI panel avec slider pour ajuster le prix
    - Taux de spawn progressif selon le prix
    - Stats dans HUD : revenue et refusés

### Système d'entrée du parc
25. **Entrée fixe au sud** ✅
    - Entrée du parc positionnée au sud (centre)
    - Spawn des visiteurs à l'entrée
    - Sortie des visiteurs par la même entrée
    - Caméra centrée sur l'entrée à 70% de hauteur
    - Tuile spéciale TILE_PARK_ENTRANCE colorée en doré

### Améliorations visuelles
26. **Coloration des tuiles sur la grille** ✅
    - Rides : Bleu (100, 100, 200)
    - Shops : Marron (200, 150, 100)
    - Restrooms : Violet/Lavande (180, 130, 200)
    - Bins : Vert (100, 200, 100)
    - Identification visuelle claire de tous les bâtiments

## Tâches en attente 📋

### Haute priorité

27. **Compléter les systèmes d'employés restants**
    - Difficulté : 3/5
    - Gardien de parc : sécurité et prévention des vols (déjà implémenté)
    - Mascotte : augmentation de l'excitation des visiteurs (déjà implémenté)
    - Note : Les 4 types d'employés sont maintenant opérationnels

28. **Ajouter plus d'attractions dans objects.json**
    - Difficulté : 2/5
    - Roller coaster
    - Ferris wheel
    - Monorail
    - Haunted house
    - Water rides

29. **Améliorer le système économique**
    - Difficulté : 3/5
    - Budget de départ plus réaliste
    - Équilibrage des coûts et revenus
    - Système de prêts ou faillite
    - Graphiques et statistiques financières

### Priorité moyenne

30. **Améliorer la toolbar**
    - Difficulté : 3/5
    - Interface plus moderne et intuitive
    - Icônes plus claires
    - Meilleure organisation des catégories

31. **Système de sauvegarde/chargement**
    - Difficulté : 3/5
    - Sauvegarde complète du parc (attractions, chemins, shops, employés, visiteurs)
    - Chargement des parcs sauvegardés
    - Gestion de plusieurs sauvegardes

32. **Ajouter des animations pour les attractions**
    - Difficulté : 3/5
    - Animations des attractions en fonctionnement
    - Effets visuels (rotation, mouvement)
    - Indicateurs visuels de l'état (ouvert/fermé/en panne)

### Priorité basse

33. **Optimiser le pathfinding**
    - Difficulté : 4/5
    - Amélioration de l'algorithme A*
    - Gestion des obstacles dynamiques
    - Cache des chemins fréquents

34. **Améliorer l'IA des visiteurs**
    - Difficulté : 5/5
    - Système de groupes (familles, amis)
    - Comportements plus réalistes avancés
    - Note : Système de besoins (faim/soif/toilettes) déjà implémenté ✅

35. **Système météo**
    - Difficulté : 4/5
    - Conditions météorologiques (soleil, pluie, vent)
    - Impact sur les visiteurs (moins de visiteurs sous la pluie)
    - Impact sur les attractions (certaines ferment sous la pluie)

36. **Système de recherche**
    - Difficulté : 5/5
    - Arbre de recherche technologique
    - Déblocage progressif des attractions
    - Coûts de recherche

37. **Mode campagne**
    - Difficulté : 5/5
    - Scénarios prédéfinis avec objectifs
    - Progression et récompenses
    - Niveaux de difficulté

38. **Mode multijoueur**
    - Difficulté : 5/5
    - Architecture réseau
    - Synchronisation du state
    - Gestion des conflits

## État actuel du système

### Fonctionnalités opérationnelles
- ✅ Vue oblique avec angle Phi de 10°
- ✅ Système de debug stable et fonctionnel
- ✅ Placement de chemins en continu
- ✅ Système de files d'attente linéaire
- ✅ Capacité normale des attractions
- ✅ Lancement automatique des attractions
- ✅ Sélection intelligente des attractions
- ✅ Mouvement fluide des visiteurs
- ✅ Toolbar groupée et sous-menus
- ✅ Shops fonctionnels avec types (food/drink/souvenir)
- ✅ Système d'ingénieurs complet avec déplacement fluide
- ✅ Système de pannes d'attractions
- ✅ Système d'agents de maintenance complet (nettoyage + tonte)
- ✅ Système de gardiens de parc (sécurité, patrouille)
- ✅ Système de mascottes (boost d'excitation)
- ✅ Système de détritus et poubelles
- ✅ Système de besoins visiteurs (hunger/thirst/bladder)
- ✅ Système de toilettes (4 tailles, gestion capacité)
- ✅ Système de temps du jeu (jour/heure, ouverture/fermeture)
- ✅ Système de vitesse du jeu (pause, x1, x2, x3)
- ✅ Prix d'entrée du parc configurable
- ✅ Budget visiteurs et refus d'entrée
- ✅ Entrée fixe au sud avec spawn/exit
- ✅ Coloration visuelle des tuiles (rides/shops/restrooms/bins)
- ✅ Pathfinding de base
- ✅ Économie de base (cash, coûts, revenus, salaires)

### Problèmes connus
- Aucun (système stable)

### Prochaines étapes recommandées
1. Ajouter plus d'attractions dans `objects.json` (variété)
2. Améliorer le système économique (équilibrage, graphiques)
3. Système de sauvegarde/chargement
4. Animations des attractions

### Architecture technique

#### Fichiers principaux
- `themepark_engine/engine.py` : Boucle de jeu principale, événements, rendu
- `themepark_engine/agents.py` : Logique des visiteurs (Guest)
- `themepark_engine/rides.py` : Définition et comportement des attractions
- `themepark_engine/shops.py` : Définition et comportement des shops
- `themepark_engine/employees.py` : Définition et comportement des employés
- `themepark_engine/queues.py` : Système de files d'attente
- `themepark_engine/map.py` : Grille et types de tuiles
- `themepark_engine/pathfinding.py` : Algorithme A*
- `themepark_engine/ui.py` : Interface utilisateur (Toolbar)
- `themepark_engine/debug.py` : Système de debug centralisé
- `themepark_engine/data/objects.json` : Définitions des objets du jeu

#### Points techniques importants
- Projection oblique : 64x36 par défaut
- Pathfinding : A* avec variante pour ingénieurs (peuvent marcher partout)
- Files d'attente : système linéaire avec capacité par tuile
- Employés : système de states (idle, moving, working)
- Debug : logs catégorisés activables/désactivables par entité

---
*Dernière mise à jour : 2025-10-13*
*Statut : En développement actif*
*Version : 0.3.1-alpha*
