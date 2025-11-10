"""
Notification System - Toast notifications and history panel
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
from enum import Enum

# Full month names for timestamp formatting
MONTH_NAMES_FULL = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class NotificationType(Enum):
    """Types de notifications avec priorités et couleurs"""
    CRITICAL = ("critical", (255, 50, 50))      # Rouge - Action immédiate
    WARNING = ("warning", (255, 180, 50))       # Orange - Attention recommandée
    INFO = ("info", (255, 255, 100))            # Jaune - Information utile
    SUCCESS = ("success", (100, 255, 100))      # Vert - Feedback positif


@dataclass
class Notification:
    """Représente une notification"""
    id: int
    type: NotificationType
    message: str
    timestamp: str  # Format "Day X"
    game_day: int
    read: bool = False
    clickable: bool = False  # Si True, peut centrer caméra ou ouvrir modal
    click_action: Optional[str] = None  # "center_camera", "open_rd", etc.
    click_data: Optional[dict] = None  # Données pour l'action (ex: position)


class NotificationManager:
    """Gestionnaire de notifications avec historique et cooldowns"""

    MAX_HISTORY = 20
    COOLDOWN_TIMES = {
        "unhappy_visitor": 300.0,  # 5 min entre notifications visiteur mécontent
        "low_stock": 86400.0,      # 1 jour entre alertes stock bas
        "negative_cash": 86400.0,  # 1 jour entre alertes cash négatif
        "queue_full": 300.0,       # 5 min entre alertes queue pleine
    }

    def __init__(self):
        self.notifications: List[Notification] = []
        self.next_id = 1
        self.cooldowns = {}  # key -> last_time

    def add(self,
            notif_type: NotificationType,
            message: str,
            game_time: Tuple[int, int, int, int, int],  # (year, month, day, hour, minute)
            clickable: bool = False,
            click_action: Optional[str] = None,
            click_data: Optional[dict] = None,
            cooldown_key: Optional[str] = None) -> Optional[Notification]:
        """
        Ajoute une notification

        Args:
            notif_type: Type de notification
            message: Message à afficher
            game_time: (year, month, day, hour, minute) du jeu
            clickable: Si True, notification cliquable
            click_action: Action à effectuer au clic
            click_data: Données pour l'action
            cooldown_key: Clé de cooldown (empêche spam)

        Returns:
            Notification créée ou None si cooldown actif
        """
        # Vérifier cooldown
        if cooldown_key:
            # For cooldown, use day-based time calculation
            year, month, day, hour, minute = game_time
            current_time = (year * 365 + month * 30 + day) * 86400 + hour * 3600 + minute * 60
            if cooldown_key in self.cooldowns:
                last_time = self.cooldowns[cooldown_key]
                cooldown_duration = self.COOLDOWN_TIMES.get(cooldown_key, 0)
                if current_time - last_time < cooldown_duration:
                    return None  # Cooldown actif, skip

            # Enregistrer nouveau cooldown
            self.cooldowns[cooldown_key] = current_time

        # Créer notification
        year, month, day, hour, minute = game_time
        month_name = MONTH_NAMES_FULL[month - 1] if 1 <= month <= 12 else "Unknown"
        timestamp = f"{day:02d} {month_name} {year}"

        notif = Notification(
            id=self.next_id,
            type=notif_type,
            message=message,
            timestamp=timestamp,
            game_day=day,
            read=False,
            clickable=clickable,
            click_action=click_action,
            click_data=click_data
        )

        self.next_id += 1

        # Ajouter en début de liste (plus récent en premier)
        self.notifications.insert(0, notif)

        # Limiter l'historique
        if len(self.notifications) > self.MAX_HISTORY:
            self.notifications = self.notifications[:self.MAX_HISTORY]

        return notif

    def get_unread_count(self) -> int:
        """Retourne le nombre de notifications non lues"""
        return sum(1 for n in self.notifications if not n.read)

    def mark_read(self, notification_id: int):
        """Marque une notification comme lue"""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.read = True
                break

    def mark_all_read(self):
        """Marque toutes les notifications comme lues"""
        for notif in self.notifications:
            notif.read = True

    def get_history(self, limit: int = MAX_HISTORY) -> List[Notification]:
        """Retourne l'historique des notifications (limitées)"""
        return self.notifications[:limit]

    def get_recent_toasts(self, max_count: int = 3) -> List[Notification]:
        """Retourne les notifications récentes pour affichage toast"""
        # Retourne les max_count premières non lues
        unread = [n for n in self.notifications if not n.read]
        return unread[:max_count]

    def to_dict(self) -> dict:
        """Sérialisation pour sauvegarde"""
        return {
            'notifications': [
                {
                    'id': n.id,
                    'type': n.type.name,
                    'message': n.message,
                    'timestamp': n.timestamp,
                    'game_day': n.game_day,
                    'read': n.read,
                    'clickable': n.clickable,
                    'click_action': n.click_action,
                    'click_data': n.click_data
                }
                for n in self.notifications
            ],
            'next_id': self.next_id,
            'cooldowns': self.cooldowns
        }

    def from_dict(self, data: dict):
        """Désérialisation depuis sauvegarde"""
        self.next_id = data.get('next_id', 1)
        self.cooldowns = data.get('cooldowns', {})

        notifications_data = data.get('notifications', [])
        self.notifications = []

        for n_data in notifications_data:
            try:
                notif_type = NotificationType[n_data['type']]
                notif = Notification(
                    id=n_data['id'],
                    type=notif_type,
                    message=n_data['message'],
                    timestamp=n_data['timestamp'],
                    game_day=n_data['game_day'],
                    read=n_data.get('read', False),
                    clickable=n_data.get('clickable', False),
                    click_action=n_data.get('click_action'),
                    click_data=n_data.get('click_data')
                )
                self.notifications.append(notif)
            except (KeyError, ValueError):
                # Skip invalid notifications
                continue
