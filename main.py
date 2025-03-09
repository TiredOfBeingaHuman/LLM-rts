import pygame.freetype as freetype
import pygame
import sys
from game import Game
from renderer import VectorRenderer

def main():
    """Main entry point for the Vector RTS game."""
    # Initialize pygame
    pygame.init()
    
    # Set up the display
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 800
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Vector RTS")
    
    # Create clock for timing
    clock = pygame.time.Clock()
    
    # Initialize game and renderer
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT)
    renderer = VectorRenderer(screen)
    
    # Main game loop
    running = True
    while running:
        # Calculate delta time
        dt = clock.tick(60) / 1000.0  # Convert to seconds
        
        # Process events
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        
        # Update game state
        game.update(dt)
        
        # Render the game
        game.render(screen, renderer)
        
        # Update the display
        pygame.display.flip()
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 