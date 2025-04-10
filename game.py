import pygame
import sys
import random
import threading
import time
import queue
from abc import ABC, abstractmethod
import pyttsx3

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1024, 768
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
LIGHT_BLUE = (100, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (230, 230, 230)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CHIAPAS PUEDE - Alfabetización Digital")

font_large = pygame.font.SysFont('Arial', 40)
font_medium = pygame.font.SysFont('Arial', 30)
font_small = pygame.font.SysFont('Arial', 20)

class GameNotifier:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify(self, event):
        for observer in self.observers:
            observer.on_event(event)

class VoiceSystem:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 140)
        self.queue = queue.Queue()
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            text = self.queue.get()
            if text == "STOP":
                break
            self.engine.say(text)
            self.engine.runAndWait()

    def speak(self, text):
        self.queue.put(text)

    def stop(self):
        self.queue.put("STOP")

    def on_event(self, event):
        if event["type"] == "speak":
            self.speak(event["text"])

class AnimationSystem:
    def __init__(self):
        self.animations = []
        self.running = True
        threading.Thread(target=self._update_animations, daemon=True).start()

    def _update_animations(self):
        while self.running:
            for anim in self.animations:
                anim.update()
            time.sleep(0.016) 

    def add_animation(self, anim):
        self.animations.append(anim)

class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.elapsed = 0
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.elapsed = time.time() - self.start_time
            time.sleep(0.1)

    def get_time(self):
        return time.strftime("%M:%S", time.gmtime(self.elapsed))

class DraggableItem:
    def __init__(self, text, x, y, width=100, height=50, color=LIGHT_BLUE):
        self.text = text
        self.original_pos = (x, y)
        self.rect = pygame.Rect(x, y, width, height)
        self.dragging = False
        self.placed = False
        self.color = color

    def draw(self, surface):
        color = GREEN if self.placed else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)
        
        text_surf = font_medium.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def reset_position(self):
        self.rect.x, self.rect.y = self.original_pos
        self.placed = False
        self.dragging = False

class DropSpace:
    def __init__(self, x, y, width=100, height=50, correct_text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.correct_text = correct_text
        self.occupied = False
        self.current_item = None

    def draw(self, surface):
        color = GRAY
        if self.occupied:
            color = GREEN if self.current_item.text == self.correct_text else RED
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)


# (El código anterior permanece igual hasta la definición de las clases Level)

class Level1: 
    def __init__(self, notifier):
        self.notifier = notifier
        self.words = ["caminar", "pelota", "ventana", "caballo", "escuela", "jardín", "montaña", "libro"]
        self.setup_level()
        self.time_limit = 120  # 2 minutos en segundos (60 FPS)
        self.time_penalty = 10  # Segundos penalizados por error
        self.error_count = 0

    def setup_level(self):
        self.notifier.notify({"type": "speak", "text": "Nivel 1: Completa las palabras con sílabas. Tienes tiempo limitado."})
        self.word = random.choice(self.words)
        self.syllables = self._split_syllables(self.word)
        self.spaces = []
        self.draggables = []
        self.completed = False
        self.start_time = time.time()

        start_x = WIDTH // 2 - (len(self.syllables) * 110) // 2
        for i, syll in enumerate(self.syllables):
            self.spaces.append(DropSpace(start_x + i * 110, 200, correct_text=syll))

        # Más sílabas distractoras
        all_syllables = self.syllables + ["la", "lo", "pa", "sa", "ti", "ma", "no", "que", "de", "en"]
        random.shuffle(all_syllables)
        for i, syll in enumerate(all_syllables):
            x = 150 + (i % 5) * 150
            y = 350 + (i // 5) * 80
            self.draggables.append(DraggableItem(syll, x, y))

    def _split_syllables(self, word):
        # División más inteligente de sílabas
        syllables = []
        vowels = "aeiouáéíóú"
        current = ""
        for i, char in enumerate(word):
            current += char
            if i < len(word)-1:
                next_char = word[i+1]
                # Reglas básicas de silabificación
                if (char in vowels and next_char not in vowels) or (char not in vowels and next_char in vowels):
                    syllables.append(current)
                    current = ""
        if current:
            syllables.append(current)
        return syllables if len(syllables) > 1 else [word[:len(word)//2], word[len(word)//2:]]

    def update(self):
        current_time = time.time()
        elapsed = current_time - self.start_time
        remaining = max(0, self.time_limit - elapsed - (self.error_count * self.time_penalty))
        
        if remaining <= 0 and not self.completed:
            self.notifier.notify({"type": "speak", "text": "Tiempo agotado. Inténtalo de nuevo."})
            self.setup_level()  # Reiniciar nivel
            return
            
        if not self.completed:
            all_occupied = all(space.occupied for space in self.spaces)
            all_correct = all(space.occupied and space.current_item.text == space.correct_text 
                             for space in self.spaces)
            if all_correct:
                self.completed = True
                self.notifier.notify({"type": "speak", "text": f"¡Correcto! La palabra es {self.word}"})
            elif all_occupied:
                self.error_count += 1
                self.notifier.notify({"type": "speak", "text": "Palabra incorrecta. Pierdes 10 segundos. Intenta de nuevo."})
                for space in self.spaces:
                    if space.current_item and space.current_item.text != space.correct_text:
                        space.current_item.reset_position()
                        space.current_item.placed = False
                        space.occupied = False
                        space.current_item = None

    def draw(self, surface):
        for space in self.spaces:
            space.draw(surface)
        for item in self.draggables:
            if not item.dragging:
                item.draw(surface)

        current_time = time.time()
        elapsed = current_time - self.start_time
        remaining = max(0, self.time_limit - elapsed - (self.error_count * self.time_penalty))
        mins, secs = divmod(int(remaining), 60)
        time_text = font_medium.render(f"Tiempo: {mins:02d}:{secs:02d}", True, RED if remaining < 30 else BLACK)
        surface.blit(time_text, (WIDTH - 150, 20))

        word_display = " ".join(["_"*len(s) for s in self.syllables])
        word_text = font_large.render(f"Palabra: {word_display}", True, BLUE)
        surface.blit(word_text, (WIDTH//2 - word_text.get_width()//2, 150))

        if self.completed:
            complete_text = font_medium.render("¡Palabra completada!", True, GREEN)
            surface.blit(complete_text, (WIDTH//2 - complete_text.get_width()//2, 500))
        
        # Mostrar contador de errores
        error_text = font_small.render(f"Errores: {self.error_count}", True, RED)
        surface.blit(error_text, (WIDTH - 150, 50))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                for item in self.draggables:
                    if item.rect.collidepoint(event.pos) and not item.placed:
                        item.dragging = True
                        self.draggables.remove(item)
                        self.draggables.append(item)
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for item in self.draggables:
                    if item.dragging:
                        item.dragging = False
                        placed = False

                        for space in self.spaces:
                            if space.rect.collidepoint(event.pos) and not space.occupied:
                                item.rect.center = space.rect.center
                                item.placed = True
                                space.occupied = True
                                space.current_item = item
                                placed = True
                                self.notifier.notify({"type": "speak", "text": item.text})
                                break

                        if not placed:
                            item.reset_position()

                        break

        elif event.type == pygame.MOUSEMOTION:
            for item in self.draggables:
                if item.dragging:
                    item.rect.center = event.pos

        return self.completed

class Level2:  
    def __init__(self, notifier):
        self.notifier = notifier
        self.attempts = 3  # Intentos permitidos (MOVIDO ARRIBA DE setup_level)
        self.current_attempt = 0
        # Palabras más largas y complejas
        self.words = ["computadora", "telefono", "elefante", "mariposa", "biblioteca", "universidad"]
        self.setup_level()

    def setup_level(self):
        self.notifier.notify({"type": "speak", "text": f"Nivel 2: Ordena las sílabas para formar la palabra. Tienes {self.attempts} intentos."})
        self.word = random.choice(self.words)
        self.syllables = self._split_syllables(self.word)
        self.correct_syllables = self.syllables.copy()
        random.shuffle(self.syllables)
        self.spaces = []
        self.draggables = []
        self.completed = False
        self.error_message = ""
        self.error_timer = 0
        
        start_x = WIDTH // 2 - (len(self.syllables) * 110) // 2
        for i, correct_syll in enumerate(self.correct_syllables):
            self.spaces.append(DropSpace(start_x + i * 110, 200, correct_text=correct_syll))
        
        # Más sílabas distractoras
        distractors = ["ción", "mente", "ando", "iendo", "mente", "ción", "ando"]
        all_syllables = self.syllables + random.sample(distractors, min(3, len(distractors)))
        random.shuffle(all_syllables)
        
        for i, syll in enumerate(all_syllables):
            x = 150 + (i % 4) * 180
            y = 350 + (i // 4) * 80
            self.draggables.append(DraggableItem(syll, x, y, color=YELLOW))

    # Resto de los métodos (update, draw, handle_event) permanecen igual
    def _split_syllables(self, word):
        # División más natural de sílabas
        syllables = []
        current = ""
        for char in word:
            current += char
            if len(current) >= 2 and (char in "aeiouáéíóú" or random.random() < 0.5):
                syllables.append(current)
                current = ""
        if current:
            syllables.append(current)
        return syllables

    def update(self):
        if self.error_timer > 0:
            self.error_timer -= 1
            
        if not self.completed:
            all_filled = all(space.occupied for space in self.spaces)
            if all_filled:
                formed_word = ""
                for space in self.spaces:
                    if space.current_item:
                        formed_word += space.current_item.text
                
                if formed_word == self.word:
                    self.completed = True
                    self.notifier.notify({"type": "speak", "text": f"¡Excelente! La palabra es {self.word}"})
                else:
                    self.current_attempt += 1
                    if self.current_attempt >= self.attempts:
                        self.error_message = f"¡Se acabaron los intentos! La palabra era: {self.word}"
                        self.notifier.notify({"type": "speak", "text": f"Se acabaron los intentos. La palabra era {self.word}"})
                        time.sleep(2)
                        self.completed = True  # Pasar al siguiente nivel aunque haya fallado
                    else:
                        self.error_message = f"¡Palabra incorrecta! Intentos restantes: {self.attempts - self.current_attempt}"
                        self.error_timer = 180
                        self.notifier.notify({"type": "speak", "text": f"Palabra incorrecta. Te quedan {self.attempts - self.current_attempt} intentos"})
                        
                        for space in self.spaces:
                            if space.occupied:
                                space.current_item.reset_position()
                                space.occupied = False
                                space.current_item = None

    def draw(self, surface):
        for space in self.spaces:
            space.draw(surface)
        for item in self.draggables:
            if not item.dragging:
                item.draw(surface)
        
        hint = font_medium.render(f"Pista: La palabra tiene {len(self.word)} letras", True, BLACK)
        surface.blit(hint, (WIDTH//2 - hint.get_width()//2, 150))

        attempts_text = font_small.render(f"Intentos: {self.attempts - self.current_attempt}/{self.attempts}", True, RED)
        surface.blit(attempts_text, (WIDTH - 150, 20))

        if self.completed:
            complete_text = font_medium.render("¡Palabra correcta!", True, GREEN)
            surface.blit(complete_text, (WIDTH//2 - complete_text.get_width()//2, 500))
        elif self.error_timer > 0:
            error_surf = font_medium.render(self.error_message, True, RED)
            alert_rect = pygame.Rect(WIDTH//2 - error_surf.get_width()//2 - 20, 490, 
                                   error_surf.get_width() + 40, error_surf.get_height() + 20)
            pygame.draw.rect(surface, (255, 220, 220), alert_rect, border_radius=10)
            pygame.draw.rect(surface, RED, alert_rect, 2, border_radius=10)
            surface.blit(error_surf, (WIDTH//2 - error_surf.get_width()//2, 500))

    def handle_event(self, event):
        if self.error_timer > 0 and event.type == pygame.MOUSEBUTTONDOWN:
            self.error_timer = 0
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for item in self.draggables:
                    if item.rect.collidepoint(event.pos) and not item.placed:
                        item.dragging = True
                        self.draggables.remove(item)
                        self.draggables.append(item)
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for item in self.draggables:
                    if item.dragging:
                        item.dragging = False
                        placed = False
                        
                        for space in self.spaces:
                            if space.rect.collidepoint(event.pos) and not space.occupied:
                                item.rect.center = space.rect.center
                                item.placed = True
                                space.occupied = True
                                space.current_item = item
                                placed = True
                                self.notifier.notify({"type": "speak", "text": item.text})
                                break
                        
                        if not placed:
                            item.reset_position()
                        
                        break

        elif event.type == pygame.MOUSEMOTION:
            for item in self.draggables:
                if item.dragging:
                    item.rect.center = event.pos

        return self.completed

class Level3:  
    def __init__(self, notifier):
        self.notifier = notifier
        self.word_groups = {
            "computadora": ["pato", "codo", "rata", "puma", "toro", "copa", "dama", "moda"],
            "universidad": ["nube", "vida", "risa", "duna", "seda", "vino", "rueda"],
            "electricidad": ["cielo", "tierra", "clima", "dieta", "circo", "tela", "dile"]
        }
        self.setup_level()
        self.required_words = 3  # Ahora requiere 5 palabras en lugar de 3
        self.incorrect_attempts = 0
        self.max_incorrect = 3  # Máximo de intentos incorrectos permitidos

    def setup_level(self):
        self.big_word = random.choice(list(self.word_groups.keys()))
        self.possible_words = self.word_groups[self.big_word]
        self.found_words = []
        self.letter_spaces = []
        self.draggable_letters = []
        self.completed = False
        self.error_message = ""
        self.error_timer = 0
        
        self.notifier.notify({"type": "speak", "text": f"Nivel 3: Forma {self.required_words} palabras con letras de {self.big_word}. Máximo {self.max_incorrect} errores."})
        
        for i in range(10):  # Más espacios para palabras más largas
            self.letter_spaces.append(DropSpace((WIDTH//2 - 250) + i * 50, 250, width=40, height=40))
        
        letters = list(self.big_word)
        random.shuffle(letters)
        for i, letter in enumerate(letters):
            x = 150 + (i % 8) * 80
            y = 350 + (i // 8) * 60
            self.draggable_letters.append(DraggableItem(letter, x, y, width=40, height=40))

    def update(self):
        if self.error_timer > 0:
            self.error_timer -= 1
            
        if not self.completed and len(self.found_words) >= self.required_words:
            self.completed = True
            self.notifier.notify({"type": "speak", "text": f"¡Nivel completado! Has encontrado {self.required_words} palabras"})
        
        if self.incorrect_attempts >= self.max_incorrect and not self.completed:
            self.error_message = f"¡Demasiados errores! Encontradas: {len(self.found_words)}/{self.required_words}"
            self.error_timer = 180
            self.notifier.notify({"type": "speak", "text": f"Demasiados errores. Encontradas {len(self.found_words)} palabras de {self.required_words}"})
            time.sleep(3)
            self.completed = True  # Pasar al siguiente nivel aunque no haya completado

    def draw(self, surface):
        surface.fill(WHITE)
        
        title = font_large.render("Nivel 3: Forma palabras cortas", True, BLUE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        big_word_text = font_large.render(self.big_word.upper(), True, BLUE)
        surface.blit(big_word_text, (WIDTH//2 - big_word_text.get_width()//2, 80))
        
        hint = font_small.render(f"Encuentra {self.required_words} palabras usando letras de: {self.big_word}", True, BLACK)
        surface.blit(hint, (WIDTH//2 - hint.get_width()//2, 130))
        
        current_word = self.get_current_word()
        word_text = font_medium.render(f"Palabra actual: {current_word}", True, BLACK)
        surface.blit(word_text, (WIDTH//2 - word_text.get_width()//2, 170))
        
        # Mostrar contador de errores
        errors_text = font_small.render(f"Errores: {self.incorrect_attempts}/{self.max_incorrect}", True, RED)
        surface.blit(errors_text, (WIDTH - 150, 20))
        
        # Botones más grandes y claros
        pygame.draw.rect(surface, GREEN, (300, 300, 120, 50), border_radius=10)
        pygame.draw.rect(surface, RED, (450, 300, 120, 50), border_radius=10)
        
        check_text = font_small.render("Verificar", True, BLACK)
        reset_text = font_small.render("Borrar", True, BLACK)
        surface.blit(check_text, (360 - check_text.get_width()//2, 325 - check_text.get_height()//2))
        surface.blit(reset_text, (510 - reset_text.get_width()//2, 325 - reset_text.get_height()//2))
        
        found_text = font_medium.render(f"Palabras encontradas: {len(self.found_words)}/{self.required_words}", True, BLACK)
        surface.blit(found_text, (50, 400))
        
        for i, word in enumerate(self.found_words):
            word_surf = font_small.render(word, True, GREEN)
            surface.blit(word_surf, (50, 440 + i * 30))
        
        for space in self.letter_spaces:
            space.draw(surface)
        for letter in self.draggable_letters:
            if not letter.dragging:
                letter.draw(surface)
                
        if self.error_timer > 0:
            error_surf = font_medium.render(self.error_message, True, RED)
            alert_rect = pygame.Rect(WIDTH//2 - error_surf.get_width()//2 - 20, 490, 
                                   error_surf.get_width() + 40, error_surf.get_height() + 20)
            pygame.draw.rect(surface, (255, 220, 220), alert_rect, border_radius=10)
            pygame.draw.rect(surface, RED, alert_rect, 2, border_radius=10)
            surface.blit(error_surf, (WIDTH//2 - error_surf.get_width()//2, 500))

    def handle_event(self, event):
        if self.error_timer > 0 and event.type == pygame.MOUSEBUTTONDOWN:
            self.error_timer = 0
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Área del botón Verificar
                if 300 <= event.pos[0] <= 420 and 300 <= event.pos[1] <= 350:
                    current_word = self.get_current_word()
                    if len(current_word) >= 2:
                        if current_word in self.possible_words and current_word not in self.found_words:
                            self.found_words.append(current_word)
                            self.notifier.notify({"type": "speak", "text": f"Correcto: {current_word}"})
                            self.reset_letters()
                        else:
                            self.incorrect_attempts += 1
                            self.error_message = "Esa palabra no es válida o ya la encontraste"
                            self.error_timer = 180
                            self.notifier.notify({"type": "speak", "text": "Esa palabra no es válida o ya la encontraste"})
                            self.reset_letters()
                    return False
                
                # Área del botón Borrar
                if 450 <= event.pos[0] <= 570 and 300 <= event.pos[1] <= 350:
                    self.reset_letters()
                    return False
                
                for letter in self.draggable_letters:
                    if letter.rect.collidepoint(event.pos) and not letter.placed:
                        letter.dragging = True
                        self.draggable_letters.remove(letter)
                        self.draggable_letters.append(letter)
                        break

        # (El resto del método handle_event permanece igual)

# (El resto del código permanece igual)
    def __init__(self, notifier):
        self.notifier = notifier
        self.word_groups = {
            "mariposa": ["mar", "piso", "rosa", "sopa", "ramo"],
            "elefante": ["ele", "fante", "tela", "lefa", "flan"],
            "biblioteca": ["libro", "teca", "bota", "beca", "lote"]
        }
        self.setup_level()


    def setup_level(self):
        self.big_word = random.choice(list(self.word_groups.keys()))
        self.possible_words = self.word_groups[self.big_word]
        self.found_words = []
        self.letter_spaces = []
        self.draggable_letters = []
        self.completed = False
        self.error_message = ""
        self.error_timer = 0
        
        self.notifier.notify({"type": "speak", "text": f"Nivel 3: Forma palabras con letras de {self.big_word}"})
        
        for i in range(8):
            self.letter_spaces.append(DropSpace((WIDTH//2 - 200) + i * 50, 250, width=40, height=40))
        
        letters = list(self.big_word)
        random.shuffle(letters)
        for i, letter in enumerate(letters):
            x = 150 + (i % 8) * 80
            y = 350 + (i // 8) * 60
            self.draggable_letters.append(DraggableItem(letter, x, y, width=40, height=40))

    def update(self):

        if self.error_timer > 0:
            self.error_timer -= 1
            
        if not self.completed and len(self.found_words) >= 3:
            self.completed = True
            self.notifier.notify({"type": "speak", "text": "¡Nivel completado! Has encontrado 3 palabras"})

    def draw(self, surface):
        surface.fill(WHITE)
        
        title = font_large.render("Nivel 3: Forma palabras cortas", True, BLUE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        big_word_text = font_large.render(self.big_word.upper(), True, BLUE)
        surface.blit(big_word_text, (WIDTH//2 - big_word_text.get_width()//2, 80))
        
        hint = font_small.render(f"Encuentra 3 palabras usando letras de: {self.big_word}", True, BLACK)
        surface.blit(hint, (WIDTH//2 - hint.get_width()//2, 130))
        
        current_word = self.get_current_word()
        word_text = font_medium.render(f"Palabra actual: {current_word}", True, BLACK)
        surface.blit(word_text, (WIDTH//2 - word_text.get_width()//2, 170))
        
        pygame.draw.rect(surface, GREEN, (300, 300, 100, 40), border_radius=10)
        pygame.draw.rect(surface, RED, (420, 300, 100, 40), border_radius=10)
        
        check_text = font_small.render("Verificar", True, BLACK)
        reset_text = font_small.render("Borrar", True, BLACK)
        surface.blit(check_text, (350 - check_text.get_width()//2, 320 - check_text.get_height()//2))
        surface.blit(reset_text, (470 - reset_text.get_width()//2, 320 - reset_text.get_height()//2))
        
        found_text = font_medium.render("Palabras encontradas:", True, BLACK)
        surface.blit(found_text, (50, 400))
        
        for i, word in enumerate(self.found_words):
            word_surf = font_small.render(word, True, GREEN)
            surface.blit(word_surf, (50, 440 + i * 30))
        
        for space in self.letter_spaces:
            space.draw(surface)
        for letter in self.draggable_letters:
            if not letter.dragging:
                letter.draw(surface)
                
        if self.error_timer > 0:
            error_surf = font_medium.render(self.error_message, True, RED)
            alert_rect = pygame.Rect(WIDTH//2 - error_surf.get_width()//2 - 20, 490, 
                                   error_surf.get_width() + 40, error_surf.get_height() + 20)
            pygame.draw.rect(surface, (255, 220, 220), alert_rect, border_radius=10)
            pygame.draw.rect(surface, RED, alert_rect, 2, border_radius=10)
            surface.blit(error_surf, (WIDTH//2 - error_surf.get_width()//2, 500))

    def get_current_word(self):
        return "".join([space.current_item.text for space in self.letter_spaces if space.occupied])

    def reset_letters(self):
        for space in self.letter_spaces:
            if space.occupied:
                space.current_item.reset_position()
                space.occupied = False
                space.current_item = None

    def handle_event(self, event):
        if self.error_timer > 0 and event.type == pygame.MOUSEBUTTONDOWN:
            self.error_timer = 0
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if 300 <= event.pos[0] <= 400 and 300 <= event.pos[1] <= 340:
                    current_word = self.get_current_word()
                    if len(current_word) >= 2:
                        if current_word in self.possible_words and current_word not in self.found_words:
                            self.found_words.append(current_word)
                            self.notifier.notify({"type": "speak", "text": f"Correcto: {current_word}"})
                            self.reset_letters()
                        else:
                            self.error_message = "Esa palabra no es válida"
                            self.error_timer = 180
                            self.notifier.notify({"type": "speak", "text": "Esa palabra no es válida"})
                            self.reset_letters()
                    return False
                
                if 420 <= event.pos[0] <= 520 and 300 <= event.pos[1] <= 340:
                    self.reset_letters()
                    return False
                
                for letter in self.draggable_letters:
                    if letter.rect.collidepoint(event.pos) and not letter.placed:
                        letter.dragging = True
                        self.draggable_letters.remove(letter)
                        self.draggable_letters.append(letter)
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for letter in self.draggable_letters:
                    if letter.dragging:
                        letter.dragging = False
                        placed = False
                        
                        for space in self.letter_spaces:
                            if space.rect.collidepoint(event.pos) and not space.occupied:
                                letter.rect.center = space.rect.center
                                letter.placed = True
                                space.occupied = True
                                space.current_item = letter
                                placed = True
                                self.notifier.notify({"type": "speak", "text": letter.text})
                                break
                        
                        if not placed:
                            letter.reset_position()
                        
                        break

        elif event.type == pygame.MOUSEMOTION:
            for letter in self.draggable_letters:
                if letter.dragging:
                    letter.rect.center = event.pos

        return self.completed

class ChiapasGame:
    def __init__(self):
        self.notifier = GameNotifier()
        self.voice = VoiceSystem()
        self.animations = AnimationSystem()
        self.timer = Timer()
        self.notifier.add_observer(self.voice)
        
        self.levels = [Level1, Level2, Level3]
        self.current_level_index = 0
        self.level_instance = self.levels[self.current_level_index](self.notifier)
        self.running = True
        self.score = 0

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                level_completed = self.level_instance.handle_event(event)
                if level_completed:
                    self.score += 100
                    self.next_level()
            
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        self.voice.stop()
        pygame.quit()
        sys.exit()

    def next_level(self):
        self.current_level_index += 1
        if self.current_level_index < len(self.levels):
            self.level_instance = self.levels[self.current_level_index](self.notifier)
        else:
            self.show_final_screen()

    def show_final_screen(self):
        self.notifier.notify({"type": "speak", "text": "¡Felicidades! Has completado todos los niveles"})
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.voice.stop()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  
                        self.__init__()
                        self.run()
                    elif event.key == pygame.K_ESCAPE: 
                        self.voice.stop()
                        pygame.quit()
                        sys.exit()
            
            screen.fill(WHITE)
            title = font_large.render("¡Juego Completado!", True, BLUE)
            score = font_medium.render(f"Puntuación final: {self.score}", True, BLACK)
            time_played = font_medium.render(f"Tiempo: {self.timer.get_time()}", True, BLACK)
            instructions = font_small.render("Presiona R para reiniciar o ESC para salir", True, BLACK)
            
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
            screen.blit(score, (WIDTH//2 - score.get_width()//2, HEIGHT//2 - 30))
            screen.blit(time_played, (WIDTH//2 - time_played.get_width()//2, HEIGHT//2 + 10))
            screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 80))
            
            pygame.display.flip()

    def update(self):
        self.level_instance.update()

    def draw(self):
        screen.fill(WHITE)
        self.level_instance.draw(screen)
        
        time_text = font_small.render(f"Tiempo: {self.timer.get_time()}", True, BLACK)
        level_text = font_small.render(f"Nivel: {self.current_level_index + 1}/3", True, BLACK)
        score_text = font_small.render(f"Puntos: {self.score}", True, BLACK)
        
        screen.blit(time_text, (20, 20))
        screen.blit(level_text, (20, 50))
        screen.blit(score_text, (20, 80))
        
        if self.current_level_index == 1:
            pygame.draw.rect(screen, GREEN, (450, 400, 100, 40), border_radius=10)
            verify_text = font_small.render("Verificar", True, BLACK)
            screen.blit(verify_text, (500 - verify_text.get_width()//2, 420 - verify_text.get_height()//2))

if __name__ == "__main__":
    game = ChiapasGame()
    game.run()