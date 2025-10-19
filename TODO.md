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

## Tâches en attente 📋

### Haute priorité

18. **Compléter les systèmes d'employés restants**
    - Difficulté : 3/5
    - Gardien de parc : sécurité et prévention des vols
    - Mascotte : augmentation de l'excitation des visiteurs
    - Système de patrouille pour chaque type

19. **Ajouter plus d'attractions dans objects.json**
    - Difficulté : 2/5
    - Roller coaster
    - Ferris wheel
    - Monorail
    - Haunted house
    - Water rides

20. **Améliorer le système économique**
    - Difficulté : 3/5
    - Budget de départ plus réaliste
    - Équilibrage des coûts et revenus
    - Système de prêts ou faillite
    - Graphiques et statistiques financières

### Priorité moyenne

21. **Améliorer la toolbar**
    - Difficulté : 3/5
    - Interface plus moderne et intuitive
    - Icônes plus claires
    - Meilleure organisation des catégories

22. **Système de bonheur des visiteurs**
    - Difficulté : 4/5
    - Jauge de satisfaction
    - Impact des attractions, shops, propreté
    - Visiteurs mécontents quittent le parc
    - Revenus liés au bonheur

23. **Ajouter un système de sauvegarde/chargement**
    - Difficulté : 3/5
    - Sauvegarde complète du parc (attractions, chemins, shops, employés, visiteurs)
    - Chargement des parcs sauvegardés
    - Gestion de plusieurs sauvegardes

24. **Ajouter des animations pour les attractions**
    - Difficulté : 3/5
    - Animations des attractions en fonctionnement
    - Effets visuels (rotation, mouvement)
    - Indicateurs visuels de l'état (ouvert/fermé/en panne)

### Priorité basse

25. **Optimiser le pathfinding**
    - Difficulté : 4/5
    - Amélioration de l'algorithme A*
    - Gestion des obstacles dynamiques
    - Cache des chemins fréquents

26. **Améliorer l'IA des visiteurs**
    - Difficulté : 5/5
    - Système de groupes (familles, amis)
    - Comportements plus réalistes
    - Préférences avancées (nourriture, souvenirs)
    - Fatigue et besoins (toilettes, repos)

27. **Système météo**
    - Difficulté : 4/5
    - Conditions météorologiques (soleil, pluie, vent)
    - Impact sur les visiteurs (moins de visiteurs sous la pluie)
    - Impact sur les attractions (certaines ferment sous la pluie)

28. **Système de recherche**
    - Difficulté : 5/5
    - Arbre de recherche technologique
    - Déblocage progressif des attractions
    - Coûts de recherche

29. **Mode campagne**
    - Difficulté : 5/5
    - Scénarios prédéfinis avec objectifs
    - Progression et récompenses
    - Niveaux de difficulté

30. **Mode multijoueur**
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
- ✅ Shops fonctionnels
- ✅ Système d'ingénieurs complet avec déplacement fluide
- ✅ Système de pannes d'attractions
- ✅ Système d'agents de maintenance complet (nettoyage + tonte)
- ✅ Système de détritus et poubelles
- ✅ Pathfinding de base
- ✅ Économie de base (cash, coûts, revenus)

### Problèmes connus
- Aucun (système stable)

### Prochaines étapes recommandées
1. Compléter les systèmes d'employés restants (gardien, mascotte)
2. Ajouter plus d'attractions dans `objects.json`
3. Améliorer le système économique (équilibrage)
4. Système de bonheur des visiteurs

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
