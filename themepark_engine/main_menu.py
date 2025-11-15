"""
Main Menu for OpenPark
Displays title and three main buttons with modals for loading/new game
"""

import pygame
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from . import assets


class SaveSlot:
    """Represents a save file with metadata"""

    def __init__(self, save_path: Path):
        self.save_path = save_path
        self.filename = save_path.name

        # Metadata
        self.park_name = ""
        self.game_day = 0
        self.cash = 0
        self.guest_count = 0
        self.save_date = ""
        self.game_year = 2025
        self.game_month = 1

        self._load_metadata()

    def _load_metadata(self):
        """Load metadata from save file"""
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                self.park_name = data.get('park_name', 'Parc sans nom')
                self.game_day = data.get('game_day', 0)
                self.cash = data.get('cash', 0)
                self.guest_count = len(data.get('guests', []))
                self.game_year = data.get('game_year', 2025)
                self.game_month = data.get('game_month', 1)

                # Parse save date
                metadata = data.get('metadata', {})
                save_date_str = metadata.get('save_date', '')
                if save_date_str:
                    try:
                        dt = datetime.fromisoformat(save_date_str)
                        self.save_date = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        self.save_date = save_date_str
        except Exception as e:
            print(f"Error loading metadata for {self.filename}: {e}")


class MainMenu:
    """Main menu screen for OpenPark"""

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.input_font = pygame.font.Font(None, 32)

        # Save directory
        self.save_dir = Path("saves")
        self.save_dir.mkdir(exist_ok=True)

        # Menu state
        self.hovered_button = None
        self.show_load_modal = False
        self.show_new_game_modal = False
        self.save_slots = []
        self.selected_save_index = None
        self.park_name_input = ""
        self.input_active = False

        # Colors
        self.bg_color_top = (26, 26, 46)
        self.bg_color_bottom = (22, 33, 62)
        self.button_color = (78, 204, 163)
        self.button_hover_color = (98, 224, 183)
        self.quit_button_color = (200, 80, 80)
        self.quit_button_hover_color = (220, 100, 100)
        self.modal_bg_color = (40, 40, 55)
        self.modal_border_color = (100, 100, 120)

        # Load menu music
        self.music_loaded = False
        self._load_menu_music()

    def _load_menu_music(self):
        """Load and play menu background music"""
        try:
            music_path = Path("assets/music/menu_theme.mp3")
            if music_path.exists():
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
                self.music_loaded = True
        except Exception as e:
            print(f"Could not load menu music: {e}")
            self.music_loaded = False

    def stop_music(self):
        """Stop menu music when leaving menu"""
        if self.music_loaded:
            pygame.mixer.music.stop()

    def _load_save_list(self):
        """Load list of available save files"""
        self.save_slots = []
        for save_file in self.save_dir.glob('*.json'):
            self.save_slots.append(SaveSlot(save_file))
        # Sort by most recent
        self.save_slots.sort(key=lambda s: s.save_date, reverse=True)

    def handle_event(self, event: pygame.event.Event) -> Optional[Dict[str, Any]]:
        """
        Handle pygame events

        Returns:
            Dictionary with action if menu choice made, None otherwise
        """
        # Handle load modal
        if self.show_load_modal:
            return self._handle_load_modal_event(event)

        # Handle new game modal
        if self.show_new_game_modal:
            return self._handle_new_game_modal_event(event)

        # Handle main menu
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check button clicks
            load_rect = self._get_load_button_rect()
            if load_rect.collidepoint(mouse_pos):
                self._load_save_list()
                self.show_load_modal = True
                return None

            new_game_rect = self._get_new_game_button_rect()
            if new_game_rect.collidepoint(mouse_pos):
                self.park_name_input = ""
                self.input_active = True
                self.show_new_game_modal = True
                return None

            quit_rect = self._get_quit_button_rect()
            if quit_rect.collidepoint(mouse_pos):
                return {"action": "quit"}

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos

            # Update hovered button
            self.hovered_button = None
            if self._get_load_button_rect().collidepoint(mouse_pos):
                self.hovered_button = "load"
            elif self._get_new_game_button_rect().collidepoint(mouse_pos):
                self.hovered_button = "new_game"
            elif self._get_quit_button_rect().collidepoint(mouse_pos):
                self.hovered_button = "quit"

        return None

    def _handle_load_modal_event(self, event: pygame.event.Event) -> Optional[Dict[str, Any]]:
        """Handle events in load game modal"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check close button
            close_rect = self._get_modal_close_button_rect()
            if close_rect.collidepoint(mouse_pos):
                self.show_load_modal = False
                return None

            # Check save slot clicks
            modal_x, modal_y = self._get_modal_position()
            for i, slot in enumerate(self.save_slots):
                slot_rect = self._get_save_slot_rect(i, modal_x, modal_y)
                if slot_rect.collidepoint(mouse_pos):
                    self.show_load_modal = False
                    return {"action": "load", "save_file": slot.filename}

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_load_modal = False

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            modal_x, modal_y = self._get_modal_position()

            # Check hover on save slots
            self.selected_save_index = None
            for i, slot in enumerate(self.save_slots):
                slot_rect = self._get_save_slot_rect(i, modal_x, modal_y)
                if slot_rect.collidepoint(mouse_pos):
                    self.selected_save_index = i
                    break

        return None

    def _handle_new_game_modal_event(self, event: pygame.event.Event) -> Optional[Dict[str, Any]]:
        """Handle events in new game modal"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check close button
            close_rect = self._get_modal_close_button_rect()
            if close_rect.collidepoint(mouse_pos):
                self.show_new_game_modal = False
                self.input_active = False
                return None

            # Check start button
            start_rect = self._get_start_button_rect()
            if start_rect.collidepoint(mouse_pos) and self.park_name_input.strip():
                park_name = self.park_name_input.strip()
                # Create save filename from park name
                safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in park_name)
                safe_filename = safe_filename.replace(' ', '_').lower()
                save_file = f"{safe_filename}.json"

                self.show_new_game_modal = False
                self.input_active = False
                return {"action": "new_game", "park_name": park_name, "save_file": save_file}

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_new_game_modal = False
                self.input_active = False
            elif event.key == pygame.K_RETURN and self.park_name_input.strip():
                # Same as clicking start button
                park_name = self.park_name_input.strip()
                safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in park_name)
                safe_filename = safe_filename.replace(' ', '_').lower()
                save_file = f"{safe_filename}.json"

                self.show_new_game_modal = False
                self.input_active = False
                return {"action": "new_game", "park_name": park_name, "save_file": save_file}
            elif event.key == pygame.K_BACKSPACE:
                self.park_name_input = self.park_name_input[:-1]
            elif event.unicode and len(self.park_name_input) < 30:
                self.park_name_input += event.unicode

        return None

    def _get_modal_position(self) -> tuple:
        """Get modal position (centered)"""
        screen_w, screen_h = self.screen.get_size()
        modal_w, modal_h = 700, 500
        modal_x = (screen_w - modal_w) // 2
        modal_y = (screen_h - modal_h) // 2
        return modal_x, modal_y

    def _get_modal_close_button_rect(self) -> pygame.Rect:
        """Get close button rect for modals"""
        modal_x, modal_y = self._get_modal_position()
        return pygame.Rect(modal_x + 650, modal_y + 10, 40, 40)

    def _get_save_slot_rect(self, index: int, modal_x: int, modal_y: int) -> pygame.Rect:
        """Get rectangle for a save slot in load modal"""
        slot_width = 660
        slot_height = 80
        slot_x = modal_x + 20
        slot_y = modal_y + 80 + index * (slot_height + 10)
        return pygame.Rect(slot_x, slot_y, slot_width, slot_height)

    def _get_start_button_rect(self) -> pygame.Rect:
        """Get start button rect for new game modal"""
        modal_x, modal_y = self._get_modal_position()
        return pygame.Rect(modal_x + 250, modal_y + 350, 200, 50)

    def _get_load_button_rect(self) -> pygame.Rect:
        """Get load game button rect"""
        screen_w, screen_h = self.screen.get_size()
        button_width = 300
        button_height = 60
        button_x = (screen_w - button_width) // 2
        button_y = screen_h // 2 - 20
        return pygame.Rect(button_x, button_y, button_width, button_height)

    def _get_new_game_button_rect(self) -> pygame.Rect:
        """Get new game button rect"""
        screen_w, screen_h = self.screen.get_size()
        button_width = 300
        button_height = 60
        button_x = (screen_w - button_width) // 2
        button_y = screen_h // 2 + 60
        return pygame.Rect(button_x, button_y, button_width, button_height)

    def _get_quit_button_rect(self) -> pygame.Rect:
        """Get quit button rect"""
        screen_w, screen_h = self.screen.get_size()
        button_width = 300
        button_height = 60
        button_x = (screen_w - button_width) // 2
        button_y = screen_h // 2 + 140
        return pygame.Rect(button_x, button_y, button_width, button_height)

    def draw(self):
        """Draw the main menu"""
        screen_w, screen_h = self.screen.get_size()

        # Draw gradient background
        self._draw_gradient_background()

        # Draw title
        title_text = "OPENPARK"
        title_surf = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_w // 2, 120))
        self.screen.blit(title_surf, title_rect)

        # Draw subtitle
        subtitle_text = "Theme Park Simulation"
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(screen_w // 2, 180))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Draw emoji decorations
        try:
            ferris_sprite = assets.load_image("1F3A1.png")
            carousel_sprite = assets.load_image("1F3A0.png")

            ferris_scaled = pygame.transform.scale(ferris_sprite, (64, 64))
            carousel_scaled = pygame.transform.scale(carousel_sprite, (64, 64))

            self.screen.blit(ferris_scaled, (screen_w // 2 - 250, 100))
            self.screen.blit(carousel_scaled, (screen_w // 2 + 186, 100))
        except:
            pass

        # Draw main menu buttons
        self._draw_load_button()
        self._draw_new_game_button()
        self._draw_quit_button()

        # Draw version
        version_text = "v0.8.3-alpha"
        if self.music_loaded:
            version_text += " ♫"
        version_surf = self.font.render(version_text, True, (150, 150, 150))
        version_rect = version_surf.get_rect(bottomright=(screen_w - 20, screen_h - 10))
        self.screen.blit(version_surf, version_rect)

        # Draw modals on top
        if self.show_load_modal:
            self._draw_load_modal()
        elif self.show_new_game_modal:
            self._draw_new_game_modal()

    def _draw_gradient_background(self):
        """Draw gradient background"""
        screen_w, screen_h = self.screen.get_size()
        for y in range(screen_h):
            ratio = y / screen_h
            r = int(self.bg_color_top[0] + (self.bg_color_bottom[0] - self.bg_color_top[0]) * ratio)
            g = int(self.bg_color_top[1] + (self.bg_color_bottom[1] - self.bg_color_top[1]) * ratio)
            b = int(self.bg_color_top[2] + (self.bg_color_bottom[2] - self.bg_color_top[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (screen_w, y))

    def _draw_load_button(self):
        """Draw load game button"""
        button_rect = self._get_load_button_rect()
        color = self.button_hover_color if self.hovered_button == "load" else self.button_color

        pygame.draw.rect(self.screen, color, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 3, border_radius=10)

        text_surf = self.input_font.render("CHARGER UNE PARTIE", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_new_game_button(self):
        """Draw new game button"""
        button_rect = self._get_new_game_button_rect()
        color = self.button_hover_color if self.hovered_button == "new_game" else self.button_color

        pygame.draw.rect(self.screen, color, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 3, border_radius=10)

        text_surf = self.input_font.render("NOUVELLE PARTIE", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_quit_button(self):
        """Draw quit button"""
        button_rect = self._get_quit_button_rect()
        color = self.quit_button_hover_color if self.hovered_button == "quit" else self.quit_button_color

        pygame.draw.rect(self.screen, color, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 3, border_radius=10)

        text_surf = self.input_font.render("QUITTER", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_load_modal(self):
        """Draw load game modal"""
        modal_x, modal_y = self._get_modal_position()
        modal_w, modal_h = 700, 500

        # Semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Modal background
        pygame.draw.rect(self.screen, self.modal_bg_color, (modal_x, modal_y, modal_w, modal_h), border_radius=10)
        pygame.draw.rect(self.screen, self.modal_border_color, (modal_x, modal_y, modal_w, modal_h), 3, border_radius=10)

        # Title
        title_surf = self.subtitle_font.render("Charger une partie", True, (255, 215, 0))
        self.screen.blit(title_surf, (modal_x + 20, modal_y + 20))

        # Close button
        close_rect = self._get_modal_close_button_rect()
        pygame.draw.rect(self.screen, (200, 80, 80), close_rect, border_radius=5)
        close_text = self.font.render("X", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)

        # Save slots
        if not self.save_slots:
            no_saves_text = self.font.render("Aucune sauvegarde disponible", True, (150, 150, 150))
            no_saves_rect = no_saves_text.get_rect(center=(modal_x + modal_w // 2, modal_y + modal_h // 2))
            self.screen.blit(no_saves_text, no_saves_rect)
        else:
            for i, slot in enumerate(self.save_slots):
                if i >= 4:  # Max 4 visible saves
                    break
                self._draw_save_slot(i, slot, modal_x, modal_y)

    def _draw_save_slot(self, index: int, slot: SaveSlot, modal_x: int, modal_y: int):
        """Draw a single save slot"""
        slot_rect = self._get_save_slot_rect(index, modal_x, modal_y)

        # Background color
        if self.selected_save_index == index:
            color = (70, 70, 90)
        else:
            color = (50, 50, 65)

        pygame.draw.rect(self.screen, color, slot_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 120), slot_rect, 2, border_radius=8)

        # Park name
        name_surf = self.font.render(slot.park_name, True, (255, 255, 255))
        self.screen.blit(name_surf, (slot_rect.x + 15, slot_rect.y + 10))

        # Game info
        month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                      "Jui", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        month_name = month_names[slot.game_month - 1] if 1 <= slot.game_month <= 12 else "???"
        info_text = f"{month_name} {slot.game_year} | ${slot.cash:,.0f} | {slot.guest_count} visiteurs"
        info_surf = self.font.render(info_text, True, (200, 200, 200))
        self.screen.blit(info_surf, (slot_rect.x + 15, slot_rect.y + 35))

        # Save date
        date_text = f"Sauvegardé: {slot.save_date}"
        date_surf = self.font.render(date_text, True, (150, 150, 170))
        self.screen.blit(date_surf, (slot_rect.x + 15, slot_rect.y + 58))

    def _draw_new_game_modal(self):
        """Draw new game modal with park name input"""
        modal_x, modal_y = self._get_modal_position()
        modal_w, modal_h = 700, 500

        # Semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Modal background
        pygame.draw.rect(self.screen, self.modal_bg_color, (modal_x, modal_y, modal_w, modal_h), border_radius=10)
        pygame.draw.rect(self.screen, self.modal_border_color, (modal_x, modal_y, modal_w, modal_h), 3, border_radius=10)

        # Title
        title_surf = self.subtitle_font.render("Nouvelle partie", True, (255, 215, 0))
        self.screen.blit(title_surf, (modal_x + 20, modal_y + 20))

        # Close button
        close_rect = self._get_modal_close_button_rect()
        pygame.draw.rect(self.screen, (200, 80, 80), close_rect, border_radius=5)
        close_text = self.font.render("X", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)

        # Instructions
        instruction_surf = self.font.render("Entrez le nom de votre parc:", True, (200, 200, 200))
        self.screen.blit(instruction_surf, (modal_x + 50, modal_y + 120))

        # Input box
        input_rect = pygame.Rect(modal_x + 50, modal_y + 180, 600, 60)
        pygame.draw.rect(self.screen, (60, 60, 75), input_rect, border_radius=8)
        pygame.draw.rect(self.screen, (120, 120, 140), input_rect, 2, border_radius=8)

        # Input text
        display_text = self.park_name_input
        if self.input_active and int(pygame.time.get_ticks() / 500) % 2:
            display_text += "|"

        input_surf = self.input_font.render(display_text, True, (255, 255, 255))
        input_text_rect = input_surf.get_rect(midleft=(input_rect.x + 20, input_rect.centery))
        self.screen.blit(input_surf, input_text_rect)

        # Start button
        start_rect = self._get_start_button_rect()
        can_start = len(self.park_name_input.strip()) > 0
        start_color = self.button_color if can_start else (80, 80, 80)

        pygame.draw.rect(self.screen, start_color, start_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 3, border_radius=10)

        start_text_surf = self.input_font.render("COMMENCER", True, (255, 255, 255))
        start_text_rect = start_text_surf.get_rect(center=start_rect.center)
        self.screen.blit(start_text_surf, start_text_rect)
