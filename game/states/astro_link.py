import pygame
import gif_pygame
import math
from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from game.utils import *
from game.widgets import Button, TextLine, MultiLine
from .states import States


class AstroLink(BaseState):
    def __init__(self, game=None):
        super().__init__(States.ASTRO_LINK, game)

        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
            speed=100,
        )

        bg_gif_path = resource_path("assets/gifs/astro_link_bg.gif")
        with open(bg_gif_path, "rb") as f:
            gif_bytes = f.read()

        self.bg_gif = load_gif_from_bytes(gif_bytes)
        self.bg_frame_index = 0
        self.bg_frame_delay = 60  # ms per frame
        self.bg_frame_timer = 0

        self.bg_gif_surf = None

        # Load images (no change needed here)
        self.spacecraft_img_original = pygame.image.load(
            resource_path("assets/images/spacecraft.png")
        ).convert_alpha()

        self.satellite_img = pygame.image.load(
            resource_path("assets/images/satellite.png")
        ).convert_alpha()

        self.ground_station_img = pygame.image.load(
            resource_path("assets/images/ground_station.png")
        ).convert_alpha()
        self.ground_station_img.set_alpha(200)

        # Dynamic sizing (no change needed here)
        self.spacecraft_size_ratio = (0.10, 0.16)
        self.satellite_size_ratio = (0.12, 0.2)
        self.ground_station_size_ratio = (0.05, 0.09)

        # Orbit parameters for spacecraft (no change needed here)
        self.orbit_center_ratio = (0.5, 0.4)  # Center of orbit
        self.orbit_radius_x_ratio = 0.30  # Horizontal radius
        self.orbit_radius_y_ratio = 0.25  # Vertical radius (ellipse)
        self.orbit_angle = 0.0  # Current angle in orbit
        self.orbit_speed = 30.0  # Degrees per second

        # Static positions (no change needed here)
        self.satellite_pos_ratio = (0.5, 0.4)  # Center of screen
        self.ground_station_pos_ratio = (0.5, 0.85)  # Bottom center

        # Placeholder to prevent crash, actual pos calculated in update
        self.spacecraft_pos_ratio = (0.5, 0.4)

        # Scaled images and rects (no change needed here)
        self.spacecraft = None
        self.spacecraft_rect = None
        # We keep a scaled original to rotate from to prevent pixel degradation
        self.spacecraft_scaled_original = None
        self.spacecraft_img = self.spacecraft_img_original

        self.satellite = None
        self.satellite_rect = None
        self.ground_station = None
        self.ground_station_rect = None

        # Antenna control (no change needed here)
        self.antenna_angle = 0.0  # Current actual angle
        self.target_antenna_angle = 0.0  # Where the mouse is
        self.dragging = False
        self.antenna_length_ratio = 0.14

        # Signal Waves (Visual effect) (no change needed here)
        self.waves = (
            []
        )  # List of dicts {'pos': Vector2, 'start': Vector2, 'end': Vector2, 'progress': 0.0}

        # Signal state (no change needed here)
        self.beam_connected = False
        self.transmission_timer = 0.0
        self.transmission_duration = 3.0  # 3 seconds to win

        # Load sounds (no change needed here)
        self.game.sound_manager.load_sound(
            "beam_connect",
            resource_path("assets/sound/sfx/beam_connect.mp3"),
        )
        self.game.sound_manager.load_sound(
            "transmission_success",
            resource_path("assets/sound/sfx/transmission_success.mp3"),
        )
        self.game.sound_manager.load_sound(
            "win", resource_path("assets/sound/sfx/win.mp3")
        )

        # Game state (no change needed here)
        self.level_complete = False
        self._played_win_sound = False
        self._played_beam_sound = False

        # --- MULTILINE TEXT BLOCK (Localized) ---
        line_sizes = (25, 27, 30)
        self.text_block = MultiLine(
            lines=[
                TextLine(
                    text=heb("סובב את האנטנה של החללית כדי ליישר אותה עם הלוויין"),
                    font=self.game.font,
                    base_ratio=line_sizes[0],
                    color=(*Colors.WHITE, 240),
                    game_size=self.game.size,
                ),
                TextLine(
                    text=heb("שמור על החיבור למשך 3 שניות כדי לשדר את האות"),
                    font=self.game.font,
                    base_ratio=line_sizes[1],
                    color=(*Colors.PLATINUM, 220),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="(" + heb("לחץ וגרור כדי לסובב") + ")",
                    font=self.game.font,
                    base_ratio=line_sizes[2],
                    color=(*Colors.CRIMSON, 200),
                    game_size=self.game.size,
                ),
            ],
            start_y_ratio=0.025,
            line_spacing_ratio=0.015,
            game_size=self.game.size,
        )

        # Next Level button (Localized)
        self.next_button = Button(
            color=Colors.DARK_GREEN,
            function=self.game.sm.next_state,
            text=heb("לשלב הבא"),
            font=self.game.font,
            font_color=Colors.PLATINUM,
            call_on_release=True,
            hover_color=Colors.KHAKI_PLAT,
            hover_font_color=Colors.DARK_GREEN,
            clicked_color=Colors.DARK_GREEN,
            clicked_font_color=Colors.PLATINUM,
            click_sound=pygame.Sound(
                resource_path("assets/sound/sfx/button_click.mp3")
            ),
            size_ratio=(0.15, 0.06),
            screen_size=self.game.size,
            border_radius=12,
        )

    def startup(self):
        # Localized window caption
        pygame.display.set_caption(heb("קישור אסטרו"))
        self.fade_transition.startup()
        self.next_button.startup()

        # Reset game state
        self.level_complete = False
        self._played_win_sound = False
        self._played_beam_sound = False
        self.antenna_angle = 0.0
        self.target_antenna_angle = 0.0
        self.dragging = False
        self.beam_connected = False
        self.transmission_timer = 0.0
        self.orbit_angle = 0.0
        self.waves = []

        # Scale images based on screen size
        self._scale_images()

        # Play background music
        pygame.mixer.music.load(resource_path("assets/sound/music/interstellar.mp3"))
        pygame.mixer.music.play(-1, fade_ms=1000)

    def cleanup(self):
        pass

    def _scale_images(self):
        """Scale all images based on current screen size."""
        w, h = self.game.size

        # Spacecraft (Scale the original, store as scaled_original)
        sc_w = int(w * self.spacecraft_size_ratio[0])
        sc_h = int(h * self.spacecraft_size_ratio[1])

        self.spacecraft_scaled_original = pygame.transform.scale(
            self.spacecraft_img_original, (sc_w, sc_h)
        )
        self.spacecraft = self.spacecraft_scaled_original.copy()

        # Initialize rect, pos updated immediately in update loop
        self.spacecraft_rect = self.spacecraft.get_rect()
        self._update_spacecraft_position()

        # Satellite
        sat_w = int(w * self.satellite_size_ratio[0])
        sat_h = int(h * self.satellite_size_ratio[1])
        self.satellite = pygame.transform.scale(self.satellite_img, (sat_w, sat_h))
        self.satellite_rect = self.satellite.get_rect(
            center=(
                int(w * self.satellite_pos_ratio[0]),
                int(h * self.satellite_pos_ratio[1]),
            )
        )

        # Ground station
        gs_w = int(w * self.ground_station_size_ratio[0])
        gs_h = int(h * self.ground_station_size_ratio[1])
        self.ground_station = pygame.transform.scale(
            self.ground_station_img, (gs_w, gs_h)
        )
        self.ground_station_rect = self.ground_station.get_rect(
            center=(
                int(w * self.ground_station_pos_ratio[0]),
                int(h * self.ground_station_pos_ratio[1]),
            )
        )

    def _update_spacecraft_position(self):
        """Calculates position AND rotation of spacecraft."""
        if not self.spacecraft_rect or not self.satellite_rect:
            return

        w, h = self.game.size

        # 1. Calculate Orbit Position
        cx = w * self.orbit_center_ratio[0]
        cy = h * self.orbit_center_ratio[1]
        rx = w * self.orbit_radius_x_ratio
        ry = h * self.orbit_radius_y_ratio

        rad_angle = math.radians(self.orbit_angle)
        new_x = cx + rx * math.cos(rad_angle)
        new_y = cy + ry * math.sin(rad_angle)

        # 2. Determine if spacecraft should be flipped
        # Check if spacecraft is on left side (-x) or right side (+x) of orbit
        # Flip when on the left side (when x < center_x)
        # Note: The original code flips vertically (True, False), which is likely intended to simulate
        # the craft rotating its orientation as it orbits an object, but this is usually a horizontal flip
        # for a sprite that needs to face the orbit center. I'll maintain the original `(True, False)` for vertical flip.
        should_flip = new_y >= cy

        # 3. Apply flip if needed
        self.spacecraft_img = self.spacecraft_scaled_original
        if should_flip:
            self.spacecraft_img = pygame.transform.flip(
                self.spacecraft_scaled_original,
                True,
                False,  # flip vertically (based on original code's comment, might be a bug/intention of the game author)
            )

        # # 4. Rotate the (possibly flipped) image (No rotation in this code, just flip)
        self.spacecraft = self.spacecraft_img

        # 5. Update rect with new center
        self.spacecraft_rect = self.spacecraft.get_rect(center=(int(new_x), int(new_y)))

    def get_event(self, event: pygame.event.Event):
        if self.level_complete:
            self.next_button.get_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Allow clicking anywhere nearby to start dragging
            if (
                self.spacecraft_rect.collidepoint(event.pos) or True
            ):  # True makes it easier
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.spacecraft_rect.centerx
            dy = event.pos[1] - self.spacecraft_rect.centery
            # Update TARGET, not actual angle, for smoothing
            self.target_antenna_angle = math.degrees(math.atan2(dy, dx))

        if event.type == pygame.KEYDOWN and self.game.admin:
            if event.key == pygame.K_d and (event.mod & pygame.KMOD_CTRL):
                self._trigger_win()

    def update(self, screen, dt):
        # If GIF delay accidentally left large, reduce to reasonable frame interval:
        if hasattr(self, "bg_frame_delay") and self.bg_frame_delay > 1.0:
            # likely value from earlier bug — use ~120ms per frame
            self.bg_frame_delay = 0.12

        # Background GIF (dt is seconds)
        self.bg_frame_timer += dt
        if self.bg_frame_timer >= self.bg_frame_delay:
            self.bg_frame_timer = 0.0
            # protect against empty gif frames
            if self.bg_gif:
                self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_gif)
        if self.bg_gif:
            bg_frame = self.bg_gif[self.bg_frame_index]
            # scale each frame to screen size
            try:
                self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)
            except Exception:
                # fallback: if frame isn't a surface, ignore
                self.bg_gif_surf = None

        # text block
        self.text_block.update(self.game.size)

        # Handle Resize
        current_sc_w = int(self.game.width * self.spacecraft_size_ratio[0])
        # Check against scaled original width to detect resize
        if (
            self.spacecraft_scaled_original
            and self.spacecraft_scaled_original.get_width() != current_sc_w
        ):
            self._scale_images()

        # Update Orbit
        if not self.level_complete:
            self.orbit_angle += self.orbit_speed * dt
            if self.orbit_angle >= 360:
                self.orbit_angle -= 360

        self._update_spacecraft_position()

        # --- Smooth Antenna Rotation ---
        # Calculate shortest difference to target
        diff = (self.target_antenna_angle - self.antenna_angle + 180) % 360 - 180
        # Lerp factor (adjust 10.0 for speed, lower is smoother)
        self.antenna_angle += diff * 10.0 * dt

        # Update Logic
        if self.level_complete:
            self.next_button.update(self.game.size)

        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        self._check_beam_collision()

        # --- Signal Logic ---
        if self.beam_connected and not self.level_complete:
            self.transmission_timer += dt

            # Spawn waves
            # Spawn roughly every 0.5 seconds (using random chance or timer)
            import random

            if random.random() < 0.1:  # simple probabilistic spawn
                # Use satellite center as start point
                sat_center = (
                    self.satellite_rect.center if self.satellite_rect else (0, 0)
                )
                # Use ground station center as end point
                gs_center = (
                    self.ground_station_rect.center
                    if self.ground_station_rect
                    else (0, 0)
                )

                self.waves.append(
                    {
                        "start": sat_center,
                        "end": gs_center,
                        "progress": 0.0,
                        "speed": 0.5,  # traversals per second
                    }
                )

            if self.transmission_timer >= self.transmission_duration:
                self._trigger_win()
        else:
            self.transmission_timer = max(0, self.transmission_timer - dt * 0.5)
            # Clear waves if beam breaks
            if not self.beam_connected:
                self.waves = []

        # Update Waves
        for wave in self.waves[:]:
            wave["progress"] += wave["speed"] * dt
            if wave["progress"] >= 1.0:
                self.waves.remove(wave)

    def draw(self, screen: pygame.Surface):
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (0, 0))

        if not self.level_complete:
            self.text_block.draw(screen)

        # Draw connecting waves (Bottom layer)
        self._draw_waves(screen)

        if self.satellite:
            screen.blit(self.satellite, self.satellite_rect)
        if self.ground_station:
            screen.blit(self.ground_station, self.ground_station_rect)

        # Draw spacecraft last so it's on top
        if self.spacecraft:
            screen.blit(self.spacecraft, self.spacecraft_rect)

        if self.spacecraft and self.spacecraft_rect and not self.level_complete:
            self._draw_beam(screen)

        self._draw_signal_strength(screen)

        if self.level_complete:
            self._draw_win_ui(screen)

        self.fade_transition.draw(screen)

    def _draw_waves(self, screen):
        """Draws signals moving from satellite to ground station."""
        for wave in self.waves:
            start_x, start_y = wave["start"]
            end_x, end_y = wave["end"]

            # Lerp position
            t = wave["progress"]
            cur_x = start_x + (end_x - start_x) * t
            cur_y = start_y + (end_y - start_y) * t

            # Radius grows slightly
            radius = 5 + (t * 20)

            # Alpha fades out (255 -> 0)
            alpha = int(255 * (1 - t))

            # Draw simple circle pulse
            s = pygame.Surface((int(radius) * 2, int(radius) * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s, (*Colors.GREEN, alpha), (int(radius), int(radius)), int(radius), 2
            )
            screen.blit(s, (cur_x - radius, cur_y - radius))

    def _draw_beam(self, screen: pygame.Surface):
        w, h = self.game.size
        antenna_length = int(w * self.antenna_length_ratio)

        start_x, start_y = self.spacecraft_rect.center
        end_x = start_x + antenna_length * math.cos(math.radians(self.antenna_angle))
        end_y = start_y + antenna_length * math.sin(math.radians(self.antenna_angle))

        beam_color = Colors.GREEN if self.beam_connected else Colors.RED
        beam_width = 4 if self.beam_connected else 2

        pygame.draw.line(
            screen, beam_color, (start_x, start_y), (end_x, end_y), beam_width
        )
        pygame.draw.circle(screen, beam_color, (int(end_x), int(end_y)), 6)

    def _draw_signal_strength(self, screen: pygame.Surface):
        w, h = self.game.size
        bar_width = int(w * 0.2)
        bar_height = int(h * 0.03)
        bar_x = int(w * 0.5 - bar_width / 2)
        bar_y = int(h * 0.95)
        strength = self.transmission_timer / self.transmission_duration
        if self.level_complete:
            strength = 1

        pygame.draw.rect(
            screen, Colors.DARK_GREEN, (bar_x, bar_y, bar_width, bar_height)
        )

        progress_width = int(bar_width * strength)
        progress_color = (
            Colors.GREEN
            if self.beam_connected
            else (Colors.GREEN if self.level_complete else Colors.RED)
        )
        pygame.draw.rect(
            screen, progress_color, (bar_x, bar_y, progress_width, bar_height)
        )

        pygame.draw.rect(screen, Colors.WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # Localized label
        label_text = heb("אות") + f": {int(strength * 100)}%"
        label_surf, label_rect = self.game.font.render(
            label_text,
            Colors.WHITE,
            size=self.game.size_depended(30),
        )
        label_rect.centerx = bar_x + bar_width // 2
        label_rect.bottom = bar_y - 5
        screen.blit(label_surf, label_rect)

    def _check_beam_collision(self):
        w, h = self.game.size
        antenna_length = int(w * self.antenna_length_ratio)

        start_x, start_y = self.spacecraft_rect.center
        end_x = start_x + antenna_length * math.cos(math.radians(self.antenna_angle))
        end_y = start_y + antenna_length * math.sin(math.radians(self.antenna_angle))

        expanded_satellite = self.satellite_rect.inflate(20, 20)
        beam_end_point = pygame.Rect(int(end_x) - 15, int(end_y) - 15, 30, 30)

        was_connected = self.beam_connected
        self.beam_connected = beam_end_point.colliderect(
            expanded_satellite
        ) or expanded_satellite.clipline((start_x, start_y), (end_x, end_y))

        if self.beam_connected and not was_connected:
            self.game.sound_manager.play_sound("beam_connect")
            self._played_beam_sound = True
        elif not self.beam_connected:
            self._played_beam_sound = False

    def _trigger_win(self):
        if not self.level_complete:
            self.level_complete = True
            self.game.sound_manager.play_sound("transmission_success")
            logger.info("AstroLink: Level complete!")

    def _draw_win_ui(self, screen: pygame.Surface):
        w, h = screen.get_size()
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        if not self._played_win_sound:
            self.game.sound_manager.play_sound("win")
            self._played_win_sound = True

        # Localized Win Text
        text_surf, text_rect = self.game.font.render(
            heb("עבודה טובה!"), Colors.WHITE, size=self.game.size_depended(10)
        )
        text_pos = mid_pos((w, h), text_rect)
        screen.blit(text_surf, text_pos)

        text_rect_on_screen = text_rect.copy()
        text_rect_on_screen.topleft = text_pos

        self.next_button.pos_ratio = (
            text_rect_on_screen.centerx / w,
            (text_rect_on_screen.bottom + text_rect_on_screen.h) / h,
        )

        self.next_button.update((w, h))
        self.next_button.draw(screen)
