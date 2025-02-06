import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 400  # Window size
GRID_ROWS = 4  # Number of instruments (tracks)
GRID_COLS = 16  # Number of time steps
CELL_SIZE = 40  # Size of each grid cell
GRID_WIDTH = GRID_COLS * CELL_SIZE
GRID_HEIGHT = GRID_ROWS * CELL_SIZE
GRID_X = (WIDTH - GRID_WIDTH) // 2  # Center horizontally
GRID_Y = (HEIGHT - GRID_HEIGHT) // 2  # Center vertically

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 100, 255)

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chiptune Music Sequencer")

# Grid data (stores active notes)
grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def draw_grid():
    """Draws the sequencer grid at the center of the screen."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = GRID_X + col * CELL_SIZE
            y = GRID_Y + row * CELL_SIZE
            color = BLUE if grid[row][col] else WHITE
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)


def handle_mouse_click(pos):
    """Handles mouse click to toggle notes."""
    x, y = pos
    col = (x - GRID_X) // CELL_SIZE
    row = (y - GRID_Y) // CELL_SIZE
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        grid[row][col] = 1 - grid[row][col]  # Toggle on/off


def main():
    """Main loop."""
    running = True
    while running:
        screen.fill(GRAY)
        draw_grid()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()