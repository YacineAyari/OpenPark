# OpenPark - Documentation GitHub 📚

Ce dossier `.github/` contient toute la configuration et les templates pour le projet OpenPark sur GitHub.

## 📁 Structure

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md              # Template pour signaler des bugs
│   ├── feature_request.md         # Template pour proposer des features
│   └── vibe_coding_discussion.md  # Template pour discussions vibe coding
├── workflows/
│   └── ci.yml.template            # CI/CD configuration (à activer plus tard)
├── PULL_REQUEST_TEMPLATE.md       # Template pour les Pull Requests
├── labels.yml                      # Configuration des labels GitHub
└── README.md                       # Ce fichier
```

## 🎯 Templates d'Issues

### 🐛 Bug Report
**Quand l'utiliser**: Vous avez trouvé un bug ou un comportement inattendu

**Inclut**:
- Description du bug
- Steps to reproduce
- Comportement attendu vs observé
- Environment (OS, Python, Pygame versions)
- Logs (si disponibles)
- Option pour indiquer si développé/investigué avec IA

### 💡 Feature Request
**Quand l'utiliser**: Vous voulez proposer une nouvelle fonctionnalité

**Inclut**:
- Description de la feature
- Problème résolu
- Solution proposée
- Priorité suggérée
- Approche de développement (vibe coding ou traditionnel)
- Relation avec la roadmap

### 🤖 Vibe Coding Discussion
**Quand l'utiliser**: Partager des expériences, prompts, ou poser des questions sur le vibe coding

**Inclut**:
- Type de discussion (partage, question, retour d'expérience)
- Outil(s) IA utilisé(s)
- Prompts efficaces
- Difficultés rencontrées et solutions
- Temps et itérations

## 📝 Pull Request Template

**Sections principales**:
- Description et type de contribution
- Changes apportés
- **Section Vibe Coding** (si applicable):
  - IA utilisée
  - Prompts clés
  - Itérations et difficultés
  - Temps de développement
- **Section Code Traditionnel** (si applicable):
  - Approche technique
  - Difficultés rencontrées
- Testing et screenshots
- Documentation mise à jour
- Checklist finale

## 🏷️ Labels GitHub

Le fichier `labels.yml` définit tous les labels utilisés dans le projet:

### Par priorité:
- `priority: high/medium/low` - Niveau d'urgence

### Par type:
- `type: bug/feature/enhancement/documentation/refactor`

### Par méthode de développement:
- `vibe-coding` 🤖 - Développé avec IA
- `traditional-code` 💻 - Développé manuellement
- `hybrid` 🔀 - Mix des deux

### Pour les nouveaux contributeurs:
- `good first issue` - Bon pour débuter
- `good for AI` - Adapté au vibe coding
- `needs manual coding` - Requiert expertise humaine

### Par composant:
- `component: engine/AI/rendering/UI/economy/pathfinding`

### Par statut:
- `status: in progress/blocked/needs review/needs testing`

## 🔄 GitHub Actions (CI/CD)

Le fichier `workflows/ci.yml.template` contient la configuration pour:
- ✅ **Linting** (flake8, pylint)
- ✅ **Security checks** (Safety)
- ✅ **Tests multi-plateforme** (Linux, Windows, macOS)
- ✅ **Auto-labeling** des PRs
- ✅ **Welcome message** pour nouveaux contributeurs

**Pour activer**: Renommer `ci.yml.template` → `ci.yml`

## 📖 Utilisation

### Créer une Issue

1. Aller sur [Issues](https://github.com/Enicay/openpark/issues)
2. Cliquer "New Issue"
3. Choisir un template (Bug Report, Feature Request, Vibe Coding Discussion)
4. Remplir les sections
5. Submit!

### Créer une Pull Request

1. Fork le projet
2. Créer une branche (`git checkout -b feature/ma-feature`)
3. Faire vos modifications
4. Commit (`git commit -m "feat: Ma feature"`)
5. Push (`git push origin feature/ma-feature`)
6. Créer la PR sur GitHub
7. Le template se remplira automatiquement
8. Compléter les sections pertinentes
9. Submit!

### Ajouter des labels

**Automatique**: GitHub Actions ajoutera des labels basés sur les fichiers modifiés

**Manuel**: Les mainteneurs peuvent ajouter des labels additionnels

## 🎨 Customization

### Modifier les templates

Les templates sont en Markdown et peuvent être modifiés:

```bash
# Éditer un template
nano .github/ISSUE_TEMPLATE/bug_report.md

# Commit et push
git add .github/
git commit -m "docs: Update bug report template"
git push
```

### Ajouter un nouveau template

```bash
# Créer un nouveau fichier dans ISSUE_TEMPLATE/
touch .github/ISSUE_TEMPLATE/mon_template.md

# Ajouter le front matter:
---
name: Mon Template
about: Description
title: '[PREFIX] '
labels: mon-label
assignees: ''
---

# Contenu du template
```

### Configurer les labels

Utiliser `gh` CLI pour créer les labels depuis `labels.yml`:

```bash
# Installer gh CLI
# https://cli.github.com/

# Créer tous les labels
gh label create -f .github/labels.yml
```

## 🤝 Bonnes Pratiques

### Issues
- ✅ Utilisez les templates
- ✅ Soyez descriptif et précis
- ✅ Ajoutez des screenshots si pertinent
- ✅ Indiquez votre méthode de développement (vibe coding ou non)
- ✅ Référencez les issues liées

### Pull Requests
- ✅ Remplissez toutes les sections du template
- ✅ Cochez la checklist
- ✅ Ajoutez des screenshots pour les changements visuels
- ✅ Documentez vos prompts si vibe coding
- ✅ Expliquez vos choix techniques si code traditionnel

### Labels
- ✅ Ajoutez TOUJOURS `vibe-coding` ou `traditional-code`
- ✅ Ajoutez un label de priorité
- ✅ Ajoutez un label de type
- ✅ Ajoutez un label de composant si applicable

## ❓ Questions

Si vous avez des questions sur l'utilisation de ces templates:
- Créez une Discussion GitHub
- Ou ouvrez une Issue avec le template Vibe Coding Discussion

---

**Ces templates sont conçus pour rendre la contribution facile et documentée, que vous codiez avec une IA ou à la main!** 🎢🤖💻
