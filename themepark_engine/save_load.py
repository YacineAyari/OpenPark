"""
Save/Load system for OpenPark
Handles serialization and deserialization of game state
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class SaveLoadManager:
    """Manages game saves and loads"""

    def __init__(self, save_dir: str = "saves"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def save_game(self, game_state: Dict[str, Any], save_name: Optional[str] = None) -> str:
        """
        Save game state to JSON file

        Args:
            game_state: Dictionary containing all game state
            save_name: Optional custom save name, otherwise uses timestamp

        Returns:
            Path to the saved file
        """
        if save_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"park_{timestamp}"

        # Ensure .json extension
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = self.save_dir / save_name

        # Add metadata
        game_state['metadata'] = {
            'save_date': datetime.now().isoformat(),
            'version': '0.3.1-alpha',
            'game_name': 'OpenPark'
        }

        # Write to file with pretty formatting
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(game_state, f, indent=2, ensure_ascii=False)

        return str(save_path)

    def load_game(self, save_name: str) -> Dict[str, Any]:
        """
        Load game state from JSON file

        Args:
            save_name: Name of the save file (with or without .json)

        Returns:
            Dictionary containing game state

        Raises:
            FileNotFoundError: If save file doesn't exist
            json.JSONDecodeError: If save file is corrupted
        """
        # Ensure .json extension
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = self.save_dir / save_name

        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_path}")

        with open(save_path, 'r', encoding='utf-8') as f:
            game_state = json.load(f)

        return game_state

    def list_saves(self) -> list:
        """
        List all available save files

        Returns:
            List of save file names (without .json extension)
        """
        saves = []
        for save_file in self.save_dir.glob('*.json'):
            saves.append(save_file.stem)
        return sorted(saves, reverse=True)  # Most recent first

    def delete_save(self, save_name: str) -> bool:
        """
        Delete a save file

        Args:
            save_name: Name of the save file

        Returns:
            True if deleted successfully, False otherwise
        """
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = self.save_dir / save_name

        if save_path.exists():
            save_path.unlink()
            return True
        return False


def serialize_grid(grid) -> Dict[str, Any]:
    """Serialize grid to JSON-compatible format"""
    return {
        'width': grid.width,
        'height': grid.height,
        'tiles': [[grid.get(x, y) for y in range(grid.height)] for x in range(grid.width)]
    }


def serialize_ride(ride) -> Dict[str, Any]:
    """Serialize a ride to JSON-compatible format"""
    return {
        'id': ride.defn.id,
        'x': ride.x,
        'y': ride.y,
        'operational': ride.operational,
        'current_visitors': [guest.id for guest in ride.current_visitors],
        'ride_timer': ride.ride_timer,
        'ride_duration': ride.ride_duration,
        'is_launched': ride.is_launched,
        'waiting_visitors': [guest.id for guest in ride.waiting_visitors],
        'waiting_timer': ride.waiting_timer,
        'max_wait_time': ride.max_wait_time,
        'is_broken': ride.is_broken,
        'being_repaired': ride.being_repaired,
        'breakdown_timer': ride.breakdown_timer,
        'entrance': {'x': ride.entrance.x, 'y': ride.entrance.y} if ride.entrance else None,
        'exit': {'x': ride.exit.x, 'y': ride.exit.y} if ride.exit else None
    }


def serialize_shop(shop) -> Dict[str, Any]:
    """Serialize a shop to JSON-compatible format"""
    return {
        'id': shop.defn.id,
        'x': shop.x,
        'y': shop.y,
        'entrance': {'x': shop.entrance.x, 'y': shop.entrance.y} if shop.entrance else None,
        'connected_to_path': shop.connected_to_path
    }


def serialize_employee(employee) -> Dict[str, Any]:
    """Serialize an employee to JSON-compatible format"""
    data = {
        'id': employee.defn.id,
        'type': employee.defn.type,
        'x': employee.x,
        'y': employee.y,
        'state': employee.state,
        'employee_id': employee.id  # Internal ID for tracking
    }

    # Add type-specific data for Engineers and MaintenanceWorkers
    if hasattr(employee, 'target_x'):
        data['target_x'] = employee.target_x if employee.target_x is not None else employee.x
        data['target_y'] = employee.target_y if employee.target_y is not None else employee.y

    # Add placement_type for MaintenanceWorkers
    if hasattr(employee, 'placement_type') and employee.placement_type is not None:
        data['placement_type'] = employee.placement_type

    return data


def serialize_guest(guest) -> Dict[str, Any]:
    """Serialize a guest to JSON-compatible format"""
    return {
        'id': guest.id,
        'x': guest.x,
        'y': guest.y,
        'grid_x': guest.grid_x,
        'grid_y': guest.grid_y,
        'state': guest.state,
        'satisfaction': guest.satisfaction,
        'happiness': guest.happiness,
        'excitement': guest.excitement,
        'money': guest.money,
        'budget': guest.budget,
        'entry_time': guest.entry_time,
        'thrill_preference': guest.thrill_preference,
        'nausea_tolerance': guest.nausea_tolerance,
        'sprite': guest.sprite,
        'hunger': guest.hunger,
        'thirst': guest.thirst,
        'bladder': guest.bladder,
        'has_litter': guest.has_litter,
        'litter_type': guest.litter_type,
        'litter_hold_timer': guest.litter_hold_timer,
        'litter_hold_duration': guest.litter_hold_duration
    }


def serialize_bin(bin_obj) -> Dict[str, Any]:
    """Serialize a bin to JSON-compatible format"""
    return {
        'id': bin_obj.defn.id,
        'x': bin_obj.x,
        'y': bin_obj.y,
        'current_capacity': bin_obj.current_capacity
    }


def serialize_litter(litter_obj) -> Dict[str, Any]:
    """Serialize litter to JSON-compatible format"""
    return {
        'x': litter_obj.x,
        'y': litter_obj.y,
        'type': litter_obj.type,
        'age': litter_obj.age,
        'offset_x': litter_obj.offset_x,
        'offset_y': litter_obj.offset_y
    }


def serialize_restroom(restroom) -> Dict[str, Any]:
    """Serialize a restroom to JSON-compatible format"""
    return {
        'id': restroom.defn.id,
        'x': restroom.x,
        'y': restroom.y,
        'current_occupancy': len(restroom.current_users),  # Count of current users
        'connected_to_path': restroom.connected_to_path
    }
