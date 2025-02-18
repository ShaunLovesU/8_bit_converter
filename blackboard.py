import pygame
import time
# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1500, 1000  # Initial window size
GRID_ROWS = 16  # Number of instruments (tracks)
INITIAL_GRID_COLS = 16  # Initial number of time steps
CELL_SIZE = 40  # Size of each grid cell
FIXED_COL_X_RATIO = 0.1  # Fixed first column at 30% of the window width

# Slider range variables
SLIDER_MIN_VALUE = 4
SLIDER_MAX_VALUE = 32


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
SLIDER_MIN, SLIDER_MAX = SLIDER_MIN_VALUE, SLIDER_MAX_VALUE
slider_value = INITIAL_GRID_COLS
font = pygame.font.Font(None, 36)

# Play bar properties
is_playing = False
bps = 1   # Default Beats Per Second
playbar_x = 0
playbar_interval = 1 / bps  # Interval in seconds per step
last_update_time = time.time()
font = pygame.font.Font(None, 36)



play_button = pygame.Rect(50, HEIGHT - 100, 100, 40)
stop_button = pygame.Rect(200, HEIGHT - 100, 100, 40)

# BPM input box
bps_input_box = pygame.Rect(350, HEIGHT - 100, 100, 50)
bps_text = str(bps)


def draw_buttons():
    """Draws the play and stop buttons."""
    pygame.draw.rect(screen, BLUE, play_button)
    pygame.draw.rect(screen, BLUE, stop_button)
    play_text = font.render("Play", True, WHITE)
    stop_text = font.render("Stop", True, WHITE)
    screen.blit(play_text, (play_button.x + 25, play_button.y + 10))
    screen.blit(stop_text, (stop_button.x + 25, stop_button.y + 10))

    # Draw BPM input box
    pygame.draw.rect(screen, WHITE, bps_input_box)
    bps_display = font.render(bps_text, True, BLACK)
    screen.blit(bps_display, (bps_input_box.x + 10, bps_input_box.y + 10))

def draw_slider():
    """Draws the slider for adjusting the number of columns."""
    slider_x = 50  # Keep slider at the bottom left
    slider_y = HEIGHT - 50  # Always below the grid
    pygame.draw.rect(screen, BLACK, (slider_x, slider_y, SLIDER_WIDTH, SLIDER_HEIGHT))
    handle_x = slider_x + ((slider_value - SLIDER_MIN) / (SLIDER_MAX - SLIDER_MIN)) * SLIDER_WIDTH
    pygame.draw.circle(screen, BLUE, (int(handle_x), slider_y + SLIDER_HEIGHT // 2), 8)

    # Display the current grid column number
    value_text = font.render(f"Cols: {slider_value}", True, BLACK)
    screen.blit(value_text, (slider_x + SLIDER_WIDTH + 10, slider_y - 10))

def update_grid():
    """Updates the grid size based on the slider value, keeping the first column fixed at 30% position."""
    global grid, GRID_COLS, GRID_X, playbar_x, playbar_limit
    GRID_COLS = slider_value
    GRID_X = get_fixed_col_x() + CELL_SIZE  # The second column starts right after the fixed column
    playbar_x = GRID_X - 40  # Reset playbar to start position
    playbar_limit = GRID_X + (GRID_COLS - 1) * CELL_SIZE  # Set playbar limit
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



def draw_playbar():
    """Draws the play bar that moves across the grid columns based on BPS."""
    global playbar_x, last_update_time
    if is_playing:
        current_time = time.time()
        if current_time - last_update_time >= playbar_interval:
            last_update_time = current_time
            playbar_x += CELL_SIZE
            if playbar_x >= GRID_X + (slider_value - 1) * CELL_SIZE:
                playbar_x = GRID_X -40
    pygame.draw.rect(screen, BLUE, (playbar_x, (HEIGHT - GRID_ROWS * CELL_SIZE - 60) // 2, 5, GRID_ROWS * CELL_SIZE))




def handle_mouse_click(pos):
    """Handles mouse click to toggle notes, adjust the slider, press buttons, or enter BPS."""
    global is_playing, playbar_x, bps_text, bps, playbar_interval
    x, y = pos
    if play_button.collidepoint(x, y):
        is_playing = True
        playbar_x = GRID_X
    elif stop_button.collidepoint(x, y):
        is_playing = False
    elif bps_input_box.collidepoint(x, y):
        bps_text = ""  # Clear input when clicked
    else:
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



def handle_key_input(event):
    """Handles BPS input typing."""
    global bps_text, bps, playbar_interval
    if event.key == pygame.K_RETURN:
        try:
            bps = float(bps_text)
            playbar_interval = 1 / bps
        except ValueError:
            bps_text = str(bps)  # Reset if invalid
    elif event.key == pygame.K_BACKSPACE:
        bps_text = bps_text[:-1]
    else:
        bps_text += event.unicode

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
        draw_playbar()
        draw_buttons()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_grid()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                handle_key_input(event)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
