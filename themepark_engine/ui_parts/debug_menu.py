
import pygame
from ..debug import DebugConfig

class DebugMenu:
    def __init__(self, font, proj_presets, current_proj=0, oblique_tilt=10.0):
        self.font=font; self.visible=False
        self.proj_presets=proj_presets; self.index_proj=current_proj
        self.oblique_tilt=float(oblique_tilt)
        self.show_queue_arrows = True  # Toggle pour les flèches de queue (activé par défaut)
        # layout
        self.width=420; self.pad=8; self.row_h=26; self.header_h=24; self.slider_h=24
        self.rect = pygame.Rect(0,0,self.width, 230 + 30*len(self.proj_presets))
        self.rect.topright=(1280-16,56)
        # sliders
        self.slider_tilt  = pygame.Rect(0,0,self.width-2*self.pad, 8)
        self.knob_tilt    = pygame.Rect(0,0,14,18)
        self.drag_tilt=False
        # bouton pour les flèches
        self.arrow_toggle_rect = pygame.Rect(0,0,self.width-2*self.pad, 24)
        # bouton pour les logs de debug
        self.debug_logs_toggle_rect = pygame.Rect(0,0,self.width-2*self.pad, 24)

    def toggle(self): self.visible = not self.visible

    def _tilt_to_x(self, val, x0, x1): t=(val-10.0)/50.0; return int(x0 + max(0,min(1,t))*(x1-x0))
    def _x_to_tilt(self, x, x0, x1): t=max(0.0,min(1.0,(x-x0)/float(x1-x0))); return 10.0 + 50.0*t

    def draw(self, screen):
        if not self.visible: return
        self.rect.topright=(screen.get_width()-16,56)
        pygame.draw.rect(screen,(20,20,20),self.rect); pygame.draw.rect(screen,(200,200,200),self.rect,1)
        y=self.rect.y+self.pad
        screen.blit(self.font.render('Debug',True,(255,255,255)), (self.rect.x+self.pad,y)); y+=self.header_h
        # Projections
        screen.blit(self.font.render('Projection Presets',True,(200,200,200)), (self.rect.x+self.pad,y)); y+=self.pad
        for i,(tw,th) in enumerate(self.proj_presets):
            r = pygame.Rect(self.rect.x+self.pad, y, self.rect.w-2*self.pad, self.row_h)
            sel = (i==self.index_proj)
            pygame.draw.rect(screen,(60,60,60) if sel else (40,40,40), r)
            pygame.draw.rect(screen,(220,220,0) if sel else (120,120,120), r, 1)
            screen.blit(self.font.render(f"{i+1}. {tw}x{th}", True, (255,255,255)), (r.x+8, r.y+5))
            y+=self.row_h+4
        # Tilt slider
        y+=4
        screen.blit(self.font.render(f"Tilt (φ): {self.oblique_tilt:.1f}°",True,(200,200,200)), (self.rect.x+self.pad,y)); y+=self.pad
        self.slider_tilt.x=self.rect.x+self.pad; self.slider_tilt.y=y+(self.slider_h-8)//2
        pygame.draw.rect(screen,(60,60,60), self.slider_tilt)
        x0t=self.slider_tilt.x; x1t=self.slider_tilt.x+self.slider_tilt.w
        ktx = self._tilt_to_x(self.oblique_tilt, x0t, x1t)
        self.knob_tilt.center=(ktx, self.slider_tilt.centery)
        pygame.draw.rect(screen,(0,200,220), self.knob_tilt)
        
        # Bouton pour afficher/masquer les flèches de queue
        y += 30
        self.arrow_toggle_rect.x = self.rect.x + self.pad
        self.arrow_toggle_rect.y = y
        pygame.draw.rect(screen, (60,60,60) if self.show_queue_arrows else (40,40,40), self.arrow_toggle_rect)
        pygame.draw.rect(screen, (220,220,0) if self.show_queue_arrows else (120,120,120), self.arrow_toggle_rect, 1)
        arrow_text = "Show Queue Arrows: ON" if self.show_queue_arrows else "Show Queue Arrows: OFF"
        screen.blit(self.font.render(arrow_text, True, (255,255,255)), (self.arrow_toggle_rect.x + 8, self.arrow_toggle_rect.y + 4))
        
        # Bouton pour activer/désactiver les logs de debug
        y += 30
        self.debug_logs_toggle_rect.x = self.rect.x + self.pad
        self.debug_logs_toggle_rect.y = y
        pygame.draw.rect(screen, (60,60,60) if DebugConfig.ENABLED else (40,40,40), self.debug_logs_toggle_rect)
        pygame.draw.rect(screen, (220,220,0) if DebugConfig.ENABLED else (120,120,120), self.debug_logs_toggle_rect, 1)
        debug_text = "Debug Logs: ON" if DebugConfig.ENABLED else "Debug Logs: OFF"
        screen.blit(self.font.render(debug_text, True, (255,255,255)), (self.debug_logs_toggle_rect.x + 8, self.debug_logs_toggle_rect.y + 4))

    def handle_mouse(self, event):
        if not self.visible: return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.rect.collidepoint(event.pos): return None
            # projection rows
            y=self.rect.y+self.pad + self.header_h + self.pad
            for i,_ in enumerate(self.proj_presets):
                r = pygame.Rect(self.rect.x+self.pad, y, self.rect.w-2*self.pad, self.row_h)
                if r.collidepoint(event.pos): self.index_proj=i; return ('proj', i)
                y+=self.row_h+4
            # tilt slider
            if self.slider_tilt.collidepoint(event.pos) or self.knob_tilt.collidepoint(event.pos):
                self.drag_tilt=True
                x0=self.slider_tilt.x; x1=self.slider_tilt.x+self.slider_tilt.w
                tl=self._x_to_tilt(event.pos[0], x0, x1); self.oblique_tilt=tl; return ('tilt_oblique', tl)
            
            # arrow toggle button
            if self.arrow_toggle_rect.collidepoint(event.pos):
                self.show_queue_arrows = not self.show_queue_arrows
                return ('toggle_arrows', self.show_queue_arrows)
            
            # debug logs toggle button
            if self.debug_logs_toggle_rect.collidepoint(event.pos):
                if DebugConfig.ENABLED:
                    DebugConfig.disable_all()
                else:
                    DebugConfig.enable_all()
                return ('debug_logs_toggle', DebugConfig.ENABLED)
        elif event.type == pygame.MOUSEMOTION:
            if self.drag_tilt:
                x0=self.slider_tilt.x; x1=self.slider_tilt.x+self.slider_tilt.w
                tl=self._x_to_tilt(event.pos[0], x0, x1); self.oblique_tilt=tl; return ('tilt_oblique', tl)
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.drag_tilt: self.drag_tilt=False
        return None
