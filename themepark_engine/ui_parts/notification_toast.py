"""
Toast Notifications - Affichage temporaire top-right
"""

import pygame
from typing import List, Optional
from pathlib import Path
from ..notification import Notification, NotificationType


class NotificationToast:
    """Gestionnaire d'affichage des toasts (notifications temporaires)"""

    TOAST_DURATION = 6.0  # Secondes avant auto-dismiss
    TOAST_WIDTH = 350
    TOAST_HEIGHT = 60
    TOAST_SPACING = 10
    MAX_VISIBLE = 3

    # Sprites OpenMoji par type
    TYPE_ICONS = {
        NotificationType.CRITICAL: "274C.png",   # X rouge
        NotificationType.WARNING: "26A0.png",     # Panneau d'avertissement
        NotificationType.INFO: "2139.png",        # Information
        NotificationType.SUCCESS: "2705.png"      # Checkmark vert
    }

    def __init__(self):
        self.active_toasts: List[dict] = []  # {notification, timer, y_offset, alpha}

        # Charger les icônes OpenMoji (24x24)
        self.type_icons = {}
        assets_path = Path(__file__).parent.parent.parent / "assets" / "openmoji"
        for notif_type, icon_file in self.TYPE_ICONS.items():
            icon_path = assets_path / icon_file
            if icon_path.exists():
                icon = pygame.image.load(str(icon_path))
                self.type_icons[notif_type] = pygame.transform.scale(icon, (24, 24))
            else:
                print(f"Warning: Icon not found: {icon_path}")

    def add_toast(self, notification: Notification):
        """Ajoute un toast à afficher"""
        # Ne pas ajouter si déjà présent
        for toast in self.active_toasts:
            if toast['notification'].id == notification.id:
                return

        # Limiter à MAX_VISIBLE
        if len(self.active_toasts) >= self.MAX_VISIBLE:
            # Retirer le plus ancien
            self.active_toasts.pop()

        # Ajouter en début de liste
        self.active_toasts.insert(0, {
            'notification': notification,
            'timer': self.TOAST_DURATION,
            'y_offset': 0,
            'alpha': 255,
            'target_y': 0
        })

        # Recalculer les positions cibles
        self._recalculate_positions()

    def update(self, dt: float):
        """Met à jour les toasts (timers et animations)"""
        to_remove = []

        for i, toast in enumerate(self.active_toasts):
            # Décrémenter timer
            toast['timer'] -= dt

            # Fade out si timer < 1s
            if toast['timer'] < 1.0:
                toast['alpha'] = int(255 * toast['timer'])
            else:
                toast['alpha'] = 255

            # Marquer pour suppression si timer écoulé
            if toast['timer'] <= 0:
                to_remove.append(toast)
            else:
                # Animation slide vers position cible
                target_y = toast['target_y']
                current_y = toast['y_offset']
                diff = target_y - current_y

                if abs(diff) > 1:
                    toast['y_offset'] += diff * 0.15  # Smooth lerp
                else:
                    toast['y_offset'] = target_y

        # Retirer les toasts expirés
        for toast in to_remove:
            self.active_toasts.remove(toast)

        # Recalculer positions après suppression
        if to_remove:
            self._recalculate_positions()

    def _recalculate_positions(self):
        """Recalcule les positions cibles de tous les toasts"""
        for i, toast in enumerate(self.active_toasts):
            toast['target_y'] = i * (self.TOAST_HEIGHT + self.TOAST_SPACING)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Dessine tous les toasts actifs"""
        if not self.active_toasts:
            return

        screen_w, screen_h = screen.get_size()
        start_x = screen_w - self.TOAST_WIDTH - 20
        start_y = 80  # En dessous du HUD

        for toast in self.active_toasts:
            notif = toast['notification']
            y_pos = start_y + int(toast['y_offset'])
            alpha = toast['alpha']

            # Créer surface avec alpha
            toast_surface = pygame.Surface((self.TOAST_WIDTH, self.TOAST_HEIGHT), pygame.SRCALPHA)

            # Couleur du type pour la bordure
            type_color = notif.type.value[1]  # Couleur RGB du type
            bg_rect = pygame.Rect(0, 0, self.TOAST_WIDTH, self.TOAST_HEIGHT)

            # Background sombre uniforme pour lisibilité
            dark_bg = (40, 40, 50, int(240 * alpha / 255))
            pygame.draw.rect(toast_surface, dark_bg, bg_rect, border_radius=8)

            # Bordure colorée épaisse selon le type (3px)
            border_color = (*type_color[:3], alpha)
            pygame.draw.rect(toast_surface, border_color, bg_rect, 3, border_radius=8)

            # Icône OpenMoji
            icon = self.type_icons.get(notif.type)
            if icon:
                # Appliquer alpha si nécessaire
                if alpha < 255:
                    icon_with_alpha = icon.copy()
                    icon_with_alpha.set_alpha(alpha)
                    toast_surface.blit(icon_with_alpha, (10, 18))
                else:
                    toast_surface.blit(icon, (10, 18))

            # Message (word wrap si nécessaire)
            message = notif.message
            max_width = self.TOAST_WIDTH - 50

            # Découper message si trop long
            words = message.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                test_render = font.render(test_line, True, (255, 255, 255))
                if test_render.get_width() <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Limiter à 2 lignes
            lines = lines[:2]

            # Afficher lignes
            for i, line in enumerate(lines):
                text_render = font.render(line, True, (255, 255, 255, alpha))
                toast_surface.blit(text_render, (40, 10 + i * 20))

            # Timestamp (petit, en bas à droite)
            timestamp_text = f"Day {notif.game_day} - {notif.timestamp}"
            small_font = pygame.font.Font(None, 16)
            timestamp_render = small_font.render(timestamp_text, True, (200, 200, 200, alpha))
            toast_surface.blit(timestamp_render, (self.TOAST_WIDTH - 120, self.TOAST_HEIGHT - 18))

            # Bouton fermer (X) si cliquable ou temps > 2s
            if toast['timer'] > 2.0 or notif.clickable:
                close_x = self.TOAST_WIDTH - 25
                close_y = 5
                close_rect = pygame.Rect(close_x, close_y, 20, 20)
                pygame.draw.rect(toast_surface, (150, 50, 50, alpha), close_rect, border_radius=3)
                close_text = font.render("×", True, (255, 255, 255, alpha))
                toast_surface.blit(close_text, (close_x + 4, close_y))

            # Blitter sur l'écran
            screen.blit(toast_surface, (start_x, y_pos))

    def handle_click(self, mouse_pos: tuple, screen_size: tuple) -> Optional[Notification]:
        """
        Gère le clic sur un toast

        Returns:
            Notification cliquée ou None
        """
        screen_w, screen_h = screen_size
        start_x = screen_w - self.TOAST_WIDTH - 20
        start_y = 80

        for toast in self.active_toasts:
            y_pos = start_y + int(toast['y_offset'])
            toast_rect = pygame.Rect(start_x, y_pos, self.TOAST_WIDTH, self.TOAST_HEIGHT)

            if toast_rect.collidepoint(mouse_pos):
                # Vérifier si clic sur bouton fermer
                close_x = start_x + self.TOAST_WIDTH - 25
                close_y = y_pos + 5
                close_rect = pygame.Rect(close_x, close_y, 20, 20)

                if close_rect.collidepoint(mouse_pos):
                    # Fermer immédiatement
                    self.active_toasts.remove(toast)
                    self._recalculate_positions()
                    return None
                else:
                    # Clic sur le toast lui-même
                    notif = toast['notification']
                    if notif.clickable:
                        # Retirer le toast et retourner la notification
                        self.active_toasts.remove(toast)
                        self._recalculate_positions()
                        return notif

        return None

    def clear_all(self):
        """Ferme tous les toasts"""
        self.active_toasts.clear()
