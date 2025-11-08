"""
Weather System
Manages weather conditions with seasonal probabilities
"""

from enum import Enum
import random
from typing import Dict, Tuple


class WeatherType(Enum):
    """Types of weather"""
    SUNNY = "sunny"
    RAIN = "rain"
    SNOW = "snow"


class Season(Enum):
    """Seasons of the year"""
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"


class WeatherSystem:
    """Manages weather conditions with seasonal probabilities"""

    # Seasonal weather probabilities (sunny, rain, snow)
    SEASONAL_PROBABILITIES = {
        Season.WINTER: {
            WeatherType.SUNNY: 0.30,
            WeatherType.RAIN: 0.20,
            WeatherType.SNOW: 0.50
        },
        Season.SPRING: {
            WeatherType.SUNNY: 0.50,
            WeatherType.RAIN: 0.50,
            WeatherType.SNOW: 0.00
        },
        Season.SUMMER: {
            WeatherType.SUNNY: 0.85,
            WeatherType.RAIN: 0.15,
            WeatherType.SNOW: 0.00
        },
        Season.AUTUMN: {
            WeatherType.SUNNY: 0.35,
            WeatherType.RAIN: 0.65,
            WeatherType.SNOW: 0.00
        }
    }

    # Weather impact on visitor spawn rate
    SPAWN_RATE_MULTIPLIER = {
        WeatherType.SUNNY: 1.0,   # 100% normal
        WeatherType.RAIN: 0.5,    # 50% less visitors
        WeatherType.SNOW: 0.3     # 70% less visitors
    }

    # Weather impact on visitor satisfaction (per minute in outdoor areas)
    SATISFACTION_PENALTY = {
        WeatherType.SUNNY: 0.0,   # No penalty
        WeatherType.RAIN: -5.0,   # -5 per minute
        WeatherType.SNOW: -10.0   # -10 per minute
    }

    def __init__(self):
        # Current weather (starts sunny)
        self.current_weather = WeatherType.SUNNY

        # Days until next weather change (2 days)
        self.days_until_change = 2
        self.weather_change_interval = 2  # Change every 2 days

        # Last day checked (to detect day changes)
        self.last_day = 0

    def get_season(self, month: int) -> Season:
        """Get season based on month (1-12)"""
        if month in [12, 1, 2]:
            return Season.WINTER
        elif month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        else:  # 9, 10, 11
            return Season.AUTUMN

    def tick_day(self, current_day: int, current_month: int):
        """
        Called when a new day starts.
        Check if weather should change.
        """
        # Detect day change
        if current_day != self.last_day:
            self.last_day = current_day
            self.days_until_change -= 1

            # Change weather if interval reached
            if self.days_until_change <= 0:
                self._change_weather(current_month)
                self.days_until_change = self.weather_change_interval

    def _change_weather(self, current_month: int):
        """Change weather based on seasonal probabilities"""
        season = self.get_season(current_month)
        probabilities = self.SEASONAL_PROBABILITIES[season]

        # Generate random weather based on probabilities
        rand = random.random()
        cumulative = 0.0

        for weather_type, probability in probabilities.items():
            cumulative += probability
            if rand <= cumulative:
                self.current_weather = weather_type
                break

    def get_spawn_rate_multiplier(self) -> float:
        """Get visitor spawn rate multiplier for current weather"""
        return self.SPAWN_RATE_MULTIPLIER[self.current_weather]

    def get_satisfaction_penalty(self) -> float:
        """Get satisfaction penalty per minute for current weather"""
        return self.SATISFACTION_PENALTY[self.current_weather]

    def get_weather_name(self) -> str:
        """Get human-readable weather name"""
        names = {
            WeatherType.SUNNY: "Soleil",
            WeatherType.RAIN: "Pluie",
            WeatherType.SNOW: "Neige"
        }
        return names[self.current_weather]

    def get_weather_emoji(self) -> str:
        """Get weather emoji for display"""
        emojis = {
            WeatherType.SUNNY: "☀️",
            WeatherType.RAIN: "🌧️",
            WeatherType.SNOW: "❄️"
        }
        return emojis[self.current_weather]

    def get_weather_color(self) -> Tuple[int, int, int]:
        """Get color for weather overlay"""
        colors = {
            WeatherType.SUNNY: (255, 255, 200),  # Light yellow (subtle)
            WeatherType.RAIN: (100, 100, 150),   # Blue-gray
            WeatherType.SNOW: (220, 220, 240)    # Light blue-white
        }
        return colors[self.current_weather]

    def should_show_overlay(self) -> bool:
        """Check if weather overlay should be shown"""
        return self.current_weather in [WeatherType.RAIN, WeatherType.SNOW]

    def should_show_particles(self) -> bool:
        """Check if weather particles should be shown"""
        return self.current_weather in [WeatherType.RAIN, WeatherType.SNOW]

    # Serialization for save/load
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'current_weather': self.current_weather.value,
            'days_until_change': self.days_until_change,
            'last_day': self.last_day
        }

    def from_dict(self, data: dict):
        """Load from dictionary"""
        weather_str = data.get('current_weather', 'sunny')
        self.current_weather = WeatherType(weather_str)
        self.days_until_change = data.get('days_until_change', 2)
        self.last_day = data.get('last_day', 0)


class WeatherParticle:
    """Single weather particle (rain drop or snowflake)"""

    def __init__(self, x: float, y: float, weather_type: WeatherType):
        self.x = x
        self.y = y
        self.weather_type = weather_type

        # Particle properties based on weather
        if weather_type == WeatherType.RAIN:
            self.speed_y = random.uniform(300, 400)  # Fast falling
            self.speed_x = random.uniform(-20, 20)   # Slight horizontal drift
            self.size = random.randint(1, 2)
            self.color = (150, 150, 200, 180)  # Semi-transparent blue
        else:  # SNOW
            self.speed_y = random.uniform(50, 100)   # Slow falling
            self.speed_x = random.uniform(-30, 30)   # More drift
            self.size = random.randint(2, 4)
            self.color = (255, 255, 255, 200)  # Semi-transparent white

    def update(self, dt: float):
        """Update particle position"""
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt

    def is_off_screen(self, screen_height: int) -> bool:
        """Check if particle has fallen off screen"""
        return self.y > screen_height


class WeatherParticleSystem:
    """Manages weather particles (rain/snow)"""

    def __init__(self):
        self.particles = []
        self.max_particles = 200  # Maximum number of particles
        self.spawn_rate = 100      # Particles per second

    def update(self, dt: float, weather_type: WeatherType, screen_width: int, screen_height: int):
        """Update particle system"""
        # Remove off-screen particles
        self.particles = [p for p in self.particles if not p.is_off_screen(screen_height)]

        # Update existing particles
        for particle in self.particles:
            particle.update(dt)

        # Spawn new particles
        if weather_type in [WeatherType.RAIN, WeatherType.SNOW]:
            particles_to_spawn = int(self.spawn_rate * dt)
            for _ in range(particles_to_spawn):
                if len(self.particles) < self.max_particles:
                    # Spawn above screen
                    x = random.uniform(0, screen_width)
                    y = random.uniform(-50, 0)
                    self.particles.append(WeatherParticle(x, y, weather_type))

    def clear(self):
        """Clear all particles"""
        self.particles.clear()

    def draw(self, screen):
        """Draw all particles"""
        import pygame
        for particle in self.particles:
            if particle.weather_type == WeatherType.RAIN:
                # Rain: vertical line
                pygame.draw.line(screen, particle.color[:3],
                               (int(particle.x), int(particle.y)),
                               (int(particle.x), int(particle.y + 10)),
                               particle.size)
            else:  # SNOW
                # Snow: small circle
                pygame.draw.circle(screen, particle.color[:3],
                                 (int(particle.x), int(particle.y)),
                                 particle.size)
