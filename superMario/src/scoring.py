#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Game - Scoring System
Handles all scoring logic and high score management
"""

import json
import os
from pathlib import Path

class ScoringSystem:
    """Handles game scoring and statistics"""

    def __init__(self):
        """Initialize scoring system"""
        # Point values
        self.coin_points = 200
        self.enemy_points = 100
        self.powerup_points = 1000
        self.level_complete_bonus = 5000
        self.time_bonus_multiplier = 50  # points per second remaining

        # Current game stats
        self.current_score = 0
        self.coins_collected = 0
        self.enemies_defeated = 0
        self.powerups_collected = 0
        self.levels_completed = 0
        self.time_bonus_total = 0

        # High scores
        self.high_scores_file = Path("high_scores.json")
        self.high_scores = self._load_high_scores()

    def _load_high_scores(self):
        """Load high scores from file"""
        if self.high_scores_file.exists():
            try:
                with open(self.high_scores_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load high scores: {e}")

        # Default high scores
        return {
            "easy": [],
            "normal": [],
            "hard": []
        }

    def _save_high_scores(self):
        """Save high scores to file"""
        try:
            with open(self.high_scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.high_scores, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save high scores: {e}")

    def add_coin_score(self):
        """Add points for collecting a coin"""
        self.current_score += self.coin_points
        self.coins_collected += 1

    def add_enemy_score(self):
        """Add points for defeating an enemy"""
        self.current_score += self.enemy_points
        self.enemies_defeated += 1

    def add_powerup_score(self):
        """Add points for collecting a powerup"""
        self.current_score += self.powerup_points
        self.powerups_collected += 1

    def add_level_complete_score(self, time_remaining):
        """Add points for completing a level"""
        time_bonus = int(time_remaining * self.time_bonus_multiplier)
        self.current_score += self.level_complete_bonus + time_bonus
        self.time_bonus_total += time_bonus
        self.levels_completed += 1

    def get_current_score(self):
        """Get current game score"""
        return self.current_score

    def get_stats(self):
        """Get current game statistics"""
        return {
            "score": self.current_score,
            "coins": self.coins_collected,
            "enemies": self.enemies_defeated,
            "powerups": self.powerups_collected,
            "levels": self.levels_completed,
            "time_bonus": self.time_bonus_total
        }

    def reset_game_stats(self):
        """Reset current game statistics"""
        self.current_score = 0
        self.coins_collected = 0
        self.enemies_defeated = 0
        self.powerups_collected = 0
        self.levels_completed = 0
        self.time_bonus_total = 0

    def check_high_score(self, difficulty="normal"):
        """Check if current score is a high score"""
        if difficulty not in self.high_scores:
            self.high_scores[difficulty] = []

        scores = self.high_scores[difficulty]

        # Add current score
        scores.append({
            "score": self.current_score,
            "stats": self.get_stats(),
            "timestamp": self._get_timestamp()
        })

        # Sort by score (highest first) and keep top 10
        scores.sort(key=lambda x: x["score"], reverse=True)
        self.high_scores[difficulty] = scores[:10]

        # Save high scores
        self._save_high_scores()

        # Return rank (1-based)
        for i, score_entry in enumerate(scores):
            if score_entry["score"] == self.current_score and score_entry["timestamp"] == scores[-1]["timestamp"]:
                return i + 1

        return None

    def get_high_scores(self, difficulty="normal"):
        """Get high scores for a difficulty level"""
        return self.high_scores.get(difficulty, [])

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def calculate_performance_rating(self):
        """Calculate performance rating based on stats"""
        stats = self.get_stats()

        if stats["levels"] == 0:
            return "未完成"

        # Base rating on levels completed and score efficiency
        avg_score_per_level = stats["score"] / stats["levels"]

        if avg_score_per_level >= 10000:
            return "S - 完美表现"
        elif avg_score_per_level >= 8000:
            return "A - 优秀"
        elif avg_score_per_level >= 6000:
            return "B - 良好"
        elif avg_score_per_level >= 4000:
            return "C - 及格"
        else:
            return "D - 需要改进"

    def get_score_breakdown(self):
        """Get detailed score breakdown"""
        stats = self.get_stats()

        breakdown = {
            "金币得分": stats["coins"] * self.coin_points,
            "敌人得分": stats["enemies"] * self.enemy_points,
            "道具得分": stats["powerups"] * self.powerup_points,
            "关卡完成奖励": stats["levels"] * self.level_complete_bonus,
            "时间奖励": stats["time_bonus"],
            "总分": stats["score"]
        }

        return breakdown

    def export_stats(self, filename=None):
        """Export game statistics to file"""
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_stats_{timestamp}.json"

        stats = {
            "final_score": self.current_score,
            "detailed_stats": self.get_stats(),
            "score_breakdown": self.get_score_breakdown(),
            "performance_rating": self.calculate_performance_rating(),
            "timestamp": self._get_timestamp()
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"Statistics exported to {filename}")
            return filename
        except Exception as e:
            print(f"Failed to export statistics: {e}")
            return None

class AchievementSystem:
    """Handles game achievements"""

    def __init__(self):
        """Initialize achievement system"""
        self.achievements = {
            "first_coin": {"name": "第一个金币", "description": "收集你的第一个金币", "unlocked": False},
            "coin_collector": {"name": "金币收藏家", "description": "收集100个金币", "unlocked": False},
            "enemy_slayer": {"name": "敌人杀手", "description": "击败50个敌人", "unlocked": False},
            "power_up": {"name": "力量提升", "description": "收集第一个道具", "unlocked": False},
            "level_master": {"name": "关卡大师", "description": "完成10个关卡", "unlocked": False},
            "speed_runner": {"name": "速度狂人", "description": "在关卡中剩余时间超过300秒", "unlocked": False},
            "perfect_game": {"name": "完美游戏", "description": "完成游戏且没有损失生命", "unlocked": False}
        }

        self.achievement_file = Path("achievements.json")
        self._load_achievements()

    def _load_achievements(self):
        """Load achievements from file"""
        if self.achievement_file.exists():
            try:
                with open(self.achievement_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    for key, value in saved.items():
                        if key in self.achievements:
                            self.achievements[key]["unlocked"] = value.get("unlocked", False)
            except Exception as e:
                print(f"Failed to load achievements: {e}")

    def _save_achievements(self):
        """Save achievements to file"""
        try:
            with open(self.achievement_file, 'w', encoding='utf-8') as f:
                json.dump(self.achievements, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save achievements: {e}")

    def check_achievements(self, stats):
        """Check and unlock achievements based on current stats"""
        new_achievements = []

        # First coin
        if not self.achievements["first_coin"]["unlocked"] and stats["coins"] >= 1:
            self.achievements["first_coin"]["unlocked"] = True
            new_achievements.append("first_coin")

        # Coin collector
        if not self.achievements["coin_collector"]["unlocked"] and stats["coins"] >= 100:
            self.achievements["coin_collector"]["unlocked"] = True
            new_achievements.append("coin_collector")

        # Enemy slayer
        if not self.achievements["enemy_slayer"]["unlocked"] and stats["enemies"] >= 50:
            self.achievements["enemy_slayer"]["unlocked"] = True
            new_achievements.append("enemy_slayer")

        # Power up
        if not self.achievements["power_up"]["unlocked"] and stats["powerups"] >= 1:
            self.achievements["power_up"]["unlocked"] = True
            new_achievements.append("power_up")

        # Level master
        if not self.achievements["level_master"]["unlocked"] and stats["levels"] >= 10:
            self.achievements["level_master"]["unlocked"] = True
            new_achievements.append("level_master")

        if new_achievements:
            self._save_achievements()

        return new_achievements

    def get_achievement(self, achievement_id):
        """Get achievement details"""
        return self.achievements.get(achievement_id)

    def get_all_achievements(self):
        """Get all achievements"""
        return self.achievements

    def get_unlocked_achievements(self):
        """Get list of unlocked achievement IDs"""
        return [key for key, value in self.achievements.items() if value["unlocked"]]