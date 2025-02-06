import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 1000  # Initial window size
GRID_ROWS = 16  # Number of instruments (tracks)
INITIAL_GRID_COLS = 16  # Initial number of time steps
CELL_SIZE = 40  # Size of each grid cell
FIXED_COL_X_RATIO = 0.1  # Fixed first column at 30% of the window width


def get_fixed_col_x():
    return int(WIDTH * FIXED_COL_X_RATIO)


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 100, 255)

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Chiptune Music Sequencer")

# Slider properties
SLIDER_WIDTH, SLIDER_HEIGHT = 300, 10
SLIDER_MIN, SLIDER_MAX = 4, 32
slider_value = INITIAL_GRID_COLS


def draw_slider():
    """Draws the slider for adjusting the number of columns."""
    slider_x = 50  # Keep slider at the bottom left
    slider_y = HEIGHT - 50  # Always below the grid
    pygame.draw.rect(screen, BLACK, (slider_x, slider_y, SLIDER_WIDTH, SLIDER_HEIGHT))
    handle_x = slider_x + ((slider_value - SLIDER_MIN) / (SLIDER_MAX - SLIDER_MIN)) * SLIDER_WIDTH
    pygame.draw.circle(screen, BLUE, (int(handle_x), slider_y + SLIDER_HEIGHT // 2), 8)


def update_grid():
    """Updates the grid size based on the slider value, keeping the first column fixed at 30% position."""
    global grid, GRID_COLS, GRID_X
    GRID_COLS = slider_value
    GRID_X = get_fixed_col_x() + CELL_SIZE  # The second column starts right after the fixed column
    for row in range(GRID_ROWS):
        grid[row] = grid[row][:1] + [0] * (GRID_COLS - 1)


def draw_grid():
    """Draws the sequencer grid with the first column fixed at 30% position."""
    fixed_col_x = get_fixed_col_x()
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = GRID_X + (col - 1) * CELL_SIZE if col > 0 else fixed_col_x
            y = (HEIGHT - GRID_ROWS * CELL_SIZE - 60) // 2 + row * CELL_SIZE  # Ensure grid doesn't cover the slider
            color = BLUE if grid[row][col] else WHITE
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)


def handle_mouse_click(pos):
    """Handles mouse click to toggle notes or adjust the slider."""
    x, y = pos
    slider_x = 50  # Match the slider position
    slider_y = HEIGHT - 50
    if slider_x <= x <= slider_x + SLIDER_WIDTH and slider_y - 10 <= y <= slider_y + SLIDER_HEIGHT + 10:
        global slider_value
        slider_value = int(SLIDER_MIN + ((x - slider_x) / SLIDER_WIDTH) * (SLIDER_MAX - SLIDER_MIN))
        update_grid()
    else:
        col = (x - GRID_X) // CELL_SIZE + 1 if x > GRID_X else 0
        row = (y - (HEIGHT - GRID_ROWS * CELL_SIZE - 60) // 2) // CELL_SIZE
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            grid[row][col] = 1 - grid[row][col]  # Toggle on/off


def main():
    """Main loop."""
    global grid, WIDTH, HEIGHT, screen
    grid = [[0 for _ in range(INITIAL_GRID_COLS)] for _ in range(GRID_ROWS)]
    update_grid()
    running = True
    while running:
        screen.fill(GRAY)
        draw_grid()
        draw_slider()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_grid()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
