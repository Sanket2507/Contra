import pygame as pg
import numpy as np
import pickle
import os
from collections import deque
import random

class DifficultyManager:
    def __init__(self, game):
        self.game = game
        
        # Current difficulty level (start very easy)
        self.difficulty_level = 1
        
        # Base difficulty parameters
        self.base_enemy_health = 2  # Very low health for level 1
        self.base_enemy_fire_rate = 1500  # Very slow fire rate at level 1
        self.base_enemy_bullet_damage = 1
        self.base_enemy_bullet_speed = 300  # Slow bullets at level 1
        self.base_player_bullet_damage = 2  # Player starts stronger
        
        # Challenge tracking
        self.challenge_start_time = 0
        self.challenge_active = False
        self.challenge_duration = 180  # 3 minutes in seconds
        self.challenge_completed = False
        self.challenge_failed = False
        
        # Player performance metrics
        self.player_metrics = {
            'damage_taken': 0,
            'enemies_killed': 0,
            'shots_fired': 0,
            'shots_hit': 0,
            'time_alive': 0,
            'distance_traveled': 0,
            'last_evaluation_time': 0,
            'challenge_time': 0
        }
        
        # Player position tracking
        self.last_position = None
        
        # State-action value function (Q-table)
        self.q_table = {}
        
        # Experience replay buffer
        self.replay_buffer = deque(maxlen=1000)
        
        # Load previous Q-table if exists
        self.load_model()
        
        # Warning signs
        self.show_warning = False
        self.warning_time = 0
        self.warning_duration = 3000  # 3 seconds
        
        # Warning sign assets
        try:
            self.warning_surface = pg.image.load('./graphics/warning.png').convert_alpha()
        except:
            # Create a simple warning sign if image doesn't exist
            self.warning_surface = pg.Surface((200, 100), pg.SRCALPHA)
            pg.draw.polygon(self.warning_surface, (255, 255, 0), [(100, 10), (10, 90), (190, 90)], 0)
            pg.draw.polygon(self.warning_surface, (0, 0, 0), [(100, 10), (10, 90), (190, 90)], 4)
            font = pg.font.Font(None, 60)
            text = font.render("!", True, (0, 0, 0))
            text_rect = text.get_rect(center=(100, 50))
            self.warning_surface.blit(text, text_rect)
            
        self.warning_rect = self.warning_surface.get_rect(center=(640, 100))
        
        # UI elements for difficulty prompt
        self.font = pg.font.Font(None, 32)
        self.small_font = pg.font.Font(None, 24)
        self.show_prompt = False
        self.prompt_time = 0
        self.prompt_duration = 8000  # 8 seconds
        self.prompt_type = "difficulty"  # "difficulty" or "challenge"
        
        # Initial application of difficulty settings
        self.apply_difficulty_parameters()
        
        # Time between difficulty evaluations (in seconds)
        self.evaluation_interval = 60  # Evaluate every minute
        
        # Performance thresholds
        self.good_performance_threshold = 0.7
        self.poor_performance_threshold = 0.3
        
        # Accuracy threshold for challenge
        self.accuracy_threshold = 0.85  # 85% accuracy
        
        # Feedback messages
        self.feedback_message = ""
        self.feedback_time = 0
        self.feedback_duration = 5000  # 5 seconds
    
    def load_model(self):
        if os.path.exists('difficulty_model.pkl'):
            try:
                with open('difficulty_model.pkl', 'rb') as f:
                    self.q_table = pickle.load(f)
                print("Difficulty model loaded successfully")
            except Exception as e:
                print(f"Failed to load difficulty model: {e}")
    
    def save_model(self):
        try:
            with open('difficulty_model.pkl', 'wb') as f:
                pickle.dump(self.q_table, f)
            print("Difficulty model saved successfully")
        except Exception as e:
            print(f"Failed to save difficulty model: {e}")
    
    def get_state(self):
        # Discretize player metrics to create state
        accuracy = self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired'])
        accuracy_level = min(5, int(accuracy * 5))  # 0-5 accuracy levels
        
        health_percentage = self.game.my_player.health / self.game.my_player.max_health
        health_level = min(5, int(health_percentage * 5))  # 0-5 health levels
        
        # Calculate kills per minute
        time_in_minutes = max(0.1, self.player_metrics['time_alive'] / 60)
        kills_per_minute = self.player_metrics['enemies_killed'] / time_in_minutes
        kill_level = min(5, int(kills_per_minute * 2))  # 0-5 kill levels
        
        return (self.difficulty_level, accuracy_level, health_level, kill_level)
    
    def get_q_value(self, state, action):
        if state not in self.q_table:
            self.q_table[state] = [0, 0, 0]  # [increase, decrease, maintain]
        return self.q_table[state][action]
    
    def update_q_value(self, state, action, reward, next_state):
        # Q-learning update
        current_q = self.get_q_value(state, action)
        
        # Get max Q-value for next state
        next_max_q = max([self.get_q_value(next_state, a) for a in range(3)])
        
        # Q-learning formula
        new_q = current_q + 0.1 * (reward + 0.9 * next_max_q - current_q)
        
        # Update Q-table
        if state not in self.q_table:
            self.q_table[state] = [0, 0, 0]
        self.q_table[state][action] = new_q
    
    def choose_action(self, state):
        # Epsilon-greedy policy
        if random.random() < 0.2:
            return random.randint(0, 2)  # Random action
        else:
            # Choose action with highest Q-value
            q_values = [self.get_q_value(state, a) for a in range(3)]
            return q_values.index(max(q_values))
    
    def update_metrics(self, deltaTime):
        # Update time alive
        self.player_metrics['time_alive'] += deltaTime
        
        # Update distance traveled
        if self.last_position is not None:
            current_position = self.game.my_player.rect.center
            distance = ((current_position[0] - self.last_position[0]) ** 2 + 
                        (current_position[1] - self.last_position[1]) ** 2) ** 0.5
            self.player_metrics['distance_traveled'] += distance
        self.last_position = self.game.my_player.rect.center
        
        # Update challenge time if active
        if self.challenge_active:
            self.player_metrics['challenge_time'] += deltaTime
            
            # Check if challenge time exceeded
            if self.player_metrics['challenge_time'] >= self.challenge_duration:
                self.challenge_active = False
                self.challenge_failed = True
                self.feedback_message = "Challenge failed! Better luck next time."
                self.feedback_time = pg.time.get_ticks()
    
    def get_performance_score(self):
        # Calculate a comprehensive performance score based on player metrics
        
        # Calculate accuracy (capped at 100%)
        accuracy = min(1.0, self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired']))
        
        # Health percentage
        health_percentage = self.game.my_player.health / self.game.my_player.max_health
        
        # Kills per minute
        time_in_minutes = max(0.1, self.player_metrics['time_alive'] / 60)
        kills_per_minute = self.player_metrics['enemies_killed'] / time_in_minutes
        
        # Damage efficiency (how much damage taken per enemy killed)
        damage_efficiency = max(0, 1 - (self.player_metrics['damage_taken'] / 
                                        max(1, self.player_metrics['enemies_killed'])))
        
        # Weight the components based on their importance
        weights = {
            'accuracy': 0.25,
            'health': 0.25,
            'kills': 0.3,
            'damage_efficiency': 0.2
        }
        
        # Calculate normalized scores (0-1 range)
        scores = {
            'accuracy': accuracy,
            'health': health_percentage,
            'kills': min(1.0, kills_per_minute / 5),  # 5 kills per minute is considered excellent
            'damage_efficiency': damage_efficiency
        }
        
        # Calculate weighted average score
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score
    
    def get_reward(self):
        # Calculate reward based on player performance
        performance_score = self.get_performance_score()
        
        # Base reward on performance
        base_reward = performance_score * 2 - 1  # Maps 0-1 to -1 to 1
        
        # Additional reward for balanced challenge
        optimal_health = 0.75
        health_percentage = self.game.my_player.health / self.game.my_player.max_health
        health_balance = 1 - abs(health_percentage - optimal_health)
        
        # Combine rewards
        total_reward = base_reward * 0.7 + health_balance * 0.3
        
        return total_reward
    
    def check_challenge_completion(self):
        # Check if player completed challenge within time limit
        if self.challenge_active:
            # Calculate accuracy
            accuracy = self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired'])
            
            # Check if challenge completed successfully
            if accuracy >= self.accuracy_threshold and self.player_metrics['challenge_time'] <= self.challenge_duration:
                self.challenge_active = False
                self.challenge_completed = True
                self.show_prompt = True
                self.prompt_type = "challenge"
                self.prompt_time = pg.time.get_ticks()
                return True
        
        return False
    
    def start_challenge(self):
        self.challenge_active = True
        self.challenge_completed = False
        self.challenge_failed = False
        self.player_metrics['challenge_time'] = 0
        self.challenge_start_time = self.player_metrics['time_alive']
        self.feedback_message = f"Challenge started! Maintain 85% accuracy for 3 minutes."
        self.feedback_time = pg.time.get_ticks()
    
    def suggest_difficulty_change(self):
        performance_score = self.get_performance_score()
        
        # Check if we should start a challenge
        if not self.challenge_active and not self.challenge_completed and not self.challenge_failed:
            accuracy = self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired'])
            if accuracy >= 0.75 and self.difficulty_level < 3:  # Good accuracy but still at low difficulty
                self.start_challenge()
                return "challenge"
        
        # Get state and choose action based on Q-learning
        state = self.get_state()
        action = self.choose_action(state)
        
        # Override with common sense rules for early game
        if self.difficulty_level == 1 and performance_score > self.good_performance_threshold:
            # If player is doing well at level 1, suggest increase
            action = 0  # Increase difficulty
        elif performance_score < self.poor_performance_threshold and self.difficulty_level > 1:
            # If player is struggling and not at minimum difficulty, suggest decrease
            action = 1  # Decrease difficulty
        
        if action == 0 and self.difficulty_level < 10:  # Increase difficulty
            self.show_warning = True
            self.warning_time = pg.time.get_ticks()
            self.show_prompt = True
            self.prompt_type = "difficulty"
            self.prompt_time = pg.time.get_ticks()
            
            # Set feedback message
            self.feedback_message = "You're doing well! Consider increasing the difficulty?"
            return "increase"
        elif action == 1 and self.difficulty_level > 1:  # Decrease difficulty
            self.feedback_message = "Difficulty has been decreased to give you a better challenge."
            self.apply_difficulty_change("decrease")
            self.feedback_time = pg.time.get_ticks()
            return "decrease"
        else:  # Maintain difficulty
            self.feedback_message = "Difficulty remains the same. You're playing at a good level."
            self.feedback_time = pg.time.get_ticks()
            return "maintain"
    
    def apply_difficulty_change(self, change):
        old_state = self.get_state()
        old_difficulty = self.difficulty_level
        
        if change == "increase":
            self.difficulty_level = min(10, self.difficulty_level + 1)
            self.feedback_message = f"Difficulty increased to level {self.difficulty_level}. Enemies are stronger now!"
        elif change == "decrease":
            self.difficulty_level = max(1, self.difficulty_level - 1)
            self.feedback_message = f"Difficulty decreased to level {self.difficulty_level}. You'll find the game a bit easier."
        elif change == "challenge_success":
            # Significant increase for challenge success
            self.difficulty_level = min(10, self.difficulty_level + 2)
            self.base_enemy_bullet_damage += 1  # Permanent increase in enemy bullet damage
            self.feedback_message = f"Challenge completed! Difficulty jumped to level {self.difficulty_level}. Enemy bullets now deal more damage!"
        else:
            self.feedback_message = f"Difficulty maintained at level {self.difficulty_level}."
        
        self.feedback_time = pg.time.get_ticks()
        
        # Apply difficulty changes to game parameters
        self.apply_difficulty_parameters()
        
        # Calculate reward
        reward = self.get_reward()
        
        # Get new state
        new_state = self.get_state()
        
        # Update Q-table
        action = 0 if change == "increase" or change == "challenge_success" else 1 if change == "decrease" else 2
        self.update_q_value(old_state, action, reward, new_state)
        
        # Store experience in replay buffer
        self.replay_buffer.append((old_state, action, reward, new_state))
        
        # Perform experience replay
        self.experience_replay()
        
        # Save model if difficulty changed
        if self.difficulty_level != old_difficulty:
            self.save_model()
        
        # Reset performance metrics for next evaluation
        self.reset_metrics()
    
    def experience_replay(self):
        # Perform batch learning from replay buffer
        if len(self.replay_buffer) > 32:
            batch = random.sample(self.replay_buffer, 32)
            for state, action, reward, next_state in batch:
                self.update_q_value(state, action, reward, next_state)
    
    def reset_metrics(self):
        # Store the time of this evaluation
        self.player_metrics['last_evaluation_time'] = self.player_metrics['time_alive']
        
        # Reset performance metrics but keep time alive
        self.player_metrics['damage_taken'] = 0
        self.player_metrics['enemies_killed'] = 0
        self.player_metrics['shots_fired'] = 0
        self.player_metrics['shots_hit'] = 0
    
    def apply_difficulty_parameters(self):
        # Scale parameters based on difficulty level
        if self.difficulty_level == 1:
            # Very easy at level 1
            health_factor = 0.7
            fire_rate_factor = 1.5
            bullet_speed_factor = 0.8
        else:
            # Progressive scaling after level 1
            health_factor = 0.7 + (self.difficulty_level - 1) * 0.3  # 30% increase per level after level 1
            fire_rate_factor = 1.5 - (self.difficulty_level - 1) * 0.15  # 15% decrease per level (faster firing)
            bullet_speed_factor = 0.8 + (self.difficulty_level - 1) * 0.2  # 20% increase per level
        
        # Update enemy parameters for all existing enemies
        for enemy in [sprite for sprite in self.game.vulnerable_grp.sprites() 
                     if sprite != self.game.my_player]:
            if hasattr(enemy, 'health'):
                # Scale enemy health based on difficulty
                enemy.health = max(1, int(self.base_enemy_health * health_factor))
                
                # Scale enemy fire rate based on difficulty
                if hasattr(enemy, 'time_bw_shots'):
                    enemy.time_bw_shots = max(300, int(self.base_enemy_fire_rate * fire_rate_factor))
        
        # Update bullet speed for future bullets
        # This is used when creating new bullets
        self.current_bullet_speed = int(self.base_enemy_bullet_speed * bullet_speed_factor)
    
    def register_shot_fired(self):
        self.player_metrics['shots_fired'] += 1
    
    def register_shot_hit(self):
        self.player_metrics['shots_hit'] += 1
        
        # Check if challenge is completed after each successful hit
        self.check_challenge_completion()
    
    def register_enemy_killed(self):
        self.player_metrics['enemies_killed'] += 1
    
    def register_damage_taken(self):
        self.player_metrics['damage_taken'] += 1
    
    def check_progress(self, deltaTime):
        # Update metrics
        self.update_metrics(deltaTime)
        
        # Check if it's time for an evaluation
        time_since_last_eval = self.player_metrics['time_alive'] - self.player_metrics['last_evaluation_time']
        
        # More frequent evaluations in the first few minutes
        evaluation_threshold = self.evaluation_interval
        if self.player_metrics['time_alive'] < 180:  # First 3 minutes
            evaluation_threshold = 30  # Check every 30 seconds initially
        
        if time_since_last_eval >= evaluation_threshold:
            self.suggest_difficulty_change()
    
    def draw_warning(self):
        if self.show_warning:
            current_time = pg.time.get_ticks()
            if current_time - self.warning_time < self.warning_duration:
                display_surface = pg.display.get_surface()
                display_surface.blit(self.warning_surface, self.warning_rect)
                
                # Make it flash
                if (current_time // 250) % 2 == 0:
                    text = self.font.render("DIFFICULTY INCREASE SUGGESTED!", True, (255, 50, 50))
                    text_rect = text.get_rect(center=(640, 150))
                    display_surface.blit(text, text_rect)
            else:
                self.show_warning = False
    
    def draw_prompt(self):
        if self.show_prompt:
            current_time = pg.time.get_ticks()
            if current_time - self.prompt_time < self.prompt_duration:
                display_surface = pg.display.get_surface()
                
                # Draw background
                prompt_bg = pg.Surface((600, 150))
                prompt_bg.set_alpha(200)
                prompt_bg.fill((0, 0, 0))
                bg_rect = prompt_bg.get_rect(center=(640, 360))
                display_surface.blit(prompt_bg, bg_rect)
                
                # Draw text based on prompt type
                if self.prompt_type == "difficulty":
                    text1 = self.font.render("You're doing well! Increase difficulty?", True, (255, 255, 255))
                    text2 = self.font.render("Press Y to increase, N to stay at current level", True, (255, 255, 255))
                elif self.prompt_type == "challenge":
                    text1 = self.font.render("Challenge completed! Accept harder difficulty?", True, (255, 255, 0))
                    text2 = self.font.render("Press Y to increase enemy damage, N to decline", True, (255, 255, 0))
                
                text1_rect = text1.get_rect(center=(640, 330))
                text2_rect = text2.get_rect(center=(640, 370))
                
                display_surface.blit(text1, text1_rect)
                display_surface.blit(text2, text2_rect)
            else:
                self.show_prompt = False
                # Auto-reject if player didn't respond
                if self.prompt_type == "difficulty":
                    self.apply_difficulty_change("maintain")
                elif self.prompt_type == "challenge":
                    self.feedback_message = "Challenge reward declined. Difficulty remains the same."
                    self.feedback_time = pg.time.get_ticks()
    
    def draw_feedback(self):
        current_time = pg.time.get_ticks()
        if current_time - self.feedback_time < self.feedback_duration and self.feedback_message:
            display_surface = pg.display.get_surface()
            
            # Draw background
            feedback_bg = pg.Surface((600, 40))
            feedback_bg.set_alpha(150)
            feedback_bg.fill((0, 0, 0))
            bg_rect = feedback_bg.get_rect(center=(640, 50))
            display_surface.blit(feedback_bg, bg_rect)
            
            # Draw text
            text = self.small_font.render(self.feedback_message, True, (255, 255, 255))
            text_rect = text.get_rect(center=(640, 50))
            display_surface.blit(text, text_rect)
    
    def draw_challenge_timer(self):
        if self.challenge_active:
            display_surface = pg.display.get_surface()
            
            # Calculate remaining time
            remaining_time = self.challenge_duration - self.player_metrics['challenge_time']
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            
            # Draw timer
            timer_text = self.small_font.render(f"Challenge: {minutes}:{seconds:02d}", True, (255, 255, 0))
            display_surface.blit(timer_text, (10, 130))
            
            # Draw accuracy
            accuracy = self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired']) * 100
            acc_color = (0, 255, 0) if accuracy >= self.accuracy_threshold * 100 else (255, 100, 100)
            acc_text = self.small_font.render(f"Accuracy: {accuracy:.1f}% (Target: {self.accuracy_threshold * 100}%)", True, acc_color)
            display_surface.blit(acc_text, (10, 160))
    
    def draw_performance_indicators(self):
        display_surface = pg.display.get_surface()
        
        # Draw difficulty level
        diff_text = self.small_font.render(f"Difficulty: {self.difficulty_level}/10", True, (255, 255, 255))
        display_surface.blit(diff_text, (10, 40))
        
        # Draw accuracy
        accuracy = self.player_metrics['shots_hit'] / max(1, self.player_metrics['shots_fired']) * 100
        acc_text = self.small_font.render(f"Accuracy: {accuracy:.1f}%", True, (255, 255, 255))
        display_surface.blit(acc_text, (10, 70))
        
        # Draw kills
        kills_text = self.small_font.render(f"Kills: {self.player_metrics['enemies_killed']}", True, (255, 255, 255))
        display_surface.blit(kills_text, (10, 100))
        
        # Draw challenge status if not active
        if self.challenge_completed:
            status_text = self.small_font.render("Challenge: Completed!", True, (0, 255, 0))
            display_surface.blit(status_text, (10, 130))
        elif self.challenge_failed:
            status_text = self.small_font.render("Challenge: Failed", True, (255, 100, 100))
            display_surface.blit(status_text, (10, 130))
    
    def handle_input(self, event):
        if self.show_prompt and event.type == pg.KEYDOWN:
            if event.key == pg.K_y:
                self.show_prompt = False
                if self.prompt_type == "difficulty":
                    self.apply_difficulty_change("increase")
                elif self.prompt_type == "challenge":
                    self.apply_difficulty_change("challenge_success")
                return True
            elif event.key == pg.K_n:
                self.show_prompt = False
                if self.prompt_type == "difficulty":
                    self.apply_difficulty_change("maintain")
                elif self.prompt_type == "challenge":
                    self.feedback_message = "Challenge reward declined. Difficulty remains the same."
                    self.feedback_time = pg.time.get_ticks()
                return True
        return False
    
    def update(self, deltaTime):
        self.check_progress(deltaTime)
        self.draw_warning()
        self.draw_prompt()
        self.draw_feedback()
        
        # Draw challenge timer or performance indicators
        if self.challenge_active:
            self.draw_challenge_timer()
        else:
            self.draw_performance_indicators()