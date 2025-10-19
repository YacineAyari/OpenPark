# Système de Détritus et Poubelles - État d'implémentation

## ✅ Implémenté

### Classes de base (litter.py)
- ✅ `Litter` : classe pour les détritus au sol
- ✅ `Bin` : classe pour les poubelles
- ✅ `BinDef` : définition des types de poubelles
- ✅ `LitterManager` : gestionnaire centralisé
  - add_litter(), remove_litter()
  - add_bin(), remove_bin()
  - find_nearest_bin(radius)
  - get_cleanliness_score()
  - get_litter_in_radius()

### Comportement des visiteurs (agents.py)
- ✅ Nouveaux états : WALKING_TO_BIN, USING_BIN
- ✅ Attributs: has_litter, target_bin, bin_use_timer
- ✅ Méthodes:
  - `get_bin_search_radius()` : calcul dynamique selon distance à l'objectif
  - `should_drop_litter_randomly()` : 80% de chance
  - `_tick_walking_to_bin()` : marche vers la poubelle
  - `_tick_using_bin()` : utilisation de la poubelle (0.5s)
- ✅ Shopping génère du litter : `self.has_litter = True`

### Intégration moteur (engine.py)
- ✅ `LitterManager` initialisé
- ✅ Chargement de `bin_defs` depuis objects.json
- ✅ Mise à jour du litter_manager dans update()
- ✅ Méthode `_handle_guest_litter()` :
  - Cherche poubelle dans le rayon
  - 70% de chance d'aller à la poubelle
  - 80% de chance de jeter si pas de poubelle

### Interface (ui.py)
- ✅ Groupe "Poubelles" ajouté à la toolbar
- ✅ Chargement dynamique des bin_defs

### Configuration (objects.json)
- ✅ Section "bins" ajoutée
- ✅ "bin_standard" défini (coût: 50)

## ⏳ Reste à faire

### 1. Placement des poubelles dans engine.py
```python
# Dans handle_events(), section après le placement d'employés
if self.toolbar.active in self.bin_defs:
    bin_def = self.bin_defs[self.toolbar.active]
    if hover and self.grid.in_bounds(*hover):
        x, y = hover
        # Check if it's a walkable tile
        if self.grid.get(x, y) == TILE_WALK or self.grid.get(x, y) == TILE_GRASS:
            if click_left:
                # Place bin
                bin_obj = self.litter_manager.add_bin(bin_def, x, y)
                if bin_obj:
                    self.economy.cash -= bin_def.cost
                    print(f"Placed {bin_def.name} at ({x}, {y}) for ${bin_def.cost}")
```

### 2. Rendu dans iso.py
```python
# Dans la méthode draw()

# Rendre les détritus
for litter in game.litter_manager.litters:
    sx, sy = self.camera.grid_to_screen(litter.x, litter.y)
    # Petit carré marron pour le détritus
    pygame.draw.circle(screen, (139, 90, 43), (sx, sy), 3)

# Rendre les poubelles
for bin_obj in game.litter_manager.bins:
    sx, sy = self.camera.grid_to_screen(bin_obj.x, bin_obj.y)
    # Rectangle vert pour la poubelle
    pygame.draw.rect(screen, (60, 179, 113), (sx-10, sy-10, 20, 20))
    # Icône
    font_small = pygame.font.SysFont('Arial', 12)
    text = font_small.render('🗑️', True, (255, 255, 255))
    screen.blit(text, (sx-6, sy-8))
```

### 3. Debug overlay (optionnel)
- Afficher score de propreté
- Visualiser rayon de recherche des visiteurs
- Marquer les poubelles pleines

## 🧪 Tests à effectuer

1. **Test basique**:
   - Placer une poubelle sur un chemin
   - Placer un shop (Ice Cream, Soda Stand)
   - Vérifier que les visiteurs achètent
   - Vérifier qu'ils ont `has_litter = True`
   - Vérifier qu'ils cherchent la poubelle

2. **Test de rayon**:
   - Placer poubelle loin (>20 tuiles)
   - Vérifier que visiteur jette par terre
   - Placer poubelle proche (<10 tuiles)
   - Vérifier que visiteur va à la poubelle

3. **Test avec attractions**:
   - Visiteur avec litter + attraction proche
   - Vérifier rayon réduit à 5 tuiles

## 📊 Métriques

### Actuellement
- ✅ 8 visiteurs créés au démarrage
- ✅ Shops fonctionnels
- ✅ Litter généré après shopping
- ✅ Calcul dynamique du rayon

### Paramètres ajustables
```python
# Dans litter.py
LITTER_MAX_PER_TILE = 3

# Dans agents.py
LITTER_DROP_CHANCE = 0.8  # 80%
BIN_GO_CHANCE = 0.7  # 70%
BIN_USE_DURATION = 0.5  # 0.5s

# Rayons de recherche
BASE_RADIUS = 20
CLOSE_ATTRACTION_RADIUS = 5  # < 10 tiles
FAR_ATTRACTION_RADIUS = 10  # >= 20 tiles
```

## 🎯 Prochaines étapes

1. Compléter le placement des poubelles
2. Ajouter le rendu visuel
3. Tester en jeu
4. Ajuster les paramètres (rayons, probabilités)
5. Implémenter agents de maintenance (nettoient les détritus)
6. Implémenter impact sur affluence (cleanliness_score)

---
*Dernière mise à jour: 2025-10-12*
*Statut: 80% complété - Core logic fonctionnel, reste UI*

