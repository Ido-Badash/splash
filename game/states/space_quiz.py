import pygame
import random
from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from game.utils import resource_path, load_gif_from_bytes, heb
from .states import States
from game.widgets import Button


class SpaceQuiz(BaseState):
    def __init__(self, game=None):
        super().__init__(States.SPACE_QUIZ, game)

        # Fade transition
        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
            speed=100,
        )

        # --- Background GIF ---
        bg_gif_path = resource_path("assets/gifs/space_quiz_bg.gif")
        with open(bg_gif_path, "rb") as f:
            gif_bytes = f.read()
        self.bg_gif = load_gif_from_bytes(gif_bytes)
        self.bg_frame_index = 0
        self.bg_frame_delay = 0.08
        self.bg_frame_timer = 0
        self.bg_gif_surf = None

        # --- Quiz Questions (Localized) ---
        self.questions = [
            {
                "question": heb("מה יוצר את הדחף החזק שמרים טיל רב עוצמה מהקרקע?"),
                "options": [
                    heb("הסיבוב של כדור הארץ מתחת לטיל"),
                    heb("שחרור מהיר של גזים חמים המיוצרים משריפת כמויות גדולות של דלק"),
                    heb("לחץ אוויר הדוחף את הטיל כלפי מעלה"),
                    heb("כוחות מגנטיים הנוצרים על ידי מנועי הטיל"),
                ],
                "correct": 1,  # Index of correct answer (B)
            },
            {
                "question": heb(
                    "מדוע תקשורת בחלל מסתמכת על לוויינים, לייזרים וגלי רדיו?"
                ),
                "options": [
                    heb("מכיוון שגלי קול נעים מהר יותר בחלל"),
                    heb("מכיוון שאין כוח משיכה בחלל"),
                    heb("מכיוון שאין אטמוספירה שגלי קול יכולים לנוע דרכה"),
                    heb(
                        "מכיוון שלוויינים אינם יכולים לתקשר דרך האטמוספירה של כדור הארץ"
                    ),
                ],
                "correct": 2,  # Index of correct answer (C)
            },
            {
                "question": heb("כיצד פועלת בדרך כלל מערכת התקשורת בחלל?"),
                "options": [
                    heb(
                        "לוויינים יוצרים אותות משלהם ושולחים אותם באופן אקראי לכדור הארץ"
                    ),
                    heb(
                        "אות נשלח מהקרקע, הלוויין קולט ומגביר אותו, ואז שולח אותו לנקודה אחרת על כדור הארץ"
                    ),
                    heb("אותות יכולים לנוע רק מלוויין אחד לאחר, לא לכדור הארץ"),
                    heb("לוויינים מקליטים הודעות ומשמיעים אותן בחזרה שעות מאוחר יותר"),
                ],
                "correct": 1,  # Index of correct answer (B)
            },
            {
                "question": heb("מהי מטרת מערכות תמיכת החיים בחללית?"),
                "options": [
                    heb("לשגר את החללית למסלול"),
                    heb("להגן על החללית מפני מטאורים"),
                    heb("לספק לאסטרונאוטים את התנאים הדרושים כדי לשרוד בחלל"),
                    heb("להפעיל את מערכות התקשורת"),
                ],
                "correct": 2,  # Index of correct answer (C)
            },
        ]

        # Quiz state
        self.current_question = 0
        self.selected_answer = None
        self.show_feedback = False
        self.feedback_timer = 0.0
        self.feedback_duration = 1.5
        self.is_correct = False
        self.quiz_complete = False
        self._played_win_sound = False

        # Visual effects
        self.particles = []
        self.glow_pulse = 0.0
        self.shake_intensity = 0.0

        # Answer buttons
        self.answer_buttons = []
        self._create_answer_buttons()

        # Next button (shown after quiz complete) (Localized)
        self.next_button = Button(
            color=Colors.ELECTRIC_BLUE,
            function=self.game.sm.next_state,
            text=heb("המשך משימה"),
            font=self.game.font,
            font_color=Colors.FROST_WHITE,
            font_size=int(self.game.size_depended(25)),  # Add font size
            call_on_release=True,
            hover_color=Colors.CYBER_BLUE,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.ELECTRIC_BLUE,
            clicked_font_color=Colors.FROST_WHITE,
            click_sound=pygame.Sound(
                resource_path("assets/sound/sfx/button_click.mp3")
            ),
            size_ratio=(0.25, 0.08),
            screen_size=self.game.size,
            border_radius=12,
            border_thickness=3,
            border_color=Colors.ICE_BLUE,
        )

        # Load sounds
        self._load_sounds()

        # Question counter visual
        self.progress_dots = []

    def _load_sounds(self):
        """Load quiz sounds"""
        try:
            self.game.sound_manager.load_sound(
                "quiz_correct", resource_path("assets/sound/sfx/quiz_correct.mp3")
            )
            self.game.sound_manager.load_sound(
                "quiz_wrong", resource_path("assets/sound/sfx/quiz_wrong.mp3")
            )
            self.game.sound_manager.load_sound(
                "quiz_complete", resource_path("assets/sound/sfx/quiz_complete.mp3")
            )
            self.game.sound_manager.load_sound(
                "win", resource_path("assets/sound/sfx/win.mp3")
            )
        except Exception as e:
            logger.warning(f"Could not load quiz sounds: {e}")

    def _create_answer_buttons(self):
        """Create buttons for answer options (A, B, C, D)"""
        self.answer_buttons = []
        # The labels A, B, C, D are likely not translated in a Hebrew UI,
        # but if they needed to be, you would use heb("א"), heb("ב"), etc.
        # For a quiz, Roman letters are often kept for indexing.
        labels = ["א", "ב", "ג", "ד"]

        # Calculate font size for buttons
        btn_font_size = int(self.game.size_depended(18))

        for i in range(4):
            btn = Button(
                color=Colors.DEEP_PURPLE,
                function=lambda idx=i: self._select_answer(idx),
                # The label is a UI element, but usually not translated to Hebrew letters
                text=f"{labels[i]}",
                font=self.game.font,
                font_color=Colors.ICE_BLUE,
                font_size=btn_font_size,  # Pass size for FreeType fonts
                call_on_release=True,
                hover_color=Colors.VIOLET_GLOW,
                hover_font_color=Colors.FROST_WHITE,
                clicked_color=Colors.CYBER_BLUE,
                clicked_font_color=Colors.WHITE,
                size_ratio=(0.08, 0.06),
                pos_ratio=(0.1, 0.5 + i * 0.12),
                screen_size=self.game.size,
                border_radius=8,
                border_thickness=2,
                border_color=Colors.CYBER_BLUE,
                hover_border_color=Colors.ICE_BLUE,
            )
            self.answer_buttons.append(btn)

    def startup(self):
        # Localized window title
        pygame.display.set_caption(heb("מבחן ידע חלל"))
        self.fade_transition.startup()
        self.next_button.startup()

        for btn in self.answer_buttons:
            btn.startup()

        # Reset state
        self.current_question = 0
        self.selected_answer = None
        self.show_feedback = False
        self.feedback_timer = 0.0
        self.is_correct = False
        self.quiz_complete = False
        self._played_win_sound = False
        self.particles = []
        self.glow_pulse = 0.0
        self.shake_intensity = 0.0

        # Play ambient space music
        try:
            pygame.mixer.music.load(
                resource_path("assets/sound/music/aria_math_c418.mp3")
            )
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1, fade_ms=1000)
        except Exception as e:
            logger.warning(f"Could not load quiz music: {e}")

    def cleanup(self):
        try:
            pygame.mixer.music.fadeout(500)
        except:
            pass

    def get_event(self, event: pygame.event.Event):
        if self.quiz_complete:
            self.next_button.get_event(event)
            return

        if not self.show_feedback:
            for btn in self.answer_buttons:
                btn.get_event(event)

        # Admin skip
        if event.type == pygame.KEYDOWN and self.game.admin:
            if event.key == pygame.K_d and (event.mod & pygame.KMOD_CTRL):
                self.quiz_complete = True

    def update(self, screen, dt):
        # Background GIF
        self.bg_frame_timer += dt
        if self.bg_frame_timer >= self.bg_frame_delay:
            self.bg_frame_timer = 0.0
            if self.bg_gif:
                self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_gif)

        if self.bg_gif:
            bg_frame = self.bg_gif[self.bg_frame_index]
            try:
                self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)
            except Exception:
                self.bg_gif_surf = None

        # Update particles
        self._update_particles(dt)

        # Update glow pulse
        self.glow_pulse += dt * 2.0

        # Reduce shake
        self.shake_intensity = max(0.0, self.shake_intensity - dt * 10.0)

        # Update buttons
        if not self.show_feedback and not self.quiz_complete:
            for btn in self.answer_buttons:
                btn.update(self.game.size)

        # Handle feedback timer
        if self.show_feedback:
            self.feedback_timer += dt
            if self.feedback_timer >= self.feedback_duration:
                if self.is_correct:
                    self.current_question += 1
                    if self.current_question >= len(self.questions):
                        self.quiz_complete = True
                        try:
                            self.game.sound_manager.play_sound("quiz_complete")
                        except:
                            pass

                self.show_feedback = False
                self.feedback_timer = 0.0
                self.selected_answer = None

        # Update fade and next button
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        if self.quiz_complete:
            self.next_button.update(self.game.size)

    def draw(self, screen: pygame.Surface):
        # Background
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (0, 0))

        # Dark overlay
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((*Colors.DEEP_SPACE_BLUE, 150))
        screen.blit(overlay, (0, 0))

        if not self.quiz_complete:
            # Draw progress dots
            self._draw_progress(screen)

            # Draw question
            self._draw_question(screen)

            # Draw answer options
            self._draw_answers(screen)

            # Draw feedback
            if self.show_feedback:
                self._draw_feedback(screen)
        else:
            # Draw completion screen
            self._draw_completion(screen)

        # Draw particles
        self._draw_particles(screen)

        # Fade
        self.fade_transition.draw(screen)

    def _draw_progress(self, screen):
        """Draw progress dots showing current question"""
        w, h = self.game.size
        dot_size = int(min(w, h) * 0.015)
        spacing = int(dot_size * 3)
        total_width = (
            len(self.questions) * dot_size + (len(self.questions) - 1) * spacing
        )
        start_x = (w - total_width) // 2
        y = int(h * 0.08)

        for i in range(len(self.questions)):
            x = start_x + i * (dot_size + spacing)
            if i < self.current_question:
                color = Colors.ELECTRIC_BLUE
            elif i == self.current_question:
                pulse = abs(pygame.math.Vector2(1, 0).rotate(self.glow_pulse * 180).x)
                color = (
                    Colors.ICE_BLUE[0],
                    Colors.ICE_BLUE[1],
                    Colors.ICE_BLUE[2],
                )
                pygame.draw.circle(
                    screen,
                    (*color, int(100 + 100 * pulse)),
                    (x + dot_size // 2, y),
                    dot_size + 4,
                )
            else:
                color = Colors.DEEP_PURPLE

            pygame.draw.circle(screen, color, (x + dot_size // 2, y), dot_size)
            pygame.draw.circle(
                screen, Colors.CYBER_BLUE, (x + dot_size // 2, y), dot_size, 2
            )

    def _draw_question(self, screen):
        """Draw the current question with modern styling (Localized)"""
        w, h = self.game.size
        question_data = self.questions[self.current_question]

        # Question number (Localized - using f-string for number insertion)
        q_num_surf, q_num_rect = self.game.font.render(
            heb(f"שאלה {self.current_question + 1}/{len(self.questions)}"),
            Colors.ELECTRIC_BLUE,
            size=self.game.size_depended(35),
        )
        q_num_rect.centerx = w // 2
        q_num_rect.top = int(h * 0.15)
        screen.blit(q_num_surf, q_num_rect)

        # Question text with word wrap
        question_text = question_data["question"]
        max_width = int(w * 0.8)
        # Note: Word wrapping for Hebrew text can be complex due to RTL and font rendering.
        # Assuming the 'heb' function handles the visual direction and the font renderer
        # correctly measures/renders the Hebrew text.
        words = question_text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_surf, test_rect = self.game.font.render(
                test_line, Colors.WHITE, size=self.game.size_depended(22)
            )
            if test_rect.width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # Draw question lines
        line_height = int(h * 0.05)
        start_y = int(h * 0.25)

        for i, line in enumerate(lines):
            line_surf, line_rect = self.game.font.render(
                line, Colors.FROST_WHITE, size=self.game.size_depended(22)
            )
            line_rect.centerx = w // 2
            line_rect.top = start_y + i * line_height
            screen.blit(line_surf, line_rect)

    def _draw_answers(self, screen):
        """Draw answer options with labels"""
        w, h = self.game.size
        question_data = self.questions[self.current_question]
        options = question_data["options"]
        labels = ["א", "ב", "ג", "ד"]

        start_y = int(h * 0.48)
        spacing = int(h * 0.12)

        for i, (option, label) in enumerate(zip(options, labels)):
            y_pos = start_y + i * spacing

            # Update button position
            self.answer_buttons[i].pos_ratio = (0.12, y_pos / h)
            self.answer_buttons[i].update(self.game.size)

            # Highlight if selected
            if self.show_feedback and self.selected_answer == i:
                glow_color = (
                    Colors.ELECTRIC_BLUE if self.is_correct else Colors.CRITICAL_RED
                )
                glow_rect = self.answer_buttons[i].rect.inflate(20, 20)
                pygame.draw.rect(
                    screen, (*glow_color, 100), glow_rect, border_radius=12
                )

            # Draw button
            self.answer_buttons[i].draw(screen)

            # Draw option text
            text_x = int(w * 0.18)
            text_surf, text_rect = self.game.font.render(
                option, Colors.FROST_WHITE, size=self.game.size_depended(26)
            )
            text_rect.left = text_x
            text_rect.centery = y_pos + self.answer_buttons[i].rect.height // 2 - 30

            # Word wrap if too long
            if text_rect.width > w * 0.65:
                words = option.split()
                lines = []
                current_line = []
                max_width = int(w * 0.65)

                for word in words:
                    test_line = " ".join(current_line + [word])
                    test_surf, test_rect = self.game.font.render(
                        test_line, Colors.FROST_WHITE, size=self.game.size_depended(26)
                    )
                    if test_rect.width <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(" ".join(current_line))
                        current_line = [word]

                if current_line:
                    lines.append(" ".join(current_line))

                # Draw wrapped lines
                line_offset = 0
                for line in lines:
                    line_surf, line_rect = self.game.font.render(
                        line, Colors.FROST_WHITE, size=self.game.size_depended(26)
                    )
                    line_rect.left = text_x
                    line_rect.top = text_rect.top + line_offset
                    screen.blit(line_surf, line_rect)
                    line_offset += line_rect.height + 5
            else:
                screen.blit(text_surf, text_rect)

    def _draw_feedback(self, screen):
        """Draw feedback message (Localized)"""
        w, h = self.game.size

        # Create semi-transparent overlay
        feedback_overlay = pygame.Surface((w, int(h * 0.15)), pygame.SRCALPHA)

        if self.is_correct:
            feedback_overlay.fill((*Colors.ELECTRIC_BLUE, 200))
            text = heb("נכון!")
            color = Colors.FROST_WHITE
        else:
            feedback_overlay.fill((*Colors.CRITICAL_RED, 200))
            text = heb("לא נכון - נסה שוב")
            color = Colors.WHITE

        # Draw overlay
        overlay_y = int(h * 0.85)
        screen.blit(feedback_overlay, (0, overlay_y))

        # Draw border
        border_color = Colors.ELECTRIC_BLUE if self.is_correct else Colors.CRITICAL_RED
        pygame.draw.rect(screen, border_color, (0, overlay_y, w, int(h * 0.15)), 4)

        # Draw text
        text_surf, text_rect = self.game.font.render(
            text, color, size=self.game.size_depended(15)
        )
        text_rect.center = (w // 2, overlay_y + int(h * 0.075))
        screen.blit(text_surf, text_rect)

    def _draw_completion(self, screen):
        """Draw quiz completion screen (Localized)"""
        w, h = self.game.size

        # Overlay
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((*Colors.DEEP_SPACE_BLUE, 220))
        screen.blit(overlay, (0, 0))

        # Play win sound once
        if not self._played_win_sound:
            try:
                self.game.sound_manager.play_sound("win")
            except:
                pass
            self._played_win_sound = True

        # Success message (Localized)
        title_surf, title_rect = self.game.font.render(
            heb("תדריך משימה הושלם"),
            Colors.ELECTRIC_BLUE,
            size=self.game.size_depended(12),
        )
        title_rect.center = (w // 2, int(h * 0.35))
        screen.blit(title_surf, title_rect)

        # Subtitle (Localized)
        sub_surf, sub_rect = self.game.font.render(
            heb("ידע אומת - אושר לשיגור"),
            Colors.ICE_BLUE,
            size=self.game.size_depended(20),
        )
        sub_rect.center = (w // 2, int(h * 0.45))
        screen.blit(sub_surf, sub_rect)

        # Draw next button
        self.next_button.pos_ratio = (0.5, 0.6)
        self.next_button.update(self.game.size)
        self.next_button.draw(screen)

    def _select_answer(self, index):
        """Handle answer selection"""
        if self.show_feedback or self.quiz_complete:
            return

        self.selected_answer = index
        correct_answer = self.questions[self.current_question]["correct"]
        self.is_correct = index == correct_answer
        self.show_feedback = True
        self.feedback_timer = 0.0

        if self.is_correct:
            try:
                self.game.sound_manager.play_sound("quiz_correct")
            except:
                pass
            # Spawn success particles
            self._spawn_success_particles()
        else:
            try:
                self.game.sound_manager.play_sound("quiz_wrong")
            except:
                pass
            # Shake effect
            self.shake_intensity = 5.0

    def _spawn_success_particles(self):
        """Spawn particles for correct answer"""
        w, h = self.game.size
        center_x = w // 2
        center_y = h // 2

        for _ in range(30):
            angle = random.uniform(0, 360)
            speed = random.uniform(50, 150)
            self.particles.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "vx": speed * pygame.math.Vector2(1, 0).rotate(angle).x,
                    "vy": speed * pygame.math.Vector2(1, 0).rotate(angle).y,
                    "life": random.uniform(0.5, 1.2),
                    "color": random.choice(
                        [Colors.ELECTRIC_BLUE, Colors.ICE_BLUE, Colors.FROST_WHITE]
                    ),
                    "size": random.randint(3, 8),
                }
            )

    def _update_particles(self, dt):
        """Update particle positions and lifetime"""
        new_particles = []
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] > 0:
                new_particles.append(p)
        self.particles = new_particles

    def _draw_particles(self, screen):
        """Draw particles with fade"""
        for p in self.particles:
            alpha = int(255 * (p["life"] / 1.2))
            surf = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            color = (*p["color"], alpha)
            pygame.draw.circle(
                surf, color, (p["size"] // 2, p["size"] // 2), p["size"] // 2
            )
            screen.blit(surf, (int(p["x"]), int(p["y"])))
