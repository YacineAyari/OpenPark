# Système d'inventaire - OpenPark

## Vue d'ensemble

Le système d'inventaire gère les stocks de produits vendus dans les shops du parc. Chaque produit a un stock global partagé entre tous les shops du même type.

## Produits disponibles

| Produit | Coût de base | Shops utilisant ce produit |
|---------|--------------|----------------------------|
| Sodas | $0.50 | Soda Stand |
| Frites | $0.80 | Fries Stand |
| Burgers | $2.00 | Restaurant |
| Hotdogs | $1.20 | Hotdog Stand |
| Glaces | $1.00 | Ice Cream, Candy Stand |
| Souvenirs | $1.50 | Gift Shop |
| Pizzas | $1.80 | Pizza Stand |

## Système de commande

### Réductions par palier de quantité

| Quantité | Réduction | Délai de livraison |
|----------|-----------|-------------------|
| 1-50 unités | 0% | 1-3 jours |
| 51-100 unités | -10% | 4-7 jours |
| 101-200 unités | -15% | 8-14 jours |
| 201-500 unités | -20% | 15-21 jours |
| 501+ unités | -25% | **22-30 jours** |

**Conseil** : Commandez en gros pour économiser jusqu'à 25%, mais attention au délai de livraison !

## Inflation

- **Taux d'inflation annuel** : +1% à +3% (aléatoire)
- **Application** : Chaque janvier (1er du mois)
- **Effet** : Augmente tous les coûts d'achat des produits
- **Cumulative** : L'inflation s'accumule année après année

**Exemple** :
- Année 2025 : Sodas à $0.50
- Année 2026 (+2% inflation) : Sodas à $0.51
- Année 2027 (+3% inflation) : Sodas à $0.53

## Interface utilisateur

### Ouvrir la modal d'inventaire

Appuyez sur **[I]** à tout moment pendant le jeu.

### Onglets

#### 1. Stock ([1])
- Liste tous les produits avec leur stock actuel
- Indicateurs visuels :
  - ✓ (vert) : Stock suffisant (≥50 unités)
  - ⚠ (orange) : Stock bas (<50 unités)
  - ⚠️ (rouge) : Rupture de stock (0 unités)
- Affiche le coût par unité (avec inflation)
- Bouton "Order" pour commander

#### 2. Orders ([2])
- Liste des commandes en cours de livraison
- Barre de progression visuelle
- Statut :
  - 🚚 En transit : "X/Y jours restants"
  - ✓ Livré : Quand `days_remaining = 0`

### Passer une commande

⚠️ **Important** : Vous devez d'abord placer au moins un shop correspondant au produit dans votre parc avant de pouvoir commander.

1. Dans l'onglet Stock, cliquez sur **"Order"** à côté d'un produit (le bouton n'apparaît que si vous avez placé un shop utilisant ce produit)
2. Un formulaire s'ouvre avec :
   - **Quantité** : **Utilisez le slider horizontal** (10 à 1000 unités) - cliquez et glissez avec la souris
   - **Coût total** : Calculé automatiquement avec réduction affichée
   - **Délai de livraison** : Nombre de jours estimé (varie selon la quantité)
   - **Cash disponible** : Vérifie si vous pouvez payer
3. Cliquez sur **"Confirm"** pour valider (si vous avez assez d'argent)
4. Cliquez sur **"Cancel"** ou [ESC] pour annuler

## Gameplay

### Restriction de commande

**Règle importante** : Vous ne pouvez commander un produit que si vous avez **au moins un shop** qui l'utilise dans votre parc.

- Les produits sans shop apparaissent **grisés** dans l'onglet Stock
- Le bouton "Order" est remplacé par "No shop" pour ces produits
- Placez d'abord le shop correspondant, puis commandez le stock

### Ventes et consommation de stock

- Chaque vente dans un shop consomme **1 unité** du produit correspondant
- Si le stock est à **0**, le shop ne peut plus vendre
- Les guests qui arrivent à un shop vide perdent **-10 satisfaction**

### Logs de debug

Activez les logs pour suivre les événements d'inventaire :

```python
DebugConfig.ENGINE = True
```

Vous verrez :
- `"Order delivered: 100x Sodas ($50.00)"` : Quand une commande arrive
- `"Guest X finished shopping at Soda Stand, revenue: $2, stock remaining: 99"` : Après chaque vente
- `"Guest X found Soda Stand OUT OF STOCK, satisfaction -10"` : Rupture de stock
- `"Annual inflation applied: 5.2% total"` : En janvier

## Stratégies de gestion

### 1. Anticipation
- Commandez **avant** que le stock soit à 0
- Tenez compte du délai de livraison (jusqu'à 30 jours pour les grosses commandes)

### 2. Optimisation des coûts
- Les grandes commandes (500+) offrent -25% de réduction
- Mais nécessitent plus de cash initial
- Calculez votre rentabilité : `prix_vente - coût_achat - salaires - entretien`

### 3. Diversification
- Ouvrez plusieurs shops du même type pour vendre plus vite
- Tous partagent le même stock global

### 4. Planification saisonnière
- En janvier, les prix augmentent (inflation)
- Commandez en décembre pour profiter des prix plus bas

## Sauvegarde/Chargement

Le système d'inventaire est **entièrement sauvegardé** :
- Stock actuel de chaque produit
- Commandes en cours (avec progression des jours restants)
- Taux d'inflation cumulé

Utilisez **[F5]** pour sauvegarder et **[F9]** pour charger.

## Fichiers du système

- `themepark_engine/inventory.py` : Gestionnaire d'inventaire
- `themepark_engine/ui_parts/inventory_modal.py` : Interface utilisateur
- `themepark_engine/data/objects.json` : Définitions des produits (section `products`)

## Architecture technique

### Classes principales

#### `ProductDef`
Définit un produit avec :
- `id` : Identifiant unique
- `name` : Nom affiché
- `base_cost` : Coût de base (avant inflation)
- `category` : "food", "drink", ou "souvenir"
- `used_by_shops` : Liste des shop IDs utilisant ce produit

#### `PendingOrder`
Représente une commande en cours :
- `product_id` : Produit commandé
- `quantity` : Quantité
- `total_cost` : Coût total payé
- `delivery_days` : Durée totale de livraison
- `days_remaining` : Jours restants (tick chaque jour)

#### `InventoryManager`
Gère tout le système :
- `products` : Dict des définitions de produits
- `stock` : Dict {product_id: quantity}
- `pending_orders` : Liste des commandes en cours
- `inflation_rate` : Taux d'inflation cumulé (1.0 = 100%)

### Méthodes clés

```python
# Vérifier le stock
has_stock = inventory_manager.has_stock(product_id)

# Consommer du stock (lors d'une vente)
success = inventory_manager.consume_stock(product_id, quantity=1)

# Commander un produit
order = inventory_manager.place_order(product_id, quantity, year, month, day)

# Avancer d'un jour (appelé automatiquement)
delivered_orders = inventory_manager.tick_day()

# Appliquer l'inflation annuelle (janvier)
inventory_manager.apply_annual_inflation(year)
```

## Intégration dans le moteur

Le système est intégré dans `engine.py` :

1. **Initialisation** (ligne 56-57) : Chargement des produits depuis JSON
2. **Tick journalier** (ligne 1220-1222) : Avance les commandes en cours
3. **Inflation annuelle** (ligne 1225-1227) : Applique l'inflation en janvier
4. **Consommation de stock** (lignes 1278-1339) : Lors des ventes (shopping/eating/drinking)
5. **Interface** (ligne 2709-2711) : Affichage de la modal

## Prochaines améliorations possibles

- [ ] Indicateur visuel sur les shops quand stock bas/vide
- [ ] Notification push quand une commande est livrée
- [ ] Historique des commandes passées
- [ ] Prévision de consommation basée sur le nombre de guests
- [ ] Événements aléatoires (retards de livraison, bonus de réduction)
- [ ] Fournisseurs multiples avec prix différents
- [ ] Système de contrats à long terme
