"""
Research Bureau System - Gestion de la R&D avec budget mensuel et répartition par catégorie
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .debug import DebugConfig


@dataclass
class ResearchUpgrade:
    """Représente une amélioration/déblocage de recherche"""
    id: str
    name: str
    category: str
    cost: int  # Points nécessaires pour débloquer
    effect_type: str  # "unlock", "modifier", "mechanic"
    effect_data: dict  # Données de l'effet (varie selon le type)
    prerequisites: List[str]  # IDs des upgrades pré-requis
    description: str
    unlocked: bool = False

    def can_unlock(self, unlocked_upgrades: set, available_points: float) -> bool:
        """Vérifie si l'upgrade peut être débloqué"""
        if self.unlocked:
            return False
        if available_points < self.cost:
            return False
        for prereq_id in self.prerequisites:
            if prereq_id not in unlocked_upgrades:
                return False
        return True


class ResearchCategory:
    """Catégorie de recherche avec allocation et points"""
    def __init__(self, name: str):
        self.name = name
        self.allocation = 0.0  # Pourcentage du budget (0.0 à 1.0)
        self.points = 0.0  # Points accumulés

    def get_points_cap(self, upgrades_list: List[ResearchUpgrade], unlocked_ids: set) -> int:
        """
        Calcule la limite dynamique de points basée sur l'upgrade le plus cher débloquable

        Returns:
            Coût de l'upgrade le plus cher dont les pré-requis sont remplis (min 1000)
        """
        max_cost = 0
        for upgrade in upgrades_list:
            if upgrade.category == self.name and not upgrade.unlocked:
                # Vérifier si pré-requis remplis
                prereqs_met = all(pid in unlocked_ids for pid in upgrade.prerequisites)
                if prereqs_met:
                    max_cost = max(max_cost, upgrade.cost)

        # Minimum 1000 si rien de débloquable, sinon le coût max trouvé
        return max_cost if max_cost > 0 else 1000

    def add_daily_points(self, monthly_budget: int, points_cap: int):
        """
        Ajoute les points quotidiens selon l'allocation, sans dépasser la limite

        Args:
            monthly_budget: Budget mensuel de R&D
            points_cap: Limite maximale de points pour cette catégorie

        Returns:
            Nombre de points réellement ajoutés
        """
        if self.points >= points_cap:
            # Déjà au maximum, aucun point ajouté
            return 0.0

        daily_points = (monthly_budget * self.allocation) / 30.0

        # Ne pas dépasser la limite
        if self.points + daily_points > points_cap:
            # Ajuster pour ne pas dépasser
            actual_points = points_cap - self.points
            self.points = points_cap
            return actual_points
        else:
            self.points += daily_points
            return daily_points

    def spend_points(self, cost: int):
        """Dépense des points pour un upgrade"""
        if self.points >= cost:
            self.points -= cost
            return True
        return False

    def reset_points(self):
        """Remet les points à zéro (utilisé si budget non payé)"""
        self.points = 0.0

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'allocation': self.allocation,
            'points': self.points
        }

    def from_dict(self, data: dict):
        self.name = data.get('name', self.name)
        self.allocation = data.get('allocation', 0.0)
        self.points = data.get('points', 0.0)


class ResearchBureau:
    """Système de bureau de R&D avec budget mensuel et répartition par catégorie"""

    CATEGORIES = [
        "visitors",      # Visiteurs (spawn, satisfaction, comportement)
        "attractions",   # Attractions (déblocages, améliorations)
        "shops",         # Shops (déblocages, coûts, qualité)
        "employees",     # Employés (efficacité, vitesse, types)
        "decorations",   # Décorations (déblocages, effets)
        "infrastructure" # Infrastructure (systèmes globaux)
    ]

    MAX_MONTHLY_BUDGET = 5000  # Budget mensuel maximum

    def __init__(self):
        self.monthly_budget = 0  # Budget mensuel alloué à la R&D
        self.categories: Dict[str, ResearchCategory] = {}
        self.upgrades: List[ResearchUpgrade] = []
        self.unlocked_ids: set = set()  # IDs des upgrades débloqués

        # Tracking du dernier prélèvement
        self.last_deduction_day = 1
        self.last_deduction_month = 1
        self.total_spent_this_month = 0

        # Initialiser les catégories
        for cat_name in self.CATEGORIES:
            self.categories[cat_name] = ResearchCategory(cat_name)

    def load_upgrades_from_config(self, config: dict):
        """Charge l'arbre de recherche depuis la configuration JSON"""
        research_data = config.get('research_tree', {})

        for category_name, upgrades_list in research_data.items():
            for upgrade_data in upgrades_list:
                upgrade = ResearchUpgrade(
                    id=upgrade_data['id'],
                    name=upgrade_data['name'],
                    category=category_name,
                    cost=upgrade_data['cost'],
                    effect_type=upgrade_data['effect_type'],
                    effect_data=upgrade_data['effect_data'],
                    prerequisites=upgrade_data.get('prerequisites', []),
                    description=upgrade_data['description'],
                    unlocked=False
                )
                self.upgrades.append(upgrade)

        DebugConfig.log('research', f"Loaded {len(self.upgrades)} research upgrades")

    def set_monthly_budget(self, amount: int):
        """Définit le budget mensuel de R&D (modifiable à tout moment, max $5000)"""
        self.monthly_budget = max(0, min(amount, self.MAX_MONTHLY_BUDGET))
        DebugConfig.log('research', f"R&D monthly budget set to ${self.monthly_budget}")

    def set_category_allocation(self, category: str, percentage: float):
        """Définit l'allocation d'une catégorie (0.0 à 1.0)"""
        if category in self.categories:
            self.categories[category].allocation = max(0.0, min(1.0, percentage))

    def get_total_allocation(self) -> float:
        """Retourne la somme des allocations (doit être <= 1.0)"""
        return sum(cat.allocation for cat in self.categories.values())

    def tick_day(self, current_day: int, current_month: int, player_cash: int) -> Tuple[bool, str]:
        """
        Tick quotidien du système de recherche

        Returns:
            (success, message) - success=False si budget non payé
        """
        # Vérifier si on doit faire le prélèvement mensuel
        if current_day == 1 and (current_day != self.last_deduction_day or current_month != self.last_deduction_month):
            success, msg = self._try_monthly_deduction(player_cash)
            if not success:
                return False, msg

        # Accumuler les points quotidiens SEULEMENT si le joueur a du cash strictement positif
        if self.monthly_budget > 0 and player_cash > 0:
            for category in self.categories.values():
                if category.allocation > 0:
                    # Calculer la limite dynamique pour cette catégorie
                    points_cap = category.get_points_cap(self.upgrades, self.unlocked_ids)
                    points_added = category.add_daily_points(self.monthly_budget, points_cap)

                    if points_added > 0:
                        DebugConfig.log('research', f"{category.name}: +{points_added:.2f} pts (total: {category.points:.2f}/{points_cap})")
                    elif category.points >= points_cap:
                        DebugConfig.log('research', f"{category.name}: ⚠️ LIMITE ATTEINTE ({category.points:.0f}/{points_cap}) - Débloquez une amélioration!")
        elif player_cash <= 0:
            DebugConfig.log('research', "⚠️ R&D suspended: No cash available - No points accumulated today")

        return True, ""

    def _try_monthly_deduction(self, player_cash: int) -> Tuple[bool, str]:
        """
        Tente de prélever le budget mensuel

        Returns:
            (success, message)
        """
        if self.monthly_budget <= player_cash:
            # Prélèvement réussi
            self.last_deduction_day = 1
            self.last_deduction_month = self.last_deduction_month % 12 + 1
            self.total_spent_this_month = self.monthly_budget

            DebugConfig.log('research', f"R&D budget deducted: ${self.monthly_budget}")
            return True, f"R&D budget deducted: ${self.monthly_budget}"
        else:
            # Pas assez de cash : suspension + reset
            self._suspend_research()
            msg = f"⚠️ R&D SUSPENDED - Insufficient funds (${player_cash} < ${self.monthly_budget}). All points reset!"
            DebugConfig.log('research', msg)
            return False, msg

    def _suspend_research(self):
        """Suspend la recherche et reset tous les points (pénalité)"""
        for category in self.categories.values():
            category.reset_points()

        DebugConfig.log('research', "R&D suspended - all points reset to zero")

    def unlock_upgrade_manual(self, upgrade: ResearchUpgrade) -> Tuple[bool, str]:
        """
        Débloque manuellement un upgrade si les conditions sont remplies

        Returns:
            (success, message)
        """
        if upgrade.unlocked:
            return False, "Already unlocked"

        category = self.categories.get(upgrade.category)
        if not category:
            return False, "Invalid category"

        # Vérifier les pré-requis
        if not upgrade.can_unlock(self.unlocked_ids, category.points):
            # Vérifier quel est le problème
            prereqs_met = all(pid in self.unlocked_ids for pid in upgrade.prerequisites)
            if not prereqs_met:
                return False, "Pré-requis non remplis"
            else:
                return False, f"Points insuffisants ({category.points:.0f}/{upgrade.cost})"

        # Débloquer !
        category.spend_points(upgrade.cost)
        upgrade.unlocked = True
        self.unlocked_ids.add(upgrade.id)

        DebugConfig.log('research', f"🔬 MANUALLY UNLOCKED: {upgrade.name} ({upgrade.category})")
        return True, f"✅ {upgrade.name} débloqué!"

    def _check_and_unlock_upgrades(self):
        """DEPRECATED - Plus utilisé (déblocage manuel seulement)"""
        pass

    def get_upgrade_by_id(self, upgrade_id: str) -> Optional[ResearchUpgrade]:
        """Récupère un upgrade par son ID"""
        for upgrade in self.upgrades:
            if upgrade.id == upgrade_id:
                return upgrade
        return None

    def is_unlocked(self, upgrade_id: str) -> bool:
        """Vérifie si un upgrade est débloqué"""
        return upgrade_id in self.unlocked_ids

    def get_modifier(self, effect_name: str) -> float:
        """
        Récupère la valeur cumulée d'un modificateur

        Ex: "spawn_rate_multiplier" → 1.0 + 0.1 + 0.2 = 1.3
        """
        total = 0.0
        base = 1.0 if "multiplier" in effect_name else 0.0

        for upgrade in self.upgrades:
            if not upgrade.unlocked:
                continue

            if upgrade.effect_type == "modifier":
                if upgrade.effect_data.get('name') == effect_name:
                    value = upgrade.effect_data.get('value', 0.0)
                    total += value

        return base + total if "multiplier" in effect_name else total

    def get_unlocked_items(self, item_type: str) -> List[str]:
        """
        Récupère la liste des items débloqués d'un certain type

        Args:
            item_type: "ride", "shop", "employee", "decoration"

        Returns:
            Liste des IDs d'items débloqués
        """
        unlocked_items = []

        for upgrade in self.upgrades:
            if not upgrade.unlocked:
                continue

            if upgrade.effect_type == "unlock":
                if upgrade.effect_data.get('type') == item_type:
                    items = upgrade.effect_data.get('items', [])
                    unlocked_items.extend(items)

        return unlocked_items

    def get_category_progress(self, category: str) -> dict:
        """Récupère les informations de progression d'une catégorie"""
        cat = self.categories.get(category)
        if not cat:
            return {}

        # Récupérer les upgrades de cette catégorie
        category_upgrades = [u for u in self.upgrades if u.category == category]

        # Trier par coût
        category_upgrades.sort(key=lambda u: u.cost)

        # Trouver le prochain upgrade débloquable
        next_upgrade = None
        for upgrade in category_upgrades:
            if not upgrade.unlocked and upgrade.can_unlock(self.unlocked_ids, 0):
                # Pré-requis OK, juste besoin de points
                next_upgrade = upgrade
                break

        # Calculer la limite dynamique
        points_cap = cat.get_points_cap(self.upgrades, self.unlocked_ids)

        return {
            'allocation': cat.allocation,
            'points': cat.points,
            'points_cap': points_cap,
            'daily_points': (self.monthly_budget * cat.allocation) / 30.0 if self.monthly_budget > 0 else 0.0,
            'upgrades': category_upgrades,
            'next_upgrade': next_upgrade
        }

    def get_days_until_next_deduction(self, current_day: int) -> int:
        """Calcule le nombre de jours avant le prochain prélèvement"""
        if current_day == 1:
            return 30
        return 31 - current_day  # Simplifié (assume mois de 30 jours)

    def to_dict(self) -> dict:
        """Sérialisation pour sauvegarde"""
        return {
            'monthly_budget': self.monthly_budget,
            'categories': {name: cat.to_dict() for name, cat in self.categories.items()},
            'unlocked_ids': list(self.unlocked_ids),
            'last_deduction_day': self.last_deduction_day,
            'last_deduction_month': self.last_deduction_month,
            'total_spent_this_month': self.total_spent_this_month
        }

    def from_dict(self, data: dict):
        """Désérialisation depuis sauvegarde"""
        self.monthly_budget = data.get('monthly_budget', 0)
        self.last_deduction_day = data.get('last_deduction_day', 1)
        self.last_deduction_month = data.get('last_deduction_month', 1)
        self.total_spent_this_month = data.get('total_spent_this_month', 0)

        # Restaurer les catégories
        categories_data = data.get('categories', {})
        for cat_name, cat_data in categories_data.items():
            if cat_name in self.categories:
                self.categories[cat_name].from_dict(cat_data)

        # Restaurer les IDs débloqués
        self.unlocked_ids = set(data.get('unlocked_ids', []))

        # Marquer les upgrades comme débloqués
        for upgrade in self.upgrades:
            if upgrade.id in self.unlocked_ids:
                upgrade.unlocked = True

        DebugConfig.log('research', f"Research bureau restored - {len(self.unlocked_ids)} upgrades unlocked")
