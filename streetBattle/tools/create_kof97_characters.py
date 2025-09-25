#!/usr/bin/env python3
"""
KOF97 Character Creation System for StreetBattle
Creates 20 unique fighting characters with animations, special moves, and stats
"""

import json
import os
from typing import Dict, List, Any

class KOF97Character:
    """Represents a KOF97-style fighting character with complete move set"""
    
    def __init__(self, name: str, character_id: int):
        self.name = name
        self.id = character_id
        self.nationality = ""
        self.fighting_style = ""
        self.story = ""
        
        # Base stats (1-10 scale)
        self.stats = {
            "health": 5,
            "attack": 5,
            "defense": 5,
            "speed": 5,
            "range": 5,
            "special": 5
        }
        
        # Animation list
        self.animations = {
            "idle": {"file": "", "frames": 4, "speed": 8},
            "walk_forward": {"file": "", "frames": 6, "speed": 12},
            "walk_backward": {"file": "", "frames": 6, "speed": 12},
            "jump": {"file": "", "frames": 8, "speed": 16},
            "crouch": {"file": "", "frames": 2, "speed": 4},
            "block": {"file": "", "frames": 3, "speed": 6},
            "hurt": {"file": "", "frames": 4, "speed": 8},
            "knockdown": {"file": "", "frames": 8, "speed": 12},
            "victory": {"file": "", "frames": 12, "speed": 6},
            "defeat": {"file": "", "frames": 10, "speed": 8}
        }
        
        # Attack animations
        self.attacks = {
            "light_punch": {"damage": 8, "range": 1.2, "startup": 4, "recovery": 8, "frames": 6},
            "heavy_punch": {"damage": 18, "range": 1.5, "startup": 8, "recovery": 16, "frames": 10},
            "light_kick": {"damage": 10, "range": 1.4, "startup": 6, "recovery": 10, "frames": 8},
            "heavy_kick": {"damage": 20, "range": 1.8, "startup": 10, "recovery": 18, "frames": 12},
            "crouch_punch": {"damage": 6, "range": 1.0, "startup": 3, "recovery": 6, "frames": 5},
            "crouch_kick": {"damage": 12, "range": 2.0, "startup": 8, "recovery": 12, "frames": 9}
        }
        
        # Special moves (quarter-circle, etc.)
        self.special_moves = {}
        
        # Super moves (require power gauge)
        self.super_moves = {}
        
        # Color palette variations
        self.color_variations = [
            {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#000000"},  # Default
            {"primary": "#0000FF", "secondary": "#FFFF00", "accent": "#000000"},  # Blue/Yellow
            {"primary": "#00FF00", "secondary": "#FF00FF", "accent": "#FFFFFF"},  # Green/Magenta
            {"primary": "#FF8000", "secondary": "#8000FF", "accent": "#404040"}   # Orange/Purple
        ]

class KOF97CharacterDatabase:
    """Manages all 20 KOF97-style characters"""
    
    def __init__(self):
        self.characters = []
        self.create_all_characters()
    
    def create_all_characters(self):
        """Create all 20 KOF97-inspired characters"""
        
        # Team Japan (based on classic archetypes)
        self.add_character("Kyo Kusanagi", "Japan", "Kusanagi Flame Arts", 
                          {"health": 7, "attack": 8, "defense": 6, "speed": 7, "range": 6, "special": 9},
                          "Heir to the Kusanagi clan, wielder of crimson flames")
        
        self.add_character("Iori Yagami", "Japan", "Yagami Ancient Arts", 
                          {"health": 6, "attack": 9, "defense": 5, "speed": 8, "range": 5, "special": 10},
                          "Rival of Kyo, master of purple flames and blood riot")
        
        self.add_character("Chizuru Kagura", "Japan", "Sacred Mirror Arts", 
                          {"health": 5, "attack": 6, "defense": 8, "speed": 6, "range": 7, "special": 8},
                          "Guardian of the sacred treasures, master of mirror illusions")
        
        # Team Fatal Fury
        self.add_character("Terry Bogard", "USA", "Street Fighting", 
                          {"health": 8, "attack": 7, "defense": 7, "speed": 6, "range": 7, "special": 7},
                          "Legendary wolf of Southtown, master of power wave")
        
        self.add_character("Andy Bogard", "USA", "Koppo-ken & Ninjutsu", 
                          {"health": 6, "attack": 6, "defense": 6, "speed": 9, "range": 6, "special": 7},
                          "Terry's younger brother, swift ninja fighter")
        
        self.add_character("Joe Higashi", "Japan", "Muay Thai", 
                          {"health": 7, "attack": 8, "defense": 5, "speed": 8, "range": 5, "special": 6},
                          "Champion Muay Thai fighter with hurricane kicks")
        
        # Team Art of Fighting
        self.add_character("Ryo Sakazaki", "Japan", "Kyokugen Karate", 
                          {"health": 8, "attack": 9, "defense": 7, "speed": 5, "range": 6, "special": 7},
                          "Heir to Kyokugen Karate, the Invincible Dragon")
        
        self.add_character("Robert Garcia", "Italy", "Kyokugen Karate", 
                          {"health": 7, "attack": 8, "defense": 6, "speed": 7, "range": 6, "special": 7},
                          "Wealthy Italian fighter, master of kicks")
        
        self.add_character("Yuri Sakazaki", "Japan", "Modified Kyokugen", 
                          {"health": 5, "attack": 6, "defense": 5, "speed": 9, "range": 5, "special": 8},
                          "Ryo's sister, agile and spirited fighter")
        
        # Team Ikari Warriors
        self.add_character("Leona Heidern", "Unknown", "Military Combat", 
                          {"health": 7, "attack": 8, "defense": 8, "speed": 6, "range": 8, "special": 8},
                          "Silent soldier with Orochi blood, master of explosives")
        
        self.add_character("Ralf Jones", "USA", "Military Fighting", 
                          {"health": 9, "attack": 9, "defense": 8, "speed": 4, "range": 6, "special": 5},
                          "Powerhouse mercenary with vulcan punch")
        
        self.add_character("Clark Still", "USA", "Military Wrestling", 
                          {"health": 8, "attack": 7, "defense": 9, "speed": 5, "range": 7, "special": 6},
                          "Grappling specialist and Ralf's partner")
        
        # Team Psycho Soldier
        self.add_character("Athena Asamiya", "Japan", "Psychic Powers", 
                          {"health": 5, "attack": 6, "defense": 5, "speed": 7, "range": 9, "special": 10},
                          "Pop idol with powerful psychic abilities")
        
        self.add_character("Sie Kensou", "China", "Dragon Spirit", 
                          {"health": 6, "attack": 7, "defense": 6, "speed": 8, "range": 6, "special": 8},
                          "Young fighter with dragon powers and meat buns")
        
        self.add_character("Chin Gentsai", "China", "Drunken Fist", 
                          {"health": 6, "attack": 5, "defense": 7, "speed": 6, "range": 5, "special": 9},
                          "Old master of drunken kung fu")
        
        # Team Women Fighters
        self.add_character("Mai Shiranui", "Japan", "Shiranui Ninjutsu", 
                          {"health": 6, "attack": 7, "defense": 5, "speed": 8, "range": 7, "special": 8},
                          "Kunoichi master of fire and fans")
        
        self.add_character("King", "France", "Muay Thai", 
                          {"health": 6, "attack": 8, "defense": 6, "speed": 7, "range": 6, "special": 7},
                          "Female Muay Thai champion and bar owner")
        
        self.add_character("Blue Mary", "USA", "Sambo & Command", 
                          {"health": 7, "attack": 7, "defense": 7, "speed": 7, "range": 6, "special": 6},
                          "Agent and grappling expert")
        
        # Boss Characters
        self.add_character("Geese Howard", "USA", "Hakkyokuseiken", 
                          {"health": 10, "attack": 9, "defense": 8, "speed": 5, "range": 7, "special": 9},
                          "Crime boss of Southtown, master of counter attacks")
        
        self.add_character("Orochi", "Unknown", "Earth's Will", 
                          {"health": 8, "attack": 10, "defense": 9, "speed": 6, "range": 10, "special": 10},
                          "Avatar of Earth's wrath, final boss with overwhelming power")
    
    def add_character(self, name: str, nationality: str, fighting_style: str, 
                     stats: Dict[str, int], story: str):
        """Add a character to the database"""
        char_id = len(self.characters)
        character = KOF97Character(name, char_id)
        character.nationality = nationality
        character.fighting_style = fighting_style
        character.stats = stats
        character.story = story
        
        # Add special moves based on character archetype
        self._add_special_moves(character)
        
        self.characters.append(character)
    
    def _add_special_moves(self, character: KOF97Character):
        """Add character-specific special and super moves"""
        name = character.name
        
        if "Kyo" in name:
            character.special_moves = {
                "Fireball": {"input": "QCF+P", "damage": 15, "range": 5.0, "startup": 12},
                "DP": {"input": "DP+P", "damage": 20, "range": 2.0, "startup": 8},
                "Air Fireball": {"input": "QCF+P (air)", "damage": 12, "range": 4.0, "startup": 10}
            }
            character.super_moves = {
                "Orochinagi": {"input": "QCB,HCF+P", "damage": 45, "range": 3.0, "power_cost": 1},
                "Mu Shiki": {"input": "QCF,QCF+P", "damage": 35, "range": 6.0, "power_cost": 1}
            }
        
        elif "Iori" in name:
            character.special_moves = {
                "Purple Flame": {"input": "QCF+P", "damage": 18, "range": 4.5, "startup": 10},
                "Command Grab": {"input": "HCB+P", "damage": 25, "range": 1.5, "startup": 6},
                "Rekka": {"input": "QCF+K", "damage": 12, "range": 2.5, "startup": 8}
            }
            character.super_moves = {
                "Maiden Masher": {"input": "QCF,HCB+P", "damage": 50, "range": 2.0, "power_cost": 1},
                "Blood Riot": {"input": "QCB,QCB+P", "damage": 60, "range": 3.0, "power_cost": 2}
            }
        
        elif "Terry" in name:
            character.special_moves = {
                "Power Wave": {"input": "QCF+P", "damage": 14, "range": 6.0, "startup": 14},
                "Burn Knuckle": {"input": "QCB+P", "damage": 22, "range": 3.0, "startup": 12},
                "Rising Tackle": {"input": "Charge D,U+P", "damage": 20, "range": 2.0, "startup": 8}
            }
            character.super_moves = {
                "Power Geyser": {"input": "QCB,DB,F+P", "damage": 40, "range": 2.5, "power_cost": 1},
                "High Angle Geyser": {"input": "QCF,QCF+P", "damage": 35, "range": 4.0, "power_cost": 1}
            }
        
        # Add more character-specific moves...
        # Default moves for characters without specific movesets
        if not character.special_moves:
            character.special_moves = {
                "Special Attack": {"input": "QCF+P", "damage": 15, "range": 3.0, "startup": 10},
                "Counter Move": {"input": "QCB+P", "damage": 20, "range": 2.0, "startup": 8}
            }
            character.super_moves = {
                "Super Move": {"input": "QCF,QCF+P", "damage": 35, "range": 3.5, "power_cost": 1}
            }
    
    def save_to_file(self, filename: str = "kof97_characters.json"):
        """Save character database to JSON file"""
        char_data = []
        for char in self.characters:
            char_dict = {
                "id": char.id,
                "name": char.name,
                "nationality": char.nationality,
                "fighting_style": char.fighting_style,
                "story": char.story,
                "stats": char.stats,
                "animations": char.animations,
                "attacks": char.attacks,
                "special_moves": char.special_moves,
                "super_moves": char.super_moves,
                "color_variations": char.color_variations
            }
            char_data.append(char_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.characters)} characters to {filename}")
    
    def generate_character_assets(self):
        """Generate placeholder asset files for all characters"""
        assets_dir = "assets/characters"
        os.makedirs(assets_dir, exist_ok=True)
        
        for char in self.characters:
            char_dir = os.path.join(assets_dir, char.name.lower().replace(" ", "_"))
            os.makedirs(char_dir, exist_ok=True)
            
            # Create placeholder model file
            model_file = os.path.join(char_dir, f"{char.name.lower().replace(' ', '_')}.bam")
            with open(model_file, 'w') as f:
                f.write(f"# Placeholder BAM model for {char.name}\n")
            
            # Create animation files
            anim_dir = os.path.join(char_dir, "animations")
            os.makedirs(anim_dir, exist_ok=True)
            
            for anim_name, anim_data in char.animations.items():
                anim_file = os.path.join(anim_dir, f"{anim_name}.bam")
                with open(anim_file, 'w') as f:
                    f.write(f"# Animation: {anim_name} for {char.name}\n")
                    f.write(f"# Frames: {anim_data['frames']}, Speed: {anim_data['speed']}\n")
        
        print(f"Generated asset structure for {len(self.characters)} characters in {assets_dir}")
    
    def print_character_roster(self):
        """Print formatted character roster"""
        print("=" * 60)
        print("KING OF FIGHTERS '97 - CHARACTER ROSTER")
        print("=" * 60)
        
        teams = {
            "Team Japan": ["Kyo Kusanagi", "Iori Yagami", "Chizuru Kagura"],
            "Team Fatal Fury": ["Terry Bogard", "Andy Bogard", "Joe Higashi"],
            "Team Art of Fighting": ["Ryo Sakazaki", "Robert Garcia", "Yuri Sakazaki"],
            "Team Ikari Warriors": ["Leona Heidern", "Ralf Jones", "Clark Still"],
            "Team Psycho Soldier": ["Athena Asamiya", "Sie Kensou", "Chin Gentsai"],
            "Team Women Fighters": ["Mai Shiranui", "King", "Blue Mary"],
            "Boss Characters": ["Geese Howard", "Orochi"]
        }
        
        for team_name, member_names in teams.items():
            print(f"\n{team_name}:")
            print("-" * len(team_name))
            for member_name in member_names:
                char = next((c for c in self.characters if c.name == member_name), None)
                if char:
                    print(f"  {char.name} ({char.nationality}) - {char.fighting_style}")
                    print(f"    Stats: ATK:{char.stats['attack']} DEF:{char.stats['defense']} "
                          f"SPD:{char.stats['speed']} RNG:{char.stats['range']}")
                    print(f"    {char.story}")
                    print()

def main():
    """Create and save KOF97 character database"""
    print("Creating KOF97 Character Database...")
    
    db = KOF97CharacterDatabase()
    
    # Print character roster
    db.print_character_roster()
    
    # Save to JSON file
    db.save_to_file()
    
    # Generate asset structure
    db.generate_character_assets()
    
    print(f"\nCharacter creation complete!")
    print(f"Total characters: {len(db.characters)}")

if __name__ == "__main__":
    main()