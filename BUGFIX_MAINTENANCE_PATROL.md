# Correction du bug : Agents de maintenance immobiles

## Date: 2025-10-13

## 🐛 Symptômes observés

1. **Premier agent de maintenance bouge initialement puis s'arrête**
2. **Les autres agents ne bougent jamais**
3. **Tous les agents restent bloqués en état "idle"**

---

## 🔍 Analyse du problème

### Problème #1 : Timer reset prématuré

**Fichier:** `themepark_engine/employees.py` (ligne 377-383)

**Code problématique:**
```python
if self.state == "idle":
    self.patrol_timer += dt
    if self.patrol_timer >= self.patrol_duration:
        self.patrol_timer = 0.0  # ❌ RESET SANS ACTION
        # Will be assigned work by engine...
```

**Problème:**
- Le timer était incrémenté dans `tick()`
- Quand il atteignait 3 secondes, il était remis à 0
- Mais **AUCUNE action n'était lancée** à ce moment
- L'engine vérifie le timer dans `update()`, mais il est déjà à 0 !

**Résultat:** Le worker reste bloqué en idle, le timer oscille entre 0 et 3 sans jamais déclencher d'action.

---

### Problème #2 : Échec de patrouille silencieux

**Fichier:** `themepark_engine/engine.py` (ligne 1150-1154)

**Code problématique:**
```python
else:
    # No litter found, check if patrol timer expired
    if worker.patrol_timer >= worker.patrol_duration:
        # Start patrol
        worker.start_patrol(self.grid)  # ❌ PAS DE VÉRIFICATION DU SUCCÈS
```

**Problème:**
- `start_patrol()` retourne `True` si succès, `False` si échec
- Le code ne vérifie pas la valeur de retour
- Si la patrouille échoue (pas de chemin trouvé), le worker reste bloqué en idle
- Le timer n'est pas réinitialisé, donc il ne réessaiera jamais

**Résultat:** Si un worker ne trouve pas de chemin pour patrouiller, il reste bloqué définitivement.

---

### Problème #3 : Compétition pour les ressources

**Fichier:** `themepark_engine/engine.py` (ligne 1147-1149)

**Code problématique:**
```python
if not already_targeted:
    worker.start_cleaning(nearest_litter, self.grid)
# ❌ Si le litter est déjà ciblé, on ne fait RIEN
```

**Problème:**
- Si le seul litter disponible est déjà ciblé par un autre worker
- Le worker actuel ne fait rien
- Il reste en idle même si son timer a expiré

**Résultat:** Les workers idle ne patrouillent pas s'il y a du litter mais qu'il est déjà assigné.

---

## ✅ Solutions appliquées

### Solution #1 : Ne pas reset le timer dans tick()

**Fichier:** `themepark_engine/employees.py`

**Avant:**
```python
if self.state == "idle":
    self.patrol_timer += dt
    if self.patrol_timer >= self.patrol_duration:
        self.patrol_timer = 0.0  # ❌
        # Will be assigned work by engine...
```

**Après:**
```python
if self.state == "idle":
    self.patrol_timer += dt
    # Note: Do NOT reset patrol_timer here, it will be reset by engine
    # when work is assigned or patrol starts
```

**Explication:**
- Le timer continue d'augmenter
- L'engine peut détecter quand il dépasse `patrol_duration`
- Le timer est réinitialisé **uniquement** quand une action démarre

---

### Solution #2 : Reset du timer dans start_*() methods

**Fichier:** `themepark_engine/employees.py`

**Ajouté dans:**
- `start_cleaning()` : `self.patrol_timer = 0.0`
- `start_gardening()` : `self.patrol_timer = 0.0`
- `start_patrol()` : `self.patrol_timer = 0.0`

**Explication:**
- Chaque fois qu'une action démarre, le timer est remis à 0
- Garantit que le worker attend 3 secondes après l'action avant la prochaine

---

### Solution #3 : Vérification du succès de patrol

**Fichier:** `themepark_engine/engine.py`

**Avant:**
```python
else:
    if worker.patrol_timer >= worker.patrol_duration:
        worker.start_patrol(self.grid)
```

**Après:**
```python
elif should_patrol:
    success = worker.start_patrol(self.grid)
    if success:
        DebugConfig.log('engine', f"Maintenance worker {worker.id} started patrol (no litter found)")
    else:
        # Patrol failed, reset timer to try again soon
        worker.patrol_timer = worker.patrol_duration - 1.0
```

**Explication:**
- Vérifie si `start_patrol()` a réussi
- Si échec, reset le timer à `patrol_duration - 1.0` (2 secondes)
- Le worker réessaiera après 1 seconde au lieu de rester bloqué

---

### Solution #4 : Patrouille en cas de litter déjà ciblé

**Fichier:** `themepark_engine/engine.py`

**Avant:**
```python
if nearest_litter:
    if not already_targeted:
        worker.start_cleaning(nearest_litter, self.grid)
# Rien si already_targeted = True
```

**Après:**
```python
if nearest_litter:
    if not already_targeted:
        worker.start_cleaning(nearest_litter, self.grid)
    elif should_patrol:
        # Litter already targeted by someone else, start patrol instead
        success = worker.start_patrol(self.grid)
        if success:
            DebugConfig.log('engine', f"Maintenance worker {worker.id} started patrol (no available litter)")
```

**Explication:**
- Si le litter est déjà ciblé ET le timer a expiré
- Lance une patrouille plutôt que de rester idle
- Évite d'avoir plusieurs workers inactifs qui attendent le même litter

---

### Solution #5 : Même logique pour grass workers

**Fichier:** `themepark_engine/engine.py`

**Ajouté dans `_assign_maintenance_workers_to_gardening()`:**
```python
if not found_spot:
    success = worker.start_patrol(self.grid)
    if success:
        DebugConfig.log('engine', f"Grass maintenance worker {worker.id} started patrol (no garden spot found)")
    else:
        # Patrol failed, reset timer to try again soon
        worker.patrol_timer = worker.patrol_duration - 1.0
        DebugConfig.log('engine', f"Grass maintenance worker {worker.id} failed to start patrol, will retry")
```

**Explication:**
- Même logique que pour les path workers
- Gère l'échec de patrouille gracieusement

---

## 🎯 Flux corrigé

### Path Worker (sur chemin) :

```
IDLE (timer += dt)
  │
  ├─ Timer < 3s → Reste IDLE
  │
  └─ Timer >= 3s → Engine check:
      │
      ├─ Litter trouvé et disponible → CLEANING (timer = 0)
      │
      ├─ Litter trouvé mais ciblé → PATROLLING (timer = 0)
      │
      └─ Pas de litter → PATROLLING (timer = 0)
           │
           ├─ Succès → PATROLLING
           │
           └─ Échec → IDLE (timer = 2.0, retry dans 1s)
```

### Grass Worker (sur pelouse) :

```
IDLE (timer += dt)
  │
  ├─ Timer < 3s → Reste IDLE
  │
  └─ Timer >= 3s → Engine check:
      │
      ├─ Spot de grass trouvé → GARDENING (timer = 0)
      │
      └─ Pas de spot → PATROLLING (timer = 0)
           │
           ├─ Succès → PATROLLING
           │
           └─ Échec → IDLE (timer = 2.0, retry dans 1s)
```

---

## 🧪 Tests effectués

### Test 1 : Worker isolé sans litter
- ✅ Worker patrouille après 3 secondes
- ✅ Retourne en idle après patrouille
- ✅ Recommence après 3 secondes

### Test 2 : Plusieurs workers avec un seul litter
- ✅ Premier worker va nettoyer
- ✅ Deuxième worker patrouille (litter déjà ciblé)
- ✅ Troisième worker patrouille aussi

### Test 3 : Worker sur grass
- ✅ Worker cherche un spot de grass
- ✅ Va jardiner si trouvé
- ✅ Patrouille si pas de spot

### Test 4 : Échec de pathfinding
- ✅ Worker réessaie après 1 seconde
- ✅ Ne reste pas bloqué indéfiniment

---

## 📝 Fichiers modifiés

1. **`themepark_engine/employees.py`**
   - Supprimé le reset de timer dans `tick()`
   - Ajouté reset de timer dans `start_cleaning()`, `start_gardening()`, `start_patrol()`

2. **`themepark_engine/engine.py`**
   - Modifié `_assign_maintenance_workers_to_litter()` pour gérer les échecs
   - Modifié `_assign_maintenance_workers_to_gardening()` pour gérer les échecs
   - Ajouté patrouille de secours quand litter déjà ciblé

---

## ✨ Résultat

**AVANT :** Workers immobiles après la première action (ou jamais en mouvement)

**APRÈS :** Workers actifs en permanence :
- Nettoient les détritus quand disponibles
- Jardinent les spots de grass quand disponibles
- Patrouillent quand pas de travail (toutes les 3 secondes)
- Réessaient automatiquement en cas d'échec de pathfinding

**Statut :** ✅ **BUG CORRIGÉ** - Tous les workers sont maintenant actifs !
