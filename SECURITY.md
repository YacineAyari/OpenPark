# Security Policy - OpenPark 🔒

## Reporting Security Vulnerabilities

OpenPark est un projet de jeu vidéo open source en développement alpha. Bien qu'il ne gère pas de données sensibles, nous prenons la sécurité au sérieux.

### Comment signaler une vulnérabilité

Si vous découvrez une vulnérabilité de sécurité dans OpenPark:

1. **NE PAS** créer une Issue publique
2. **Contactez** les mainteneurs de manière privée:
   - Créez une [Security Advisory](https://github.com/Enicay/openpark/security/advisories/new) (recommandé)
   - Ou envoyez un email à: [VOTRE_EMAIL_SECURITE]

### Informations à inclure

Veuillez inclure autant d'informations que possible:

- **Description** de la vulnérabilité
- **Steps to reproduce** le problème
- **Impact potentiel** (que peut faire un attaquant?)
- **Versions affectées**
- **Solutions potentielles** (si vous en avez)

### Scope de sécurité

OpenPark est un jeu local qui:
- ✅ **Ne se connecte pas à Internet** (pas de réseau)
- ✅ **Ne collecte aucune donnée** utilisateur
- ✅ **Ne stocke pas de données sensibles**
- ✅ **Exécute uniquement en local**

### Types de vulnérabilités pertinentes:

Nous sommes particulièrement intéressés par:

🔴 **Haute priorité:**
- Exécution de code arbitraire
- Déni de service (DoS)
- Corruption de fichiers système
- Injection de code malveillant

🟡 **Moyenne priorité:**
- Path traversal (lecture/écriture de fichiers non autorisés)
- Corruption de sauvegardes
- Crashes exploitables

🟢 **Basse priorité:**
- Bugs de gameplay (utilisez les Issues normales)
- Problèmes de performance
- Bugs graphiques

### Ce qui N'EST PAS une vulnérabilité de sécurité:

- Bugs de jeu normaux
- Exploits de gameplay (ex: duplication d'argent dans le jeu)
- Problèmes de compatibilité
- Suggestions d'améliorations

**Pour ces cas, utilisez les [Issues normales](https://github.com/Enicay/openpark/issues).**

## Processus de réponse

1. **Acknowledgement**: Nous accuserons réception sous **48 heures**
2. **Investigation**: Nous évaluerons la vulnérabilité
3. **Fix**: Nous développerons un correctif (timeline dépend de la sévérité)
4. **Release**: Publication d'un patch de sécurité
5. **Disclosure**: Annonce publique après que le fix soit disponible

### Timeline estimée:

- 🔴 **Critique**: Fix en 1-7 jours
- 🟡 **Haute**: Fix en 1-4 semaines
- 🟢 **Moyenne/Basse**: Fix dans la prochaine release

## Versions supportées

| Version | Support |
| ------- | ------- |
| 0.3.x (alpha) | ✅ Supportée |
| < 0.3.0 | ❌ Non supportée |

**Note**: Le projet est en alpha. Nous recommandons de toujours utiliser la dernière version.

## Bonnes pratiques de sécurité

### Pour les utilisateurs:

✅ **Téléchargez uniquement depuis les sources officielles**:
- Repository GitHub officiel
- Releases GitHub officielles

❌ **Ne téléchargez PAS depuis**:
- Sites tiers non vérifiés
- Liens suspects
- Forks non officiels (sauf si vous faites confiance au développeur)

✅ **Vérifiez l'intégrité**:
- Comparez les checksums (fournis dans les releases)
- Vérifiez les signatures GPG (si disponibles)

### Pour les contributeurs:

✅ **Code sûr**:
- Validez les entrées utilisateur
- Évitez `eval()` et `exec()` sur input non contrôlé
- Utilisez des bibliothèques à jour
- Pas de secrets/credentials dans le code

✅ **Dépendances**:
- Gardez les dépendances à jour (`pip list --outdated`)
- Vérifiez les vulnérabilités connues ([Safety](https://pypi.org/project/safety/))

✅ **IA-generated code**:
- **Reviewez le code généré par IA** avant de commit
- Les IA peuvent parfois générer du code vulnérable
- Vérifiez particulièrement:
  - Manipulation de fichiers
  - Exécution de commandes
  - Parsing de données externes

## Dépendances de sécurité

OpenPark utilise:
- **Python 3.8+** - Utilisez une version supportée par la PSF
- **Pygame** - Librarie mature et largement utilisée

Nous surveillons les vulnérabilités dans nos dépendances via:
- GitHub Dependabot
- [Safety](https://pypi.org/project/safety/) checks

## Questions de sécurité

Pour toute question sur la sécurité du projet (hors vulnérabilités):
- Créez une [Discussion GitHub](https://github.com/Enicay/openpark/discussions)
- Taguez avec `security` et `question`

---

## Remerciements

Nous remercions les chercheurs en sécurité et contributeurs qui signalent de manière responsable les vulnérabilités.

Les contributeurs qui signalent des vulnérabilités valides seront:
- 🎖️ Crédités dans les release notes (si souhaité)
- 📜 Listés dans un futur SECURITY_HALL_OF_FAME.md
- 💝 Remerciés publiquement (avec permission)

---

**Merci de nous aider à garder OpenPark sûr pour tous!** 🔒

---

*Dernière mise à jour: 2025-01-XX*
