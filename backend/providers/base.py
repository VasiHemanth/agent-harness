from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

class BaseProvider(ABC):
    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name

    @abstractmethod
    def discover_sessions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of session metadata.
        Each session should at least have: id, agent, project, timestamp
        """
        pass

    @abstractmethod
    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns full details for a specific session.
        """
        pass

    def _get_platform_base(self, mac_path: str, win_path: str, linux_path: str) -> Path:
        import sys
        import os
        home = Path.home()
        if sys.platform == "darwin":
            return home / mac_path
        elif sys.platform == "win32":
            appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
            # For Windows, we often need to adjust the relative part if it's based on Library/Application Support
            return appdata / win_path
        else:
            config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
            return config / linux_path
