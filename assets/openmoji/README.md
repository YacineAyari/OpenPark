# OpenMoji Graphics for OpenPark

Ce dossier contient les emojis OpenMoji utilisés comme sprites graphiques dans OpenPark.

## À propos d'OpenMoji

**OpenMoji** est un projet open source de la HfG Schwäbisch Gmünd qui fournit des emojis de haute qualité sous licence **CC BY-SA 4.0**.

- Site officiel : https://openmoji.org/
- Repository GitHub : https://github.com/hfg-gmuend/openmoji
- Licence : CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0)

## Structure des dossiers

```
assets/openmoji/
├── rides/          # Attractions (🎢🎡🎠🎪)
├── shops/          # Boutiques et nourriture (🍔🍕🍦🥤🎁)
├── employees/      # Employés (👷🧹💂🎭)
├── guests/         # Visiteurs (🧑)
├── infrastructure/ # Infrastructure (🚻🗑️🚪)
└── decorations/    # Décorations (🌳)
```

## Emojis utilisés

### Attractions (rides/)
- `1F3A0.png` - 🎠 Carousel (Manège)
- `1F3A1.png` - 🎡 Ferris Wheel (Grande roue)
- `1F3A2.png` - 🎢 Roller Coaster (Montagnes russes)
- `1F3AA.png` - 🎪 Circus Tent (Chapiteau de cirque)

### Boutiques (shops/)
- `1F354.png` - 🍔 Hamburger (Restaurant)
- `1F355.png` - 🍕 Pizza
- `1F366.png` - 🍦 Ice Cream (Glace)
- `1F37F.png` - 🍿 Popcorn
- `1F32D.png` - 🌭 Hot Dog
- `1F964.png` - 🥤 Cup with Straw (Soda)
- `1F381.png` - 🎁 Wrapped Gift (Boutique cadeaux)

### Employés (employees/)
- `1F477.png` - 👷 Construction Worker (Ingénieur)
- `1F9F9.png` - 🧹 Broom (Agent de maintenance - balai)
- `1F482.png` - 💂 Guard (Gardien de parc)
- `1F9F8.png` - 🧸 Teddy Bear (Mascotte - ours en peluche)

### Visiteurs (guests/)
**18 emojis diversifiés avec différents tons de peau :**

**Personne neutre :**
- `1F9D1.png` - 🧑 Person
- `1F9D1-1F3FB.png` - 🧑🏻 Person: Light Skin Tone
- `1F9D1-1F3FC.png` - 🧑🏼 Person: Medium-Light Skin Tone
- `1F9D1-1F3FD.png` - 🧑🏽 Person: Medium Skin Tone
- `1F9D1-1F3FE.png` - 🧑🏾 Person: Medium-Dark Skin Tone
- `1F9D1-1F3FF.png` - 🧑🏿 Person: Dark Skin Tone

**Homme :**
- `1F468.png` - 👨 Man
- `1F468-1F3FB.png` - 👨🏻 Man: Light Skin Tone
- `1F468-1F3FC.png` - 👨🏼 Man: Medium-Light Skin Tone
- `1F468-1F3FD.png` - 👨🏽 Man: Medium Skin Tone
- `1F468-1F3FE.png` - 👨🏾 Man: Medium-Dark Skin Tone
- `1F468-1F3FF.png` - 👨🏿 Man: Dark Skin Tone

**Femme :**
- `1F469.png` - 👩 Woman
- `1F469-1F3FB.png` - 👩🏻 Woman: Light Skin Tone
- `1F469-1F3FC.png` - 👩🏼 Woman: Medium-Light Skin Tone
- `1F469-1F3FD.png` - 👩🏽 Woman: Medium Skin Tone
- `1F469-1F3FE.png` - 👩🏾 Woman: Medium-Dark Skin Tone
- `1F469-1F3FF.png` - 👩🏿 Woman: Dark Skin Tone

*Chaque visiteur se voit attribuer aléatoirement un de ces 18 emojis pour une diversité visuelle réaliste.*

### Infrastructure (infrastructure/)
- `1F6BB.png` - 🚻 Restroom (Toilettes)
- `1F5D1.png` - 🗑️ Wastebasket (Poubelle)
- `1F6AA.png` - 🚪 Door (Porte/Entrée)

### Décorations (decorations/)
- `1F333.png` - 🌳 Deciduous Tree (Arbre)

## Format des fichiers

- **Format** : PNG
- **Taille** : 72x72 pixels
- **Transparence** : Oui (canal alpha)
- **Source** : https://github.com/hfg-gmuend/openmoji/tree/master/color/72x72

## Utilisation dans le jeu

Les emojis sont chargés automatiquement par le système d'assets du jeu :

```python
# Dans objects.json
{
  "sprite": "rides/1F3A0.png"  # Chemin relatif depuis assets/openmoji/
}
```

Le système de chargement cherche les sprites dans cet ordre :
1. `assets/openmoji/`
2. `assets/original/`
3. `assets/placeholders/`

## Ajouter de nouveaux emojis

Pour ajouter un nouvel emoji OpenMoji :

1. Trouver le code Unicode de l'emoji sur https://openmoji.org/
2. Télécharger le fichier PNG 72x72 :
   ```bash
   curl -L -o "HEXCODE.png" "https://github.com/hfg-gmuend/openmoji/raw/master/color/72x72/HEXCODE.png"
   ```
3. Placer le fichier dans le bon sous-dossier
4. Référencer le fichier dans `objects.json`

Exemple :
```bash
# Télécharger l'emoji 🎯 (Bullseye, 1F3AF)
cd assets/openmoji/rides/
curl -L -o "1F3AF.png" "https://github.com/hfg-gmuend/openmoji/raw/master/color/72x72/1F3AF.png"
```

## Licence et Attribution

Tous les emojis OpenMoji sont sous licence **CC BY-SA 4.0**.

**Attribution requise :**
```
Graphics: OpenMoji (https://openmoji.org)
License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
```

Cette attribution est incluse dans le fichier `README.md` principal du projet.

## Avantages d'OpenMoji pour OpenPark

✅ **Gratuit et open source** - Licence permissive
✅ **Style cohérent** - Design uniforme et professionnel
✅ **Large bibliothèque** - Des milliers d'emojis disponibles
✅ **Format PNG** - Transparence supportée par Pygame
✅ **Haute qualité** - Rendu net et clair
✅ **Communauté active** - Mises à jour régulières

## Ressources

- Documentation OpenMoji : https://openmoji.org/about/
- Liste complète des emojis : https://openmoji.org/library/
- Téléchargement bulk : https://github.com/hfg-gmuend/openmoji/releases

---

*Pour toute question sur l'utilisation des emojis OpenMoji dans OpenPark, consultez la documentation du projet.*
