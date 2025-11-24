import pygame
import random
import math
from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from game.utils import resource_path, load_gif_from_bytes, mid_pos
from .states import States
from game.widgets import Button, TextLine, MultiLine


class LifeSupport(BaseState):
    def __init__(self, game=None):
        super().__init__(States.LIFE_SUPPORT, game)

        # Fade transition
        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
            speed=100,
        )

        # --- Background GIF ---
        bg_gif_path = resource_path("assets/gifs/lifesupport_bg.gif")
        with open(bg_gif_path, "rb") as f:
            gif_bytes = f.read()
        self.bg_gif = load_gif_from_bytes(gif_bytes)
        self.bg_frame_index = 0
        self.bg_frame_delay = 60
        self.bg_frame_timer = 0
        self.bg_gif_surf = None

        # --- Icons (original assets) ---
        self.icon_o2_orig = pygame.image.load(
            resource_path("assets/images/icon_o2.png")
        ).convert_alpha()
        self.icon_temp_orig = pygame.image.load(
            resource_path("assets/images/icon_temp.png")
        ).convert_alpha()
        self.icon_water_orig = pygame.image.load(
            resource_path("assets/images/icon_water.png")
        ).convert_alpha()
        self.icon_rad_orig = pygame.image.load(
            resource_path("assets/images/icon_radiation.png")
        ).convert_alpha()

        # Scaled versions
        self.icon_o2 = None
        self.icon_o2_rect = None
        self.icon_temp = None
        self.icon_temp_rect = None
        self.icon_water = None
        self.icon_water_rect = None
        self.icon_rad = None
        self.icon_rad_rect = None

        # --- System Values (0-100) ---
        self.o2 = 100.0
        self.temp = 100.0
        self.water = 100.0
        self.radiation = 0.0  # 0 is safe, 100 is lethal

        # Decay/increase rates (per second) - made more challenging
        self.o2_decay = 2.4
        self.temp_decay = 1.6
        self.water_decay = 2.0
        self.rad_increase = 0.8

        # --- Button cooldowns (to prevent spam) ---
        self.btn_o2_cooldown = 0.0
        self.btn_temp_cooldown = 0.0
        self.btn_water_cooldown = 0.0
        self.btn_rad_cooldown = 0.0
        self.cooldown_duration = 3.0  # seconds

        # --- Emergency system (redesigned) ---
        self.emergency = None
        self.emergency_spawn_timer = 0.0
        self.emergency_spawn_interval = random.uniform(8.0, 15.0)

        # --- Critical state warnings ---
        self.critical_states = set()  # tracks which systems are critical
        self.warning_pulse = 0.0

        # --- Sound management ---
        self.sound_loaded = False
        self.ambient_playing = False
        self.last_alert_time = 0.0
        self.alert_cooldown = 2.0  # minimum seconds between alert sounds

        # --- Win/Lose state ---
        self.level_failed = False
        self.level_complete = False
        self.survival_timer = 0.0
        self.win_duration = 60.0  # 90 seconds to win
        self._played_win_sound = False

        # --- Buttons with new colors ---
        btn_size_ratio = (0.16, 0.07)
        click_sound = pygame.Sound(resource_path("assets/sound/sfx/button_click.mp3"))

        self.btn_o2 = Button(
            color=Colors.CYBER_BLUE,
            hover_color=Colors.DARK_BLUE,
            function=self._fix_o2,
            text="O2 Filter",
            font=self.game.font,
            font_color=Colors.FROST_WHITE,
            call_on_release=True,
            click_sound=click_sound,
            size_ratio=btn_size_ratio,
            screen_size=self.game.size,
            border_radius=8,
        )
        self.btn_temp = Button(
            color=Colors.VIOLET_GLOW,
            hover_color=Colors.TECH_PURPLE,
            function=self._fix_temp,
            text="Temp Adj",
            font=self.game.font,
            font_color=Colors.FROST_WHITE,
            call_on_release=True,
            click_sound=click_sound,
            size_ratio=btn_size_ratio,
            screen_size=self.game.size,
            border_radius=8,
        )
        self.btn_water = Button(
            color=Colors.ICE_BLUE,
            hover_color=Colors.CYBER_BLUE,
            function=self._fix_water,
            text="H2O Recycle",
            font=self.game.font,
            font_color=Colors.DEEP_SPACE_BLUE,
            call_on_release=True,
            click_sound=click_sound,
            size_ratio=btn_size_ratio,
            screen_size=self.game.size,
            border_radius=8,
        )
        self.btn_radshield = Button(
            color=Colors.TECH_PURPLE,
            hover_color=Colors.DARK_PURPLE,
            function=self._fix_radiation,
            text="Rad Shield",
            font=self.game.font,
            font_color=Colors.FROST_WHITE,
            call_on_release=True,
            click_sound=click_sound,
            size_ratio=btn_size_ratio,
            screen_size=self.game.size,
            border_radius=8,
        )

        self.next_button = Button(
            color=Colors.DARK_GREEN,
            function=self.game.sm.next_state,
            text="Next Level",
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

        # --- Title and instructions ---
        line_sizes = (25, 30)
        self.text_block = MultiLine(
            lines=[
                TextLine(
                    text="LIFE SUPPORT SYSTEMS",
                    font=self.game.font,
                    base_ratio=line_sizes[0],
                    color=Colors.ELECTRIC_BLUE,
                    game_size=self.game.size,
                ),
                TextLine(
                    text=f"Maintain critical systems for {self.win_duration} seconds",
                    font=self.game.font,
                    base_ratio=line_sizes[1],
                    color=Colors.ICE_BLUE,
                    game_size=self.game.size,
                ),
            ],
            start_y_ratio=0.025,
            line_spacing_ratio=0.0185,
            game_size=self.game.size,
        )

        # --- Visual effects ---
        self.particles = []  # for visual polish

        # Initial scaling
        self._scale_images()
        self._scale_controls()

    # ----------------- Lifecycle -----------------
    def startup(self):
        pygame.display.set_caption(self.name.value)
        self.fade_transition.startup()
        self.btn_o2.startup()
        self.btn_temp.startup()
        self.btn_water.startup()
        self.btn_radshield.startup()
        self.next_button.startup()

        # Disable the Button's internal click sound (we play click only when action succeeds)
        # Some Button implementations expose the attr directly; if yours doesn't this will be a no-op.
        try:
            self.btn_o2.click_sound = None
            self.btn_temp.click_sound = None
            self.btn_water.click_sound = None
            self.btn_radshield.click_sound = None
        except Exception:
            pass

        # Reset all state
        self.o2 = 100.0
        self.temp = 100.0
        self.water = 100.0
        self.radiation = 0.0
        self.survival_timer = 0.0
        self.level_failed = False
        self.level_complete = False
        self._played_win_sound = False
        self.emergency = None
        self.emergency_spawn_timer = 0.0
        self.emergency_spawn_interval = random.uniform(8.0, 15.0)
        self.critical_states.clear()
        self.particles.clear()

        # Reset cooldowns
        self.btn_o2_cooldown = 0.0
        self.btn_temp_cooldown = 0.0
        self.btn_water_cooldown = 0.0
        self.btn_rad_cooldown = 0.0

        # Load sounds safely (includes "click" now)
        self._load_sounds()

        # Start ambient music
        try:
            pygame.mixer.music.load(
                resource_path("assets/sound/music/ambient_space.mp3")
            )
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1, fade_ms=1000)
            self.ambient_playing = True
        except Exception as e:
            logger.warning(f"Could not load ambient music: {e}")

    def cleanup(self):
        # Stop sounds gracefully
        try:
            pygame.mixer.music.fadeout(500)
        except:
            pass

    def _load_sounds(self):
        """Load all sound effects with error handling (adds click sound)."""
        if self.sound_loaded:
            return

        sounds_to_load = [
            ("alert", "assets/sound/sfx/alert_warning.mp3"),
            ("fixed", "assets/sound/sfx/emergency_fix.mp3"),
            ("win", "assets/sound/sfx/win.mp3"),
            (
                "click",
                "assets/sound/sfx/button_click.mp3",
            ),  # used when action actually occurs
        ]

        for sound_name, sound_path in sounds_to_load:
            try:
                self.game.sound_manager.load_sound(
                    sound_name, resource_path(sound_path)
                )
            except Exception as e:
                logger.warning(f"Could not load sound '{sound_name}': {e}")

        self.sound_loaded = True

    # ----------------- Scaling -----------------
    def _scale_images(self):
        """Scale icons to current screen size"""
        w, h = self.game.size
        icon_size = int(min(w, h) * 0.08)

        self.icon_o2 = pygame.transform.smoothscale(
            self.icon_o2_orig, (icon_size, icon_size)
        )
        self.icon_temp = pygame.transform.smoothscale(
            self.icon_temp_orig, (icon_size, icon_size)
        )
        self.icon_water = pygame.transform.smoothscale(
            self.icon_water_orig, (icon_size, icon_size)
        )
        self.icon_rad = pygame.transform.smoothscale(
            self.icon_rad_orig, (icon_size, icon_size)
        )

        self.icon_o2_rect = self.icon_o2.get_rect()
        self.icon_temp_rect = self.icon_temp.get_rect()
        self.icon_water_rect = self.icon_water.get_rect()
        self.icon_rad_rect = self.icon_rad.get_rect()

    def _scale_controls(self):
        """Position icons and buttons with more vertical spacing to avoid overlap"""
        w, h = self.game.size

        # Increase vertical spacing so items don't overlap
        grid_y_start = 0.30
        grid_spacing_x = 0.28
        grid_spacing_y = 0.35

        positions = [
            (0.25, grid_y_start),  # O2 - top left
            (0.75, grid_y_start),  # Temp - top right
            (0.25, grid_y_start + grid_spacing_y),  # Water - bottom left
            (0.75, grid_y_start + grid_spacing_y),  # Rad - bottom right
        ]

        self.icon_o2_rect.center = (int(w * positions[0][0]), int(h * positions[0][1]))
        self.icon_temp_rect.center = (
            int(w * positions[1][0]),
            int(h * positions[1][1]),
        )
        self.icon_water_rect.center = (
            int(w * positions[2][0]),
            int(h * positions[2][1]),
        )
        self.icon_rad_rect.center = (int(w * positions[3][0]), int(h * positions[3][1]))

        # Buttons below icons (bigger offset)
        btn_offset = int(h * 0.18)

        self.btn_o2.pos_ratio = (
            positions[0][0],
            (self.icon_o2_rect.centery + btn_offset) / h,
        )
        self.btn_temp.pos_ratio = (
            positions[1][0],
            (self.icon_temp_rect.centery + btn_offset) / h,
        )
        self.btn_water.pos_ratio = (
            positions[2][0],
            (self.icon_water_rect.centery + btn_offset) / h,
        )
        self.btn_radshield.pos_ratio = (
            positions[3][0],
            (self.icon_rad_rect.centery + btn_offset) / h,
        )

        # Update button sizes
        self.btn_o2.update(self.game.size)
        self.btn_temp.update(self.game.size)
        self.btn_water.update(self.game.size)
        self.btn_radshield.update(self.game.size)

    # ----------------- Input -----------------
    def get_event(self, event: pygame.event.Event):
        # Allow restart when failed
        if self.level_failed:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Restart the mission
                    self.startup()
            return

        if self.level_complete:
            self.next_button.get_event(event)

        self.btn_o2.get_event(event)
        self.btn_temp.get_event(event)
        self.btn_water.get_event(event)
        self.btn_radshield.get_event(event)

        # Admin emergency trigger
        if event.type == pygame.KEYDOWN and self.game.admin:
            if event.key == pygame.K_e and (event.mod & pygame.KMOD_CTRL):
                self._spawn_emergency(
                    random.choice(["o2", "temp", "water", "radiation"])
                )
            if event.key == pygame.K_d and (event.mod & pygame.KMOD_CTRL):
                self.level_complete = True

    # ----------------- Update -----------------
    def update(self, screen, dt):
        # If GIF delay accidentally left large, reduce to reasonable frame interval:
        if hasattr(self, "bg_frame_delay") and self.bg_frame_delay > 1.0:
            # likely value from earlier bug — use ~120ms per frame
            self.bg_frame_delay = 0.12

        if self.level_failed or self.level_complete:
            self.game.sound_manager.stop_sound("alert")
            self.fade_transition.set_size(self.game.size)
            self.fade_transition.update(dt)
            return

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

        # Update cooldowns
        self.btn_o2_cooldown = max(0.0, self.btn_o2_cooldown - dt)
        self.btn_temp_cooldown = max(0.0, self.btn_temp_cooldown - dt)
        self.btn_water_cooldown = max(0.0, self.btn_water_cooldown - dt)
        self.btn_rad_cooldown = max(0.0, self.btn_rad_cooldown - dt)

        # Decay systems
        decay_mult = 1.0
        if self.emergency:
            decay_mult = 2.5  # emergencies accelerate decay

        self.o2 = max(0.0, self.o2 - self.o2_decay * decay_mult * dt)
        self.temp = max(0.0, self.temp - self.temp_decay * decay_mult * dt)
        self.water = max(0.0, self.water - self.water_decay * decay_mult * dt)
        self.radiation = min(
            100.0, self.radiation + self.rad_increase * decay_mult * dt
        )

        # Check for critical states
        self._update_critical_states()

        # Handle emergencies
        if self.emergency:
            self._update_emergency(dt)
        else:
            self.emergency_spawn_timer += dt
            if self.emergency_spawn_timer >= self.emergency_spawn_interval:
                self._spawn_emergency(
                    random.choice(["o2", "temp", "water", "radiation"])
                )
                self.emergency_spawn_timer = 0.0
                self.emergency_spawn_interval = random.uniform(10.0, 18.0)

        # Check fail conditions
        if self.o2 <= 0 or self.temp <= 0 or self.water <= 0 or self.radiation >= 100:
            self.level_failed = True
            logger.info("LifeSupport: Mission failed - system critical")
            return

        # Win condition: survive for win_duration with all systems above threshold
        safe_threshold = all(
            [self.o2 > 20, self.temp > 20, self.water > 20, self.radiation < 80]
        )

        if safe_threshold:
            self.survival_timer += dt
        else:
            self.survival_timer = max(0.0, self.survival_timer - dt * 0.5)

        if self.survival_timer >= self.win_duration:
            self.level_complete = True
            logger.info("LifeSupport: Mission complete!")

        # Update visual effects
        self.warning_pulse += dt * 3
        self._update_particles(dt)

        # Rescale if needed (increase spacing to avoid overlap)
        self._scale_images()
        self._scale_controls()
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

    def _update_critical_states(self):
        """Track which systems are in critical condition"""
        self.critical_states.clear()

        if self.o2 < 30:
            self.critical_states.add("o2")
        if self.temp < 30:
            self.critical_states.add("temp")
        if self.water < 30:
            self.critical_states.add("water")
        if self.radiation > 70:
            self.critical_states.add("radiation")

        # Play alert sound if critical (with cooldown)
        if (
            self.critical_states
            and (pygame.time.get_ticks() / 1000.0 - self.last_alert_time)
            > self.alert_cooldown
        ):
            try:
                self.game.sound_manager.play_sound("alert", volume=0.3)
                self.last_alert_time = pygame.time.get_ticks() / 1000.0
            except:
                pass

    def _update_emergency(self, dt):
        """Handle active emergency"""
        if not self.emergency:
            return

        self.emergency["timer"] += dt

        # Emergency affects specific system more severely
        etype = self.emergency["type"]
        impact = self.emergency["severity"] * dt

        if etype == "o2":
            self.o2 = max(0.0, self.o2 - impact)
        elif etype == "temp":
            self.temp = max(0.0, self.temp - impact)
        elif etype == "water":
            self.water = max(0.0, self.water - impact)
        elif etype == "radiation":
            self.radiation = min(100.0, self.radiation + impact)

        # Auto-fail if emergency not resolved in time
        if self.emergency["timer"] >= self.emergency["time_to_fail"]:
            self.level_failed = True
            logger.info(f"LifeSupport: Failed - emergency timeout ({etype})")

    def _update_particles(self, dt):
        """Update visual particle effects"""
        # Remove dead particles
        self.particles = [p for p in self.particles if p["life"] > 0]

        # Update existing particles
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt

    # ----------------- Drawing -----------------
    def draw(self, screen: pygame.Surface):
        # Background
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (0, 0))

        # Dark overlay for better contrast
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((*Colors.DEEP_SPACE_BLUE, 100))
        screen.blit(overlay, (0, 0))

        # Title
        self.text_block.draw(screen)

        # Draw timer and progress
        self._draw_timer(screen)

        # Draw system panels
        self._draw_system_panels(screen)

        # Draw particles
        self._draw_particles(screen)

        # Draw buttons
        if not self.level_failed and not self.level_complete:
            self._draw_buttons_with_cooldowns(screen)

        # Emergency overlay
        if self.emergency:
            self._draw_emergency_overlay(screen)

        # Win/Lose screens
        if self.level_failed:
            self._draw_fail_ui(screen)
        elif self.level_complete:
            self._draw_win_ui(screen)

        # Fade
        self.fade_transition.draw(screen)

    def _draw_timer(self, screen):
        """Draw survival timer and progress bar"""
        w, h = self.game.size
        progress = min(1.0, self.survival_timer / self.win_duration)

        # Progress bar
        bar_w = int(w * 0.6)
        bar_h = int(h * 0.025)
        bar_x = (w - bar_w) // 2
        bar_y = int(h * 0.12)

        # Background
        pygame.draw.rect(
            screen, Colors.DEEP_PURPLE, (bar_x, bar_y, bar_w, bar_h), border_radius=5
        )

        # Progress fill
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            color = Colors.ELECTRIC_BLUE if progress < 0.9 else Colors.ICE_BLUE
            pygame.draw.rect(
                screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5
            )

        # Border
        pygame.draw.rect(
            screen, Colors.CYBER_BLUE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5
        )

        # Timer text
        time_left = max(0, self.win_duration - self.survival_timer)
        timer_text = f"{int(time_left)}s remaining"
        timer_surf, timer_rect = self.game.font.render(
            timer_text, Colors.ICE_BLUE, size=self.game.size_depended(20)
        )
        timer_rect.centerx = w // 2
        timer_rect.top = bar_y + bar_h + 8  # below progress bar
        screen.blit(timer_surf, timer_rect)

    def _draw_system_panels(self, screen):
        """Draw icons and status bars for each system (with more label spacing)"""
        systems = [
            (self.icon_o2, self.icon_o2_rect, "", self.o2, Colors.ICE_BLUE, "o2"),
            (
                self.icon_temp,
                self.icon_temp_rect,
                "",
                self.temp,
                Colors.VIOLET_GLOW,
                "temp",
            ),
            (
                self.icon_water,
                self.icon_water_rect,
                "",
                self.water,
                Colors.CYBER_BLUE,
                "water",
            ),
            (
                self.icon_rad,
                self.icon_rad_rect,
                "",
                100 - self.radiation,
                Colors.TECH_PURPLE,
                "radiation",
            ),
        ]

        for icon, rect, label, value, color, sys_type in systems:
            # Warning pulse for critical systems
            is_critical = sys_type in self.critical_states
            if is_critical:
                pulse = abs(math.sin(self.warning_pulse))
                glow_surf = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf,
                    (*Colors.CRITICAL_RED, int(100 * pulse)),
                    (glow_surf.get_width() // 2, glow_surf.get_height() // 2),
                    (rect.w + 24) // 2,
                )
                screen.blit(
                    glow_surf,
                    (
                        rect.centerx - glow_surf.get_width() // 2,
                        rect.centery - glow_surf.get_height() // 2,
                    ),
                )

            # Icon
            screen.blit(icon, rect)

            # Status bar below icon
            bar_w = int(rect.w * 1.5)
            bar_h = int(self.game.height * 0.015)
            bar_x = rect.centerx - bar_w // 2
            bar_y = rect.bottom + int(self.game.height * 0.014)  # slightly larger gap

            # Background
            pygame.draw.rect(
                screen,
                Colors.DEEP_PURPLE,
                (bar_x, bar_y, bar_w, bar_h),
                border_radius=3,
            )

            # Fill
            fill_w = int(bar_w * (value / 100.0))
            if fill_w > 0:
                # Color based on status
                if value < 30:
                    bar_color = Colors.CRITICAL_RED
                elif value < 60:
                    bar_color = Colors.WARNING_AMBER
                else:
                    bar_color = color

                pygame.draw.rect(
                    screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3
                )

            # Border
            pygame.draw.rect(
                screen,
                Colors.FROST_WHITE,
                (bar_x, bar_y, bar_w, bar_h),
                1,
                border_radius=3,
            )

            # Label and percentage (push label down a bit more)
            label_surf, label_rect = self.game.font.render(
                f"{label} {int(value)}%",
                Colors.FROST_WHITE,
                size=self.game.size_depended(20),
            )
            label_rect.centerx = rect.centerx
            label_rect.top = (
                bar_y + bar_h + int(self.game.height * 0.025)
            )  # increased gap
            screen.blit(label_surf, label_rect)

    def _draw_buttons_with_cooldowns(self, screen):
        """Draw buttons with cooldown overlays"""
        buttons_cooldowns = [
            (self.btn_o2, self.btn_o2_cooldown),
            (self.btn_temp, self.btn_temp_cooldown),
            (self.btn_water, self.btn_water_cooldown),
            (self.btn_radshield, self.btn_rad_cooldown),
        ]

        for btn, cooldown in buttons_cooldowns:
            btn.draw(screen)

            # Cooldown overlay
            if cooldown > 0:
                progress = cooldown / self.cooldown_duration
                overlay = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
                overlay.fill((*Colors.DEEP_SPACE_BLUE, int(180 * progress)))
                screen.blit(overlay, btn.rect.topleft)

                # Cooldown text
                cd_text = f"{cooldown:.1f}s"
                cd_surf, cd_rect = self.game.font.render(
                    cd_text, Colors.DISK_RED, size=self.game.size_depended(16)
                )
                cd_rect.center = btn.rect.center
                screen.blit(cd_surf, cd_rect)

    def _draw_emergency_overlay(self, screen):
        """Draw emergency warning"""
        w, h = self.game.size

        # Pulsing dark overlay
        pulse = abs(math.sin(pygame.time.get_ticks() / 200.0))
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((*Colors.CRITICAL_RED, int(60 * pulse)))
        screen.blit(overlay, (0, 0))

        # Warning border
        border_thickness = int(10 * pulse) + 5
        pygame.draw.rect(
            screen,
            Colors.CRITICAL_RED,
            (0, 0, w, h),
            border_thickness,
        )

        # Emergency text
        etype = self.emergency["type"].upper().replace("RADIATION", "RAD")
        time_left = self.emergency["time_to_fail"] - self.emergency["timer"]

        title = f"! {etype} EMERGENCY !"
        subtitle = f"Resolve in {int(time_left)}s or fail!"

        title_surf, title_rect = self.game.font.render(
            title, Colors.CRITICAL_RED, size=self.game.size_depended(28)
        )
        sub_surf, sub_rect = self.game.font.render(
            subtitle, Colors.WARNING_AMBER, size=self.game.size_depended(20)
        )

        title_rect.center = (w // 2, int(h * 0.85))
        sub_rect.center = (w // 2, int(h * 0.90))

        # Background for text
        bg_rect = pygame.Rect(
            title_rect.left - 20,
            title_rect.top - 10,
            max(title_rect.width, sub_rect.width) + 40,
            sub_rect.bottom - title_rect.top + 20,
        )
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((*Colors.DEEP_SPACE_BLUE, 200))
        screen.blit(bg_surf, bg_rect.topleft)

        screen.blit(title_surf, title_rect)
        screen.blit(sub_surf, sub_rect)

    def _draw_fail_ui(self, screen):
        """Draw failure screen + restart hint"""
        w, h = self.game.size
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((*Colors.DEEP_SPACE_BLUE, 220))
        screen.blit(overlay, (0, 0))

        # Ratios for vertical positioning
        title_ratio = 0.4  # 40% down from top
        sub_ratio = 0.5  # 50% down from top
        hint_ratio = 0.6  # 60% down from top

        # Title
        title_surf, title_rect = self.game.font.render(
            "SYSTEMS FAILURE", Colors.CRITICAL_RED, size=self.game.size_depended(8)
        )
        title_rect.center = (w // 2, int(h * title_ratio))
        screen.blit(title_surf, title_rect)

        # Subtext
        sub_surf, sub_rect = self.game.font.render(
            "Mission Failed", Colors.ICE_BLUE, size=self.game.size_depended(18)
        )
        sub_rect.center = (w // 2, int(h * sub_ratio))
        screen.blit(sub_surf, sub_rect)

        # Hint
        hint_surf, hint_rect = self.game.font.render(
            "Press R to restart", Colors.WARNING_AMBER, size=self.game.size_depended(14)
        )
        hint_rect.center = (w // 2, int(h * hint_ratio))
        screen.blit(hint_surf, hint_rect)

    def _draw_win_ui(self, screen):
        """Draw victory screen with ratio-based positioning and next button"""
        w, h = screen.get_size()

        # Overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((*Colors.DEEP_SPACE_BLUE, 200))
        screen.blit(overlay, (0, 0))

        # Play win sound only once
        if not self._played_win_sound:
            try:
                self.game.sound_manager.play_sound("win")
            except:
                pass
            self._played_win_sound = True

        # Title text
        title_surf, title_rect = self.game.font.render(
            "SYSTEMS STABLE", Colors.ELECTRIC_BLUE, size=self.game.size_depended(8)
        )
        title_rect.center = (w // 2, int(h * 0.4))  # 40% down from top
        screen.blit(title_surf, title_rect)

        # Subtitle text
        sub_surf, sub_rect = self.game.font.render(
            "Mission Complete!", Colors.ICE_BLUE, size=self.game.size_depended(18)
        )
        sub_rect.center = (w // 2, int(h * 0.5))  # 50% down from top
        screen.blit(sub_surf, sub_rect)

        # --- Draw next button below subtitle ---
        text_rect_on_screen = sub_rect.copy()
        text_rect_on_screen.topleft = sub_rect.topleft

        self.next_button.pos_ratio = (
            text_rect_on_screen.centerx / w,
            (
                text_rect_on_screen.bottom + text_rect_on_screen.height * 0.6
            )  # 60% down from top
            / h,
        )

        self.next_button.update((w, h))
        self.next_button.draw(screen)

    # ----------------- Button Actions -----------------
    def _fix_o2(self):
        if self.btn_o2_cooldown > 0:
            return

        # play click only when action is allowed
        try:
            self.game.sound_manager.play_sound("click", volume=0.3)
        except:
            pass

        self.o2 = min(100.0, self.o2 + 35.0)
        self.btn_o2_cooldown = self.cooldown_duration

        try:
            self.game.sound_manager.play_sound("fixed", volume=0.5)
        except:
            pass

        if self.emergency and self.emergency["type"] == "o2":
            self._resolve_emergency()

    def _fix_temp(self):
        if self.btn_temp_cooldown > 0:
            return

        try:
            self.game.sound_manager.play_sound("click", volume=0.3)
        except:
            pass

        self.temp = min(100.0, self.temp + 35.0)
        self.btn_temp_cooldown = self.cooldown_duration

        try:
            self.game.sound_manager.play_sound("fixed", volume=0.5)
        except:
            pass

        if self.emergency and self.emergency["type"] == "temp":
            self._resolve_emergency()

    def _fix_water(self):
        if self.btn_water_cooldown > 0:
            return

        try:
            self.game.sound_manager.play_sound("click", volume=0.3)
        except:
            pass

        self.water = min(100.0, self.water + 40.0)
        self.btn_water_cooldown = self.cooldown_duration

        try:
            self.game.sound_manager.play_sound("fixed", volume=0.5)
        except:
            pass

        if self.emergency and self.emergency["type"] == "water":
            self._resolve_emergency()

    def _fix_radiation(self):
        if self.btn_rad_cooldown > 0:
            return

        try:
            self.game.sound_manager.play_sound("click", volume=0.3)
        except:
            pass

        self.radiation = max(0.0, self.radiation - 40.0)
        self.btn_rad_cooldown = self.cooldown_duration

        try:
            self.game.sound_manager.play_sound("fixed", volume=0.5)
        except:
            pass

        if self.emergency and self.emergency["type"] == "radiation":
            self._resolve_emergency()

    # ----------------- Emergency Helpers -----------------
    def _spawn_emergency(self, etype: str):
        """Spawn a critical emergency"""
        severity = random.uniform(8.0, 15.0)
        time_to_fail = random.uniform(10.0, 20.0)

        self.emergency = {
            "type": etype,
            "severity": severity,
            "time_to_fail": time_to_fail,
            "timer": 0.0,
        }

        logger.info(
            f"LifeSupport: Emergency - {etype} (severity={severity:.1f}, "
            f"time_to_fail={time_to_fail:.1f}s)"
        )

        try:
            if self.emergency:  # only play alert if emergency is active
                self.game.sound_manager.play_sound("alert", volume=0.6)
        except:
            pass

    def _resolve_emergency(self):
        """Successfully resolve the active emergency"""
        if not self.emergency:
            return

        etype = self.emergency["type"]
        logger.info(f"LifeSupport: Emergency resolved - {etype}")

        # spawn particles at the related icon
        try:
            center = {
                "o2": self.icon_o2_rect.center,
                "temp": self.icon_temp_rect.center,
                "water": self.icon_water_rect.center,
                "radiation": self.icon_rad_rect.center,
            }[etype]
        except Exception:
            center = (self.game.width // 2, self.game.height // 2)

        # burst of particles
        for _ in range(12):
            self._spawn_particle(
                center[0] + random.randint(-8, 8),
                center[1] + random.randint(-8, 8),
                Colors.FROST_WHITE,
                size=random.randint(3, 6),
                lifetime=random.uniform(0.5, 1.2),
            )

        # play fixed/stabilize sound
        try:
            self.game.sound_manager.stop_sound("alert")
            self.game.sound_manager.play_sound("fixed", volume=0.6)
        except:
            pass

        # clear emergency and reset spawn timers
        self.emergency = None
        self.emergency_spawn_timer = 0.0
        self.emergency_spawn_interval = random.uniform(12.0, 20.0)

    def _spawn_particle(self, x, y, color, size=4, lifetime=0.6):
        """Spawn a single particle for effects"""
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(20, 60)
        self.particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": color,
                "size": size,
                "life": lifetime,
            }
        )

    def _update_particles(self, dt):
        """Update and remove expired particles"""
        new_particles = []
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] > 0:
                new_particles.append(p)
        self.particles = new_particles

    def _draw_particles(self, screen):
        """Render particles"""
        for p in self.particles:
            # fade by life/initial lifetime approximation (simple)
            alpha = int(max(0, min(255, 255 * (p["life"] / 1.2))))
            surf = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            col = (p["color"][0], p["color"][1], p["color"][2], alpha)
            pygame.draw.circle(
                surf, col, (p["size"] // 2, p["size"] // 2), p["size"] // 2
            )
            screen.blit(surf, (p["x"], p["y"]))

    # ----------------- Helpers -----------------
    def _system_bar_position(self, rect):
        """Return a tuple for status bar under icon"""
        bar_w = int(rect.w * 1.5)
        bar_h = int(self.game.height * 0.015)
        bar_x = rect.centerx - bar_w // 2
        bar_y = rect.bottom + int(self.game.height * 0.015)
        return bar_x, bar_y, bar_w, bar_h

    # ----------------- Optional Debug -----------------
    def debug_print(self):
        """Print current system status (for dev)"""
        logger.debug(
            f"O2: {self.o2:.1f}, Temp: {self.temp:.1f}, Water: {self.water:.1f}, "
            f"Radiation: {self.radiation:.1f}, Emergency: {self.emergency}"
        )
