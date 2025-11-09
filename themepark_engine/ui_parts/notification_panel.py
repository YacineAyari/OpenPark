"""
Notification History Panel - Historique des 20 dernières notifications
"""

import pygame
from typing import Optional
from pathlib import Path
from ..notification import Notification, NotificationType


class NotificationPanel:
    """Panneau d'historique des notifications"""

    # Sprites OpenMoji par type
    TYPE_ICONS = {
        NotificationType.CRITICAL: "274C.png",   # X rouge
        NotificationType.WARNING: "26A0.png",     # Panneau d'avertissement
        NotificationType.INFO: "2139.png",        # Information
        NotificationType.SUCCESS: "2705.png"      # Checkmark vert
    }

    def __init__(self):
        self.visible = False
        self.scroll_offset = 0
        self.max_scroll = 0

        # UI Rects
        self.close_button_rect = None
        self.clear_all_button_rect = None
        self.notification_rects = {}  # notification_id -> rect
        self.scroll_up_rect = None
        self.scroll_down_rect = None

        # Charger les icônes OpenMoji (20x20)
        self.type_icons = {}
        assets_path = Path(__file__).parent.parent.parent / "assets" / "openmoji"
        for notif_type, icon_file in self.TYPE_ICONS.items():
            icon_path = assets_path / icon_file
            if icon_path.exists():
                icon = pygame.image.load(str(icon_path))
                self.type_icons[notif_type] = pygame.transform.scale(icon, (20, 20))
            else:
                print(f"Warning: Icon not found: {icon_path}")

    def toggle(self):
        """Toggle la visibilité du panneau"""
        self.visible = not self.visible
        if self.visible:
            self.scroll_offset = 0

    def show(self):
        """Affiche le panneau"""
        self.visible = True
        self.scroll_offset = 0

    def hide(self):
        """Cache le panneau"""
        self.visible = False

    def handle_event(self, event: pygame.event.Event, notification_manager) -> Optional[Notification]:
        """
        Gère les événements du panneau

        Returns:
            Notification cliquée ou None
        """
        if not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # Bouton fermer
            if self.close_button_rect and self.close_button_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return None

            # Bouton clear all
            if self.clear_all_button_rect and self.clear_all_button_rect.collidepoint(mouse_x, mouse_y):
                notification_manager.mark_all_read()
                return None

            # Scroll buttons
            if self.scroll_up_rect and self.scroll_up_rect.collidepoint(mouse_x, mouse_y):
                self.scroll_offset = max(0, self.scroll_offset - 50)
                return None

            if self.scroll_down_rect and self.scroll_down_rect.collidepoint(mouse_x, mouse_y):
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
                return None

            # Notifications cliquables
            for notif_id, rect in self.notification_rects.items():
                if rect.collidepoint(mouse_x, mouse_y):
                    # Trouver la notification
                    for notif in notification_manager.notifications:
                        if notif.id == notif_id:
                            # Marquer comme lue
                            notification_manager.mark_read(notif_id)
                            # Si cliquable, retourner pour action
                            if notif.clickable:
                                return notif
                            break
                    return None

        elif event.type == pygame.MOUSEWHEEL:
            if self.visible:
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y * 30))
                return None

        return None

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, notification_manager):
        """Dessine le panneau d'historique"""
        if not self.visible:
            return

        screen_w, screen_h = screen.get_size()

        # Modal dimensions
        modal_w = 600
        modal_h = 500
        modal_x = (screen_w - modal_w) // 2
        modal_y = (screen_h - modal_h) // 2

        # Overlay semi-transparent
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Modal background
        modal_bg = pygame.Surface((modal_w, modal_h))
        modal_bg.fill((40, 40, 50))
        pygame.draw.rect(modal_bg, (200, 200, 200), (0, 0, modal_w, modal_h), 2)
        screen.blit(modal_bg, (modal_x, modal_y))

        y_offset = modal_y + 20

        # Title
        title_font = pygame.font.Font(None, 36)
        unread_count = notification_manager.get_unread_count()
        title_text = f"NOTIFICATIONS ({unread_count} non lues)"
        title = title_font.render(title_text, True, (255, 255, 255))
        screen.blit(title, (modal_x + (modal_w - title.get_width()) // 2, y_offset))

        # Close button (X)
        close_x = modal_x + modal_w - 35
        close_y = modal_y + 10
        self.close_button_rect = pygame.Rect(close_x, close_y, 25, 25)
        pygame.draw.rect(screen, (150, 50, 50), self.close_button_rect)
        pygame.draw.rect(screen, (200, 100, 100), self.close_button_rect, 2)
        close_text = font.render("X", True, (255, 255, 255))
        screen.blit(close_text, (close_x + 7, close_y + 3))

        y_offset += 50

        # Clear all button
        clear_btn_w = 150
        clear_btn_h = 30
        clear_btn_x = modal_x + modal_w - clear_btn_w - 20
        clear_btn_y = y_offset
        self.clear_all_button_rect = pygame.Rect(clear_btn_x, clear_btn_y, clear_btn_w, clear_btn_h)
        pygame.draw.rect(screen, (80, 80, 100), self.clear_all_button_rect)
        pygame.draw.rect(screen, (120, 120, 140), self.clear_all_button_rect, 2)
        clear_text = font.render("Tout marquer lu", True, (255, 255, 255))
        screen.blit(clear_text, (clear_btn_x + 10, clear_btn_y + 7))

        y_offset += 40

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 15

        # Scrollable area
        scroll_area_y = y_offset
        scroll_area_h = modal_h - (y_offset - modal_y) - 20

        # Get notifications
        notifications = notification_manager.get_history()
        content_y = scroll_area_y - self.scroll_offset

        # Calculate max scroll
        total_content_height = len(notifications) * 75
        self.max_scroll = max(0, total_content_height - scroll_area_h)

        # Clear notification rects
        self.notification_rects = {}

        # Draw notifications
        for notif in notifications:
            # Skip if outside visible area
            if content_y + 70 < scroll_area_y or content_y > scroll_area_y + scroll_area_h:
                content_y += 75
                continue

            # Notification box
            notif_rect = pygame.Rect(modal_x + 20, content_y, modal_w - 40, 65)
            self.notification_rects[notif.id] = notif_rect

            # Background color
            if not notif.read:
                bg_color = (60, 60, 80)  # Plus sombre si non lu
                border_color = notif.type.value[1]  # Couleur du type
            else:
                bg_color = (50, 50, 60)  # Gris foncé si lu
                border_color = (100, 100, 110)

            pygame.draw.rect(screen, bg_color, notif_rect, border_radius=5)
            pygame.draw.rect(screen, border_color, notif_rect, 2, border_radius=5)

            # Icône OpenMoji
            icon = self.type_icons.get(notif.type)
            if icon:
                screen.blit(icon, (notif_rect.x + 10, notif_rect.y + 23))

            # Message
            message_color = (255, 255, 255) if not notif.read else (180, 180, 180)

            # Découper message si trop long (max 400px)
            message = notif.message
            max_width = 400
            words = message.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                test_render = font.render(test_line, True, message_color)
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
            if len(notif.message.split()) > len(' '.join(lines).split()):
                lines[-1] += "..."

            # Afficher lignes
            for i, line in enumerate(lines):
                text_render = font.render(line, True, message_color)
                screen.blit(text_render, (notif_rect.x + 40, notif_rect.y + 10 + i * 18))

            # Timestamp (en bas à droite)
            timestamp_text = f"Day {notif.game_day} - {notif.timestamp}"
            small_font = pygame.font.Font(None, 16)
            timestamp_render = small_font.render(timestamp_text, True, (150, 150, 150))
            screen.blit(timestamp_render, (notif_rect.right - 120, notif_rect.bottom - 18))

            # Indicateur cliquable
            if notif.clickable:
                click_icon = small_font.render("🔗", True, (100, 200, 255))
                screen.blit(click_icon, (notif_rect.right - 25, notif_rect.y + 10))

            content_y += 75

        # Scroll indicators
        if self.max_scroll > 0:
            # Up arrow
            if self.scroll_offset > 0:
                self.scroll_up_rect = pygame.Rect(modal_x + modal_w - 40, scroll_area_y + 10, 30, 30)
                pygame.draw.rect(screen, (100, 100, 120), self.scroll_up_rect)
                pygame.draw.rect(screen, (200, 200, 200), self.scroll_up_rect, 1)
                up_text = font.render("▲", True, (255, 255, 255))
                screen.blit(up_text, (self.scroll_up_rect.x + 8, self.scroll_up_rect.y + 5))

            # Down arrow
            if self.scroll_offset < self.max_scroll:
                self.scroll_down_rect = pygame.Rect(modal_x + modal_w - 40,
                                                     scroll_area_y + scroll_area_h - 40, 30, 30)
                pygame.draw.rect(screen, (100, 100, 120), self.scroll_down_rect)
                pygame.draw.rect(screen, (200, 200, 200), self.scroll_down_rect, 1)
                down_text = font.render("▼", True, (255, 255, 255))
                screen.blit(down_text, (self.scroll_down_rect.x + 8, self.scroll_down_rect.y + 5))
