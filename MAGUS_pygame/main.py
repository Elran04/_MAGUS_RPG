import pygame
import math

# --- CONFIG ---
WIDTH, HEIGHT = 1024, 768
HEX_SIZE = 40  # Radius of hex

# --- COLORS ---
BG_COLOR = (30, 30, 40)
HEX_COLOR = (80, 120, 180)
HEX_BORDER = (200, 200, 220)

# --- Calculate grid size to fill the screen ---
def get_grid_bounds():
    # For pointy-topped hexes
    hex_width = HEX_SIZE * math.sqrt(3)
    vert_spacing = HEX_SIZE * 1.5
    # Use a wide enough range to cover the screen
    min_q = -int(WIDTH // hex_width)
    max_q = int(WIDTH // hex_width) * 2
    min_r = -int(HEIGHT // vert_spacing)
    max_r = int(HEIGHT // vert_spacing) * 2
    return min_q, max_q, min_r, max_r

MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MAGUS Hexgrid Turn-Based Demo")
clock = pygame.time.Clock()

# Load the sprite (place this near the top, after pygame.init())
warrior_img_orig = pygame.image.load("warrior_sprite_selfmade.jpg").convert_alpha()
# Scale to fit inside the hex's bounding circle
sprite_size = int(HEX_SIZE * 2)
warrior_img = pygame.transform.smoothscale(warrior_img_orig, (sprite_size, sprite_size))
# Create a hex mask surface
hex_mask = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
center = (sprite_size // 2, sprite_size // 2)
points = []
for i in range(6):
    angle = math.pi/180 * (60 * i - 30)
    x = center[0] + HEX_SIZE * math.cos(angle)
    y = center[1] + HEX_SIZE * math.sin(angle)
    points.append((x, y))
pygame.draw.polygon(hex_mask, (255, 255, 255, 255), points)
# Apply mask to the sprite
warrior_img_masked = warrior_img.copy()
warrior_img_masked.blit(hex_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

# Warrior's current hex position
warrior_q, warrior_r = 3, 3

def hex_to_pixel(q, r):
    """Convert hex coordinates to pixel coordinates (pointy-topped)."""
    x = HEX_SIZE * math.sqrt(3) * (q + r/2)
    y = HEX_SIZE * 3/2 * r
    return int(x), int(y)

def draw_hex(surface, color, pos, size, border=2):
    """Draw a single hex at pos (center) with given size."""
    points = []
    for i in range(6):
        angle = math.pi/180 * (60 * i - 30)
        x = pos[0] + size * math.cos(angle)
        y = pos[1] + size * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, HEX_BORDER, points, border)

def draw_grid():
    margin = HEX_SIZE * 2
    for q in range(MIN_Q, MAX_Q):
        for r in range(MIN_R, MAX_R):
            px, py = hex_to_pixel(q, r)
            if -margin < px < WIDTH + margin and -margin < py < HEIGHT + margin:
                draw_hex(screen, HEX_COLOR, (px, py), HEX_SIZE)
                # Place the sprite at the warrior's current hex
                if q == warrior_q and r == warrior_r:
                    rect = warrior_img_masked.get_rect(center=(px, py))
                    screen.blit(warrior_img_masked, rect)

def pixel_to_hex(x, y):
    # Inverse of hex_to_pixel for pointy-topped hexes
    q = (x / (HEX_SIZE * math.sqrt(3)) - y / (HEX_SIZE * 3/2) / 2)
    r = y / (HEX_SIZE * 3/2)
    # Round to nearest hex
    rq = round(q)
    rr = round(r)
    return rq, rr

def main():
    global warrior_q, warrior_r
    running = True
    turn = 0  # 0: Player, 1: Enemy (example)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Move warrior on left mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                q, r = pixel_to_hex(mx, my)
                # Only move if the clicked hex is on the grid
                if MIN_Q <= q < MAX_Q and MIN_R <= r < MAX_R:
                    warrior_q, warrior_r = q, r
            # Example: right click to advance turn
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                turn = (turn + 1) % 2

        screen.fill(BG_COLOR)
        draw_grid()

        # Draw turn info
        font = pygame.font.SysFont(None, 36)
        text = font.render(f"Turn: {'Player' if turn == 0 else 'Enemy'}", True, (255,255,255))
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()