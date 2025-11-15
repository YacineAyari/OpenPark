import pygame
import sys
from themepark_engine.engine import Game
from themepark_engine.main_menu import MainMenu


def main():
    """Main entry point with menu system"""
    pygame.init()
    pygame.mixer.init()

    # Create screen
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("OpenPark - Theme Park Simulation")
    clock = pygame.time.Clock()

    # Create font
    font = pygame.font.Font(None, 24)

    # Create main menu
    menu = MainMenu(screen, font)

    # Menu loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            # Handle menu events
            result = menu.handle_event(event)
            if result:
                action = result.get("action")

                if action == "quit":
                    running = False
                    pygame.quit()
                    sys.exit()

                elif action == "load":
                    # Load existing game
                    save_file = result.get("save_file")
                    menu.stop_music()
                    game = Game()
                    game.load_game(save_file)
                    game.run()
                    # After game ends, reinitialize pygame and reload menu
                    pygame.init()
                    pygame.mixer.init()
                    pygame.event.clear()  # Clear event queue after init
                    screen = pygame.display.set_mode((1280, 720))
                    pygame.display.set_caption("OpenPark - Theme Park Simulation")
                    font = pygame.font.Font(None, 24)
                    menu = MainMenu(screen, font)
                    pygame.event.pump()  # Process events to refresh queue
                    pygame.event.clear()  # Clear again after menu creation

                elif action == "new_game":
                    # Start new game
                    park_name = result.get("park_name")
                    save_file = result.get("save_file")
                    menu.stop_music()
                    game = Game(save_slot=save_file, park_name=park_name)
                    game.run()
                    # After game ends, reinitialize pygame and reload menu
                    pygame.init()
                    pygame.mixer.init()
                    pygame.event.clear()  # Clear event queue after init
                    screen = pygame.display.set_mode((1280, 720))
                    pygame.display.set_caption("OpenPark - Theme Park Simulation")
                    font = pygame.font.Font(None, 24)
                    menu = MainMenu(screen, font)
                    pygame.event.pump()  # Process events to refresh queue
                    pygame.event.clear()  # Clear again after menu creation

        # Draw menu
        menu.draw()
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
