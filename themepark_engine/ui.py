
import pygame

class NegotiationModal:
    """Modal panel for salary negotiation with employees"""

    def __init__(self, font, large_font=None):
        self.font = font
        self.large_font = large_font or font
        self.visible = False
        self.negotiation = None  # NegotiationState object
        self.employee_type = None
        self.employee_count = 0
        self.counter_offer = 0
        self.slider_dragging = False

        # UI elements rects
        self.accept_button = None
        self.reject_button = None
        self.counter_button = None
        self.slider_rect = None
        self.slider_handle_rect = None

    def show(self, negotiation, employee_type, employee_count):
        """Show the negotiation modal"""
        self.visible = True
        self.negotiation = negotiation
        self.employee_type = employee_type
        self.employee_count = employee_count
        # Initialize counter offer to the demanded salary (player can negotiate down from there)
        self.counter_offer = negotiation.demanded_salary

    def hide(self):
        """Hide the negotiation modal"""
        self.visible = False
        self.negotiation = None
        self.employee_type = None
        self.slider_dragging = False

    def handle_event(self, event):
        """Handle mouse events for the modal"""
        if not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check button clicks
            if self.accept_button and self.accept_button.collidepoint(mouse_pos):
                return ('accept', self.negotiation.demanded_salary)
            elif self.reject_button and self.reject_button.collidepoint(mouse_pos):
                return ('reject', 0)
            elif self.counter_button and self.counter_button.collidepoint(mouse_pos):
                return ('counter', self.counter_offer)

            # Check slider click
            if self.slider_rect and self.slider_rect.collidepoint(mouse_pos):
                self.slider_dragging = True
                self._update_slider_from_mouse(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.slider_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.slider_dragging:
                self._update_slider_from_mouse(event.pos)

        return None

    def _update_slider_from_mouse(self, mouse_pos):
        """Update counter offer based on slider position"""
        if not self.slider_rect or not self.negotiation:
            return

        # Calculate position along slider
        x = mouse_pos[0]
        slider_start = self.slider_rect.x
        slider_width = self.slider_rect.width

        # Clamp to slider bounds
        x = max(slider_start, min(slider_start + slider_width, x))

        # Calculate value (from current salary to demanded + 20%)
        ratio = (x - slider_start) / slider_width
        min_value = self.negotiation.current_salary
        max_value = int(self.negotiation.demanded_salary * 1.2)
        old_offer = self.counter_offer
        self.counter_offer = int(min_value + ratio * (max_value - min_value))

        # Debug: Log when counter offer changes significantly
        if abs(self.counter_offer - old_offer) > 1:
            from .debug import DebugConfig
            DebugConfig.log('engine', f"Slider moved: ${old_offer} -> ${self.counter_offer} (ratio={ratio:.2f})")

    def draw(self, screen):
        """Draw the negotiation modal"""
        if not self.visible or not self.negotiation:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Modal panel
        panel_width = 600
        panel_height = 450
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 50), panel_rect)
        pygame.draw.rect(screen, (200, 200, 100), panel_rect, 3)

        # Title
        from .salary_negotiation import NegotiationStage
        stage_names = {
            NegotiationStage.FIRST_PROPOSAL: "Négociation Salariale - Première Proposition",
            NegotiationStage.SECOND_PROPOSAL: "Négociation Salariale - Deuxième Proposition",
            NegotiationStage.THIRD_PROPOSAL: "Négociation Salariale - Dernière Proposition",
            NegotiationStage.STRIKE: "GRÈVE EN COURS !",
            NegotiationStage.FINAL_ULTIMATUM: "ULTIMATUM FINAL !"
        }
        title = stage_names.get(self.negotiation.current_stage, "Négociation Salariale")
        title_surf = self.large_font.render(title, True, (255, 255, 100))
        title_rect = title_surf.get_rect(centerx=panel_x + panel_width // 2, top=panel_y + 20)
        screen.blit(title_surf, title_rect)

        # Employee info
        y = panel_y + 70
        employee_type_display = {
            'engineer': 'Ingénieurs',
            'maintenance': 'Agents de Maintenance',
            'security': 'Gardes de Sécurité',
            'mascot': 'Mascottes'
        }
        emp_text = f"{employee_type_display.get(self.employee_type, self.employee_type)}: {self.employee_count} employés"
        emp_surf = self.font.render(emp_text, True, (255, 255, 255))
        screen.blit(emp_surf, (panel_x + 40, y))

        # Current stage info
        y += 35
        if self.negotiation.current_stage == NegotiationStage.FIRST_PROPOSAL:
            stage_text = "Les employés demandent une augmentation de salaire."
        elif self.negotiation.current_stage == NegotiationStage.SECOND_PROPOSAL:
            stage_text = "Offre refusée ! Efficacité -35%. Nouvelle proposition ?"
        elif self.negotiation.current_stage == NegotiationStage.THIRD_PROPOSAL:
            stage_text = "Offre refusée ! Efficacité -75%. Dernière chance !"
        elif self.negotiation.current_stage == NegotiationStage.STRIKE:
            stage_text = "GRÈVE ! Les employés ne travaillent plus. Acceptez maintenant !"
        else:  # FINAL_ULTIMATUM
            stage_text = "ULTIMATUM ! Acceptez ou tous les employés démissionnent !"

        stage_surf = self.font.render(stage_text, True, (255, 200, 200))
        screen.blit(stage_surf, (panel_x + 40, y))

        # Salary info
        y += 50
        current_text = f"Salaire actuel:  ${self.negotiation.current_salary}/jour"
        current_surf = self.font.render(current_text, True, (200, 200, 200))
        screen.blit(current_surf, (panel_x + 40, y))

        y += 30
        demanded_text = f"Salaire demandé: ${self.negotiation.demanded_salary}/jour"
        demanded_surf = self.font.render(demanded_text, True, (255, 255, 100))
        screen.blit(demanded_surf, (panel_x + 40, y))

        y += 30
        increase_pct = int(((self.negotiation.demanded_salary - self.negotiation.current_salary) / self.negotiation.current_salary) * 100)
        increase_text = f"Augmentation:    +{increase_pct}%"
        increase_surf = self.font.render(increase_text, True, (255, 150, 150))
        screen.blit(increase_surf, (panel_x + 40, y))

        # Counter offer slider
        y += 60
        slider_label = self.font.render("Contre-proposition:", True, (255, 255, 255))
        screen.blit(slider_label, (panel_x + 40, y))

        y += 30
        slider_width = 520
        slider_height = 10
        self.slider_rect = pygame.Rect(panel_x + 40, y, slider_width, slider_height)
        pygame.draw.rect(screen, (80, 80, 90), self.slider_rect)
        pygame.draw.rect(screen, (150, 150, 160), self.slider_rect, 1)

        # Slider handle
        min_value = self.negotiation.current_salary
        max_value = int(self.negotiation.demanded_salary * 1.2)
        ratio = (self.counter_offer - min_value) / (max_value - min_value)
        handle_x = int(self.slider_rect.x + ratio * self.slider_rect.width)
        self.slider_handle_rect = pygame.Rect(handle_x - 8, self.slider_rect.y - 5, 16, 20)
        pygame.draw.rect(screen, (200, 200, 100), self.slider_handle_rect)
        pygame.draw.rect(screen, (255, 255, 150), self.slider_handle_rect, 2)

        # Counter offer value
        counter_text = f"${self.counter_offer}/jour"
        counter_surf = self.font.render(counter_text, True, (200, 255, 200))
        counter_rect = counter_surf.get_rect(centerx=panel_x + panel_width // 2, top=y + 25)
        screen.blit(counter_surf, counter_rect)

        # Acceptance threshold indicator (50% of the demanded INCREASE)
        demanded_increase = self.negotiation.demanded_salary - self.negotiation.current_salary
        min_acceptable_increase = demanded_increase * 0.5
        acceptance_threshold = self.negotiation.current_salary + min_acceptable_increase

        if self.counter_offer >= acceptance_threshold:
            threshold_text = "✓ Probablement accepté"
            threshold_color = (100, 255, 100)
        else:
            threshold_text = "✗ Probablement refusé"
            threshold_color = (255, 100, 100)

        # Debug: Show exact threshold value
        threshold_debug = f"(seuil: ${int(acceptance_threshold)})"
        threshold_surf = self.font.render(f"{threshold_text} {threshold_debug}", True, threshold_color)
        threshold_rect = threshold_surf.get_rect(centerx=panel_x + panel_width // 2, top=y + 50)
        screen.blit(threshold_surf, threshold_rect)

        # Buttons
        button_y = panel_y + panel_height - 70
        button_width = 150
        button_height = 40
        button_spacing = 20

        # Accept button
        accept_x = panel_x + (panel_width - button_width * 3 - button_spacing * 2) // 2
        self.accept_button = pygame.Rect(accept_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, (60, 120, 60), self.accept_button)
        pygame.draw.rect(screen, (100, 200, 100), self.accept_button, 2)
        accept_text = self.font.render("Accepter", True, (255, 255, 255))
        accept_text_rect = accept_text.get_rect(center=self.accept_button.center)
        screen.blit(accept_text, accept_text_rect)

        # Counter button
        counter_x = accept_x + button_width + button_spacing
        self.counter_button = pygame.Rect(counter_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, (100, 100, 60), self.counter_button)
        pygame.draw.rect(screen, (200, 200, 100), self.counter_button, 2)
        counter_btn_text = self.font.render("Proposer", True, (255, 255, 255))
        counter_btn_text_rect = counter_btn_text.get_rect(center=self.counter_button.center)
        screen.blit(counter_btn_text, counter_btn_text_rect)

        # Reject button
        reject_x = counter_x + button_width + button_spacing
        self.reject_button = pygame.Rect(reject_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, (120, 60, 60), self.reject_button)
        pygame.draw.rect(screen, (200, 100, 100), self.reject_button, 2)
        reject_text = self.font.render("Refuser", True, (255, 255, 255))
        reject_text_rect = reject_text.get_rect(center=self.reject_button.center)
        screen.blit(reject_text, reject_text_rect)


class Toolbar:
    def __init__(self, font, ride_defs=None, shop_defs=None, employee_defs=None, bin_defs=None, restroom_defs=None, decoration_defs=None):
        self.font = font
        self.ride_defs = ride_defs or {}
        self.shop_defs = shop_defs or {}
        self.employee_defs = employee_defs or {}
        self.bin_defs = bin_defs or {}
        self.restroom_defs = restroom_defs or {}
        self.decoration_defs = decoration_defs or {}
        self._load_toolbar_icons()
        self._build_groups()
        self.active = 'walk_path'
        self.hovered_button = None
        self.expanded_group = None  # Groupe actuellement ouvert
        self.hovered_subitem = None
    
    def _load_toolbar_icons(self):
        """Load icons for toolbar buttons (53x53px - agrandis d'un tiers)"""
        from . import assets
        icon_size = (53, 53)
        self.toolbar_icons = {}

        icon_map = {
            'paths': '1F6E4.png',  # Railway track (better for paths)
            'rides': 'rides/1F3A2.png',  # Roller coaster
            'shops': 'shops/1F381.png',  # Gift/shop
            'employees': 'employees/1F477.png',  # Engineer
            'facilities': 'infrastructure/1F6BB.png',  # Restroom
            'economy': '1F4B0.png',  # Money bag (economy)
            'tools': 'infrastructure/1F6AA.png',  # Door (tools)
        }

        for name, path in icon_map.items():
            try:
                sprite = assets.load_image(path)
                scaled = pygame.transform.smoothscale(sprite, icon_size)
                self.toolbar_icons[name] = scaled
            except:
                # Fallback to colored rectangle
                fallback = pygame.Surface(icon_size, pygame.SRCALPHA)
                fallback.fill((100, 100, 100))
                self.toolbar_icons[name] = fallback

    def _build_groups(self):
        """Build grouped toolbar items"""
        self.groups = {
            'paths': {
                'name': 'Chemins',
                'tooltip': 'Chemins - Chemins piétons et files d\'attente',
                'items': [
                    ('Walk Path', 'walk_path', 0),  # Prix gratuit
                    ('Queue Path', 'queue_path', 0)  # Prix gratuit
                ]
            },
            'rides': {
                'name': 'Attractions',
                'tooltip': 'Attractions - Manèges et attractions',
                'items': []
            },
            'shops': {
                'name': 'Boutiques',
                'tooltip': 'Boutiques - Magasins de nourriture et cadeaux',
                'items': []
            },
            'employees': {
                'name': 'Employés',
                'tooltip': 'Employés - Personnel du parc',
                'items': []
            },
            'facilities': {
                'name': 'Installations',
                'tooltip': 'Installations - Toilettes et poubelles',
                'items': []
            },
            'economy': {
                'name': 'Économie',
                'tooltip': 'Économie - Gestion financière du parc',
                'items': [
                    ('Prix d\'entrée', 'entrance_fee_config', 0)
                ]
            },
            'tools': {
                'name': 'Outils',
                'tooltip': 'Outils - Configuration et debug',
                'items': [
                    ('Debug', 'debug_toggle', 0),
                    ('Sauvegarder', 'save_game', 0),
                    ('Charger', 'load_game', 0),
                    ('Quitter', 'quit_game', 0)
                ]
            }
        }
        
        # Add rides dynamically
        for ride_id, ride_def in self.ride_defs.items():
            self.groups['rides']['items'].append((ride_def.name, ride_id, ride_def.build_cost))
        
        # Add shops dynamically  
        for shop_id, shop_def in self.shop_defs.items():
            self.groups['shops']['items'].append((shop_def.name, shop_id, shop_def.build_cost))
        
        # Add employees dynamically
        for emp_id, emp_def in self.employee_defs.items():
            self.groups['employees']['items'].append((emp_def.name, emp_id, emp_def.salary))

        # Add bins, restrooms, and decorations to facilities group
        for bin_id, bin_def in self.bin_defs.items():
            self.groups['facilities']['items'].append((bin_def.name, bin_id, bin_def.cost))

        for restroom_id, restroom_def in self.restroom_defs.items():
            self.groups['facilities']['items'].append((restroom_def.name, restroom_id, restroom_def.build_cost))

        for deco_id, deco_def in self.decoration_defs.items():
            self.groups['facilities']['items'].append((deco_def.name, deco_id, deco_def.cost))
    
    def update_definitions(self, ride_defs=None, shop_defs=None, employee_defs=None):
        """Update the definitions and rebuild groups"""
        if ride_defs is not None:
            self.ride_defs = ride_defs
        if shop_defs is not None:
            self.shop_defs = shop_defs
        if employee_defs is not None:
            self.employee_defs = employee_defs
        self._build_groups()
    def draw(self, screen):
        # Position toolbar en bas de l'écran
        screen_height = screen.get_height()
        toolbar_y = screen_height - 48  # 48px de hauteur pour la toolbar
        
        # Fond de la toolbar avec dégradé
        toolbar_rect = pygame.Rect(0, toolbar_y, screen.get_width(), 48)
        pygame.draw.rect(screen, (25, 25, 30), toolbar_rect)
        pygame.draw.rect(screen, (35, 35, 40), toolbar_rect, 1)
        
        # Ombre en haut de la toolbar
        shadow_rect = pygame.Rect(0, toolbar_y - 1, screen.get_width(), 1)
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect)
        
        # Dessiner les groupes de boutons
        x = 12
        for group_id, group_data in self.groups.items():
            # Couleurs selon le groupe
            if group_id == 'paths':
                bg_color = (60, 80, 100) if self.expanded_group == group_id else (40, 50, 60)
                border_color = (100, 150, 200) if self.expanded_group == group_id else (80, 100, 120)
            elif group_id == 'rides':
                bg_color = (60, 100, 60) if self.expanded_group == group_id else (40, 60, 40)
                border_color = (100, 200, 100) if self.expanded_group == group_id else (80, 120, 80)
            elif group_id == 'shops':
                bg_color = (100, 100, 60) if self.expanded_group == group_id else (60, 60, 40)
                border_color = (200, 200, 100) if self.expanded_group == group_id else (120, 120, 80)
            elif group_id == 'economy':
                bg_color = (100, 80, 60) if self.expanded_group == group_id else (60, 50, 40)
                border_color = (200, 160, 100) if self.expanded_group == group_id else (120, 100, 80)
            else:  # tools
                bg_color = (100, 60, 60) if self.expanded_group == group_id else (60, 40, 40)
                border_color = (200, 100, 100) if self.expanded_group == group_id else (120, 80, 80)
            
            # Effet de survol
            is_hovered = self.hovered_button == group_id
            if is_hovered and self.expanded_group != group_id:
                bg_color = tuple(min(255, c + 20) for c in bg_color)
                border_color = tuple(min(255, c + 30) for c in border_color)
            
            # Dessiner le bouton du groupe (icône uniquement, agrandi d'un tiers)
            rect = pygame.Rect(x, toolbar_y + 2, 58, 44)
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, border_color, rect, 2)

            # Dessiner l'icône au centre du bouton
            if group_id in self.toolbar_icons:
                icon = self.toolbar_icons[group_id]
                icon_x = rect.centerx - 26  # Center 53px icon
                icon_y = rect.centery - 26
                screen.blit(icon, (icon_x, icon_y))

            x += 65
        
        # Dessiner le sous-menu si un groupe est ouvert
        if self.expanded_group and self.expanded_group in self.groups:
            self._draw_submenu(screen, toolbar_y)

        # Dessiner le tooltip si un bouton est survolé
        if self.hovered_button and not self.expanded_group:
            self._draw_toolbar_tooltip(screen, toolbar_y)
    
    def _draw_toolbar_tooltip(self, screen, toolbar_y):
        """Draw tooltip for toolbar buttons"""
        if self.hovered_button not in self.groups:
            return

        group_data = self.groups[self.hovered_button]
        tooltip_text = group_data.get('tooltip', group_data['name'])

        # Calculate button position
        group_index = list(self.groups.keys()).index(self.hovered_button)
        button_x = 12 + group_index * 65
        button_rect = pygame.Rect(button_x, toolbar_y + 2, 58, 44)

        # Render tooltip
        tooltip_font = pygame.font.SysFont('Arial', 12)
        tooltip_surface = tooltip_font.render(tooltip_text, True, (255, 255, 255))
        tooltip_width = tooltip_surface.get_width() + 10
        tooltip_height = tooltip_surface.get_height() + 6

        # Position tooltip above the button
        tooltip_x = button_rect.centerx - tooltip_width // 2
        tooltip_y = button_rect.top - tooltip_height - 5

        # Ensure tooltip stays on screen
        if tooltip_x + tooltip_width > screen.get_width():
            tooltip_x = screen.get_width() - tooltip_width - 5
        if tooltip_x < 5:
            tooltip_x = 5

        # Draw background
        tooltip_bg = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_bg.fill((40, 40, 40, 240))
        screen.blit(tooltip_bg, (tooltip_x, tooltip_y))

        # Draw border
        pygame.draw.rect(screen, (200, 200, 200),
                       (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 1)

        # Draw text
        screen.blit(tooltip_surface, (tooltip_x + 5, tooltip_y + 3))

    def _draw_submenu(self, screen, toolbar_y):
        """Dessiner le sous-menu avec les éléments du groupe"""
        group_data = self.groups[self.expanded_group]
        items = group_data['items']
        
        if not items:
            return
        
        # Calculer la position du sous-menu
        group_index = list(self.groups.keys()).index(self.expanded_group)
        submenu_x = 12 + group_index * 65
        submenu_y = toolbar_y - len(items) * 40 - 10  # Au-dessus de la toolbar
        
        # Fond du sous-menu
        submenu_width = 200
        submenu_height = len(items) * 40 + 10
        submenu_rect = pygame.Rect(submenu_x, submenu_y, submenu_width, submenu_height)
        
        # Couleur selon le groupe
        if self.expanded_group == 'paths':
            bg_color = (40, 50, 60)
            border_color = (80, 100, 120)
        elif self.expanded_group == 'rides':
            bg_color = (40, 60, 40)
            border_color = (80, 120, 80)
        elif self.expanded_group == 'shops':
            bg_color = (60, 60, 40)
            border_color = (120, 120, 80)
        elif self.expanded_group == 'economy':
            bg_color = (60, 50, 40)
            border_color = (120, 100, 80)
        else:  # tools
            bg_color = (60, 40, 40)
            border_color = (120, 80, 80)
        
        pygame.draw.rect(screen, bg_color, submenu_rect)
        pygame.draw.rect(screen, border_color, submenu_rect, 2)
        
        # Dessiner les éléments du sous-menu
        for i, (name, value, price) in enumerate(items):
            item_y = submenu_y + 5 + i * 40
            item_rect = pygame.Rect(submenu_x + 5, item_y, submenu_width - 10, 35)
            
            # Couleur selon l'état
            is_hovered = self.hovered_subitem == value
            is_active = self.active == value
            
            if is_active:
                item_bg = tuple(min(255, c + 40) for c in bg_color)
                item_border = tuple(min(255, c + 60) for c in border_color)
            elif is_hovered:
                item_bg = tuple(min(255, c + 20) for c in bg_color)
                item_border = tuple(min(255, c + 30) for c in border_color)
            else:
                item_bg = bg_color
                item_border = border_color
            
            pygame.draw.rect(screen, item_bg, item_rect)
            pygame.draw.rect(screen, item_border, item_rect, 1)
            
            # Texte de l'élément
            text_surface = self.font.render(name, True, (255, 255, 255))
            screen.blit(text_surface, (submenu_x + 10, item_y + 8))
            
            # Prix
            if price > 0:
                price_text = f"${price}"
                price_surface = self.font.render(price_text, True, (200, 200, 100))
                price_rect = price_surface.get_rect()
                price_rect.right = submenu_x + submenu_width - 10
                price_rect.top = item_y + 8
                screen.blit(price_surface, price_rect)
            else:
                free_text = "Gratuit"
                free_surface = self.font.render(free_text, True, (150, 255, 150))
                free_rect = free_surface.get_rect()
                free_rect.right = submenu_x + submenu_width - 10
                free_rect.top = item_y + 8
                screen.blit(free_surface, free_rect)
    
    def handle_mouse_move(self, pos, screen_height):
        """Handle mouse movement for hover effects"""
        toolbar_y = screen_height - 48
        self.hovered_button = None
        self.hovered_subitem = None
        
        # Vérifier si la souris est dans un sous-menu ouvert
        if self.expanded_group and self.expanded_group in self.groups:
            group_data = self.groups[self.expanded_group]
            items = group_data['items']
            
            if items:
                group_index = list(self.groups.keys()).index(self.expanded_group)
                submenu_x = 12 + group_index * 65
                submenu_y = toolbar_y - len(items) * 40 - 10
                submenu_width = 200

                # Vérifier si la souris est dans le sous-menu
                if (submenu_x <= pos[0] <= submenu_x + submenu_width and
                    submenu_y <= pos[1] <= submenu_y + len(items) * 40 + 10):

                    # Trouver l'élément survolé
                    for i, (name, value, price) in enumerate(items):
                        item_y = submenu_y + 5 + i * 40
                        item_rect = pygame.Rect(submenu_x + 5, item_y, submenu_width - 10, 35)
                        if item_rect.collidepoint(pos):
                            self.hovered_subitem = value
                            return

        # Vérifier les boutons de groupe
        x = 12
        for group_id, group_data in self.groups.items():
            rect = pygame.Rect(x, toolbar_y + 2, 58, 44)
            if rect.collidepoint(pos):
                self.hovered_button = group_id
                break
            x += 65
    
    def handle_click(self, pos, screen_height):
        # Position toolbar en bas de l'écran
        toolbar_y = screen_height - 48
        
        # Vérifier si le clic est dans un sous-menu ouvert
        if self.expanded_group and self.expanded_group in self.groups:
            group_data = self.groups[self.expanded_group]
            items = group_data['items']

            if items:
                group_index = list(self.groups.keys()).index(self.expanded_group)
                submenu_x = 12 + group_index * 65
                submenu_y = toolbar_y - len(items) * 40 - 10
                submenu_width = 200

                # Vérifier si le clic est dans le sous-menu
                if (submenu_x <= pos[0] <= submenu_x + submenu_width and
                    submenu_y <= pos[1] <= submenu_y + len(items) * 40 + 10):

                    # Trouver l'élément cliqué
                    for i, (name, value, price) in enumerate(items):
                        item_y = submenu_y + 5 + i * 40
                        item_rect = pygame.Rect(submenu_x + 5, item_y, submenu_width - 10, 35)
                        if item_rect.collidepoint(pos):
                            if value != 'debug_toggle':
                                self.active = value
                            self.expanded_group = None  # Fermer le sous-menu
                            return value
                    # Si on clique dans le sous-menu mais pas sur un item, ne rien faire
                    return None

        # Vérifier les boutons de groupe
        x = 12
        for group_id, group_data in self.groups.items():
            rect = pygame.Rect(x, toolbar_y + 2, 58, 44)
            if rect.collidepoint(pos):
                # Ouvrir/fermer le sous-menu
                if self.expanded_group == group_id:
                    self.expanded_group = None  # Fermer
                else:
                    self.expanded_group = group_id  # Ouvrir
                return group_id
            x += 65
        
        # Si clic ailleurs, fermer le sous-menu
        self.expanded_group = None
        return None
