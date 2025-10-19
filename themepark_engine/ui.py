
import pygame

class Toolbar:
    def __init__(self, font, ride_defs=None, shop_defs=None, employee_defs=None, bin_defs=None):
        self.font = font
        self.ride_defs = ride_defs or {}
        self.shop_defs = shop_defs or {}
        self.employee_defs = employee_defs or {}
        self.bin_defs = bin_defs or {}
        self._build_groups()
        self.active = 'walk_path'
        self.hovered_button = None
        self.expanded_group = None  # Groupe actuellement ouvert
        self.hovered_subitem = None
    
    def _build_groups(self):
        """Build grouped toolbar items"""
        self.groups = {
            'paths': {
                'name': 'Chemins',
                'icon': '🛤️',
                'items': [
                    ('Walk Path', 'walk_path', 0),  # Prix gratuit
                    ('Queue Path', 'queue_path', 0)  # Prix gratuit
                ]
            },
            'rides': {
                'name': 'Attractions',
                'icon': '🎢',
                'items': []
            },
            'shops': {
                'name': 'Boutiques',
                'icon': '🏪',
                'items': []
            },
            'employees': {
                'name': 'Employés',
                'icon': '👷',
                'items': []
            },
            'bins': {
                'name': 'Poubelles',
                'icon': '🗑️',
                'items': []
            },
            'tools': {
                'name': 'Outils',
                'icon': '🔧',
                'items': [
                    ('Debug', 'debug_toggle', 0)
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
        
        # Add bins dynamically
        for bin_id, bin_def in self.bin_defs.items():
            self.groups['bins']['items'].append((bin_def.name, bin_id, bin_def.cost))
    
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
            else:  # tools
                bg_color = (100, 60, 60) if self.expanded_group == group_id else (60, 40, 40)
                border_color = (200, 100, 100) if self.expanded_group == group_id else (120, 80, 80)
            
            # Effet de survol
            is_hovered = self.hovered_button == group_id
            if is_hovered and self.expanded_group != group_id:
                bg_color = tuple(min(255, c + 20) for c in bg_color)
                border_color = tuple(min(255, c + 30) for c in border_color)
            
            # Dessiner le bouton du groupe
            rect = pygame.Rect(x, toolbar_y + 6, 140, 36)
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, border_color, rect, 2)
            
            # Texte du groupe avec icône
            group_text = f"{group_data['icon']} {group_data['name']}"
            text_surface = self.font.render(group_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
            screen.blit(text_surface, text_rect)
            
            x += 150
        
        # Dessiner le sous-menu si un groupe est ouvert
        if self.expanded_group and self.expanded_group in self.groups:
            self._draw_submenu(screen, toolbar_y)
    
    def _draw_submenu(self, screen, toolbar_y):
        """Dessiner le sous-menu avec les éléments du groupe"""
        group_data = self.groups[self.expanded_group]
        items = group_data['items']
        
        if not items:
            return
        
        # Calculer la position du sous-menu
        group_index = list(self.groups.keys()).index(self.expanded_group)
        submenu_x = 12 + group_index * 150
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
                submenu_x = 12 + group_index * 150
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
            rect = pygame.Rect(x, toolbar_y + 6, 140, 36)
            if rect.collidepoint(pos):
                self.hovered_button = group_id
                break
            x += 150
    
    def handle_click(self, pos, screen_height):
        # Position toolbar en bas de l'écran
        toolbar_y = screen_height - 48
        
        # Vérifier si le clic est dans un sous-menu ouvert
        if self.expanded_group and self.expanded_group in self.groups:
            group_data = self.groups[self.expanded_group]
            items = group_data['items']
            
            if items:
                group_index = list(self.groups.keys()).index(self.expanded_group)
                submenu_x = 12 + group_index * 150
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
        
        # Vérifier les boutons de groupe
        x = 12
        for group_id, group_data in self.groups.items():
            rect = pygame.Rect(x, toolbar_y + 6, 140, 36)
            if rect.collidepoint(pos):
                # Ouvrir/fermer le sous-menu
                if self.expanded_group == group_id:
                    self.expanded_group = None  # Fermer
                else:
                    self.expanded_group = group_id  # Ouvrir
                return group_id
            x += 150
        
        # Si clic ailleurs, fermer le sous-menu
        self.expanded_group = None
        return None
