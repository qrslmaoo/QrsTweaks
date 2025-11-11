from dataclasses import dataclass

@dataclass
class AppState:
    unlocked_vault: bool = False
