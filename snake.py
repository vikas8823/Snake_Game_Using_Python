"""
Snake Game - built with Pygame

Controls:
    Arrow keys / WASD  - move
    P                  - pause / resume
    R                  - restart (after game over)
    ESC                - quit
"""

import random
import sys
from pathlib import Path

import pygame

# ---------- Settings ----------
CELL = 20
COLS, ROWS = 30, 24
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL + 40  # extra 40px for the score bar
BASE_FPS = 8
MAX_FPS = 20

BG = (18, 18, 28)
GRID = (28, 28, 42)
SNAKE_HEAD = (80, 250, 123)
SNAKE_BODY = (46, 160, 90)
FOOD = (255, 85, 85)
BONUS = (255, 215, 0)
TEXT = (235, 235, 245)
BAR = (10, 10, 18)

HIGHSCORE_FILE = Path(__file__).with_name("snake_highscore.txt")

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)


def load_highscore() -> int:
    try:
        return int(HIGHSCORE_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_highscore(score: int) -> None:
    try:
        HIGHSCORE_FILE.write_text(str(score))
    except OSError:
        pass


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        start = (COLS // 2, ROWS // 2)
        self.body = [start, (start[0] - 1, start[1]), (start[0] - 2, start[1])]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.grow_pending = 0

    def set_direction(self, new_dir):
        # Prevent reversing directly into yourself
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (0, 0):
            self.next_direction = new_dir

    def move(self):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, amount=1):
        self.grow_pending += amount

    @property
    def head(self):
        return self.body[0]

    def hit_wall(self):
        x, y = self.head
        return not (0 <= x < COLS and 0 <= y < ROWS)

    def hit_self(self):
        return self.head in self.body[1:]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 44, bold=True)

        self.high_score = load_highscore()
        self.new_game()

    def new_game(self):
        self.snake = Snake()
        self.score = 0
        self.bonus = None
        self.bonus_timer = 0
        self.food = self.random_free_cell()
        self.paused = False
        self.game_over = False

    def random_free_cell(self):
        occupied = set(self.snake.body)
        if self.bonus:
            occupied.add(self.bonus)
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occupied]
        return random.choice(free)

    @property
    def fps(self):
        # Speed up every 5 points
        return min(BASE_FPS + self.score // 5, MAX_FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                if event.key == pygame.K_r and self.game_over:
                    self.new_game()

                keymap = {
                    pygame.K_UP: UP, pygame.K_w: UP,
                    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
                    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
                    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
                }
                if event.key in keymap and not self.paused and not self.game_over:
                    self.snake.set_direction(keymap[event.key])

    def update(self):
        if self.paused or self.game_over:
            return

        self.snake.move()

        if self.snake.hit_wall() or self.snake.hit_self():
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
                save_highscore(self.high_score)
            return

        # Normal food
        if self.snake.head == self.food:
            self.snake.grow()
            self.score += 1
            self.food = self.random_free_cell()
            # Occasionally spawn a timed bonus food
            if self.bonus is None and random.random() < 0.25:
                self.bonus = self.random_free_cell()
                self.bonus_timer = 50  # ticks until it disappears

        # Bonus food
        if self.bonus:
            if self.snake.head == self.bonus:
                self.snake.grow(2)
                self.score += 5
                self.bonus = None
            else:
                self.bonus_timer -= 1
                if self.bonus_timer <= 0:
                    self.bonus = None

    def draw_cell(self, pos, color, inset=1):
        rect = pygame.Rect(pos[0] * CELL + inset, pos[1] * CELL + inset + 40,
                           CELL - inset * 2, CELL - inset * 2)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)

    def draw_text_center(self, text, font, y, color=TEXT):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))

    def draw(self):
        self.screen.fill(BG)

        # Score bar
        pygame.draw.rect(self.screen, BAR, (0, 0, WIDTH, 40))
        self.screen.blit(self.font.render(f"Score: {self.score}", True, TEXT), (12, 8))
        best = self.font.render(f"Best: {self.high_score}", True, BONUS)
        self.screen.blit(best, (WIDTH - best.get_width() - 12, 8))

        # Grid
        for x in range(COLS):
            for y in range(ROWS):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(self.screen, GRID, (x * CELL, y * CELL + 40, CELL, CELL))

        # Food
        self.draw_cell(self.food, FOOD, inset=3)
        if self.bonus:
            self.draw_cell(self.bonus, BONUS, inset=2)

        # Snake
        for i, segment in enumerate(self.snake.body):
            self.draw_cell(segment, SNAKE_HEAD if i == 0 else SNAKE_BODY)

        # Overlays
        if self.paused:
            self.draw_text_center("PAUSED", self.big_font, HEIGHT // 2)
            self.draw_text_center("Press P to resume", self.font, HEIGHT // 2 + 45)
        if self.game_over:
            self.draw_text_center("GAME OVER", self.big_font, HEIGHT // 2 - 20, FOOD)
            self.draw_text_center(f"Score: {self.score}", self.font, HEIGHT // 2 + 25)
            self.draw_text_center("Press R to restart or ESC to quit", self.font, HEIGHT // 2 + 55)

        pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)


if __name__ == "__main__":
    Game().run()