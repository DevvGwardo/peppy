"""
Peppy Plugin for SIGI (Siggy)

This module provides the integration layer between Peppy and SIGI.
It handles:
- Configuration parsing from .siggy.yml
- Peppy availability detection
- Agent path resolution
- Auto-indexing coordination

Usage in SIGI:
    from peppy_sigi_plugin import PeppySigiPlugin

    plugin = PeppySigiPlugin(config)
    if plugin.is_available():
        plugin.setup()
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PeppyConfig:
    """Configuration for Peppy integration with SIGI."""
    enabled: bool = True
    auto_index: bool = True
    index_path: str = "."
    exclude_patterns: list = field(default_factory=lambda: [
        "node_modules/**",
        ".git/**",
        "dist/**",
        "build/**",
        "__pycache__/**",
    ])
    reindex_interval: int = 60  # minutes
    use_enhanced_agents: bool = True
    custom_planner_path: Optional[str] = None
    custom_executor_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "PeppyConfig":
        """Create config from dictionary (parsed from .siggy.yml)."""
        if not data:
            return cls(enabled=False)

        agents = data.get("agents", {})
        return cls(
            enabled=data.get("enabled", True),
            auto_index=data.get("auto_index", True),
            index_path=data.get("index_path", "."),
            exclude_patterns=data.get("exclude_patterns", cls.exclude_patterns),
            reindex_interval=data.get("reindex_interval", 60),
            use_enhanced_agents=data.get("use_enhanced_agents", True),
            custom_planner_path=agents.get("planner"),
            custom_executor_path=agents.get("executor"),
        )


class PeppySigiPlugin:
    """
    Peppy integration plugin for SIGI.

    This plugin enables Peppy's codebase indexing capabilities within SIGI workflows,
    providing significant token savings and faster code navigation.
    """

    PLUGIN_NAME = "peppy"
    PLUGIN_VERSION = "1.0.0"
    MIN_SIGGY_VERSION = "1.9.0"
    RECOMMENDED_SIGGY_VERSION = "1.10.0"

    def __init__(self, siggy_config: dict, project_root: Optional[Path] = None):
        """
        Initialize the Peppy plugin.

        Args:
            siggy_config: The full .siggy.yml config dict
            project_root: Project root path (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.siggy_config = siggy_config

        # Extract peppy config from plugins section
        plugins = siggy_config.get("plugins", {})
        peppy_data = plugins.get("peppy", {})

        # Handle boolean shorthand: plugins.peppy: true
        if isinstance(peppy_data, bool):
            peppy_data = {"enabled": peppy_data}

        self.config = PeppyConfig.from_dict(peppy_data)
        self._peppy_available: Optional[bool] = None
        self._bundled_agents_path: Optional[Path] = None

    @property
    def is_enabled(self) -> bool:
        """Check if Peppy integration is enabled in config."""
        return self.config.enabled

    def is_available(self) -> bool:
        """
        Check if Peppy MCP server is available.

        Returns:
            True if Peppy can be used, False otherwise.
        """
        if self._peppy_available is not None:
            return self._peppy_available

        # Check 1: Can we import peppy?
        try:
            import peppy
            self._peppy_available = True
        except ImportError:
            # Check 2: Is peppy available as a command?
            if shutil.which("peppy") or shutil.which("python"):
                # Try to run peppy module
                try:
                    result = subprocess.run(
                        ["python", "-c", "import peppy; print(peppy.__version__)"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    self._peppy_available = result.returncode == 0
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    self._peppy_available = False
            else:
                self._peppy_available = False

        return self._peppy_available

    def get_status(self) -> dict:
        """
        Get the current status of Peppy integration.

        Returns:
            Dict with status information.
        """
        return {
            "plugin": self.PLUGIN_NAME,
            "version": self.PLUGIN_VERSION,
            "enabled": self.is_enabled,
            "available": self.is_available(),
            "config": {
                "auto_index": self.config.auto_index,
                "index_path": self.config.index_path,
                "use_enhanced_agents": self.config.use_enhanced_agents,
                "reindex_interval": self.config.reindex_interval,
            }
        }

    def get_bundled_agents_path(self) -> Optional[Path]:
        """
        Get the path to bundled Peppy-enhanced agents.

        Returns:
            Path to agents directory, or None if not found.
        """
        if self._bundled_agents_path is not None:
            return self._bundled_agents_path

        # Try to find bundled agents relative to peppy installation
        try:
            import peppy
            peppy_root = Path(peppy.__file__).parent.parent
            agents_path = peppy_root / "integrations" / "siggy" / "agents"
            if agents_path.exists():
                self._bundled_agents_path = agents_path
                return agents_path
        except ImportError:
            pass

        # Try common installation paths
        common_paths = [
            Path(__file__).parent / "agents",
            Path.home() / ".peppy" / "agents",
            Path("/usr/local/share/peppy/agents"),
        ]

        for path in common_paths:
            if path.exists():
                self._bundled_agents_path = path
                return path

        return None

    def get_planner_agent_path(self) -> Optional[str]:
        """Get the path to the Peppy-enhanced planner agent."""
        if self.config.custom_planner_path:
            return self.config.custom_planner_path

        agents_path = self.get_bundled_agents_path()
        if agents_path:
            planner = agents_path / "peppy-planner.md"
            if planner.exists():
                return str(planner)

        return None

    def get_executor_agent_path(self) -> Optional[str]:
        """Get the path to the Peppy-enhanced executor agent."""
        if self.config.custom_executor_path:
            return self.config.custom_executor_path

        agents_path = self.get_bundled_agents_path()
        if agents_path:
            executor = agents_path / "peppy-executor.md"
            if executor.exists():
                return str(executor)

        return None

    def get_agent_overrides(self) -> dict:
        """
        Get agent path overrides for SIGI configuration.

        Returns:
            Dict with planner and executor paths to use.
        """
        if not self.config.use_enhanced_agents:
            return {}

        overrides = {}

        planner = self.get_planner_agent_path()
        if planner:
            overrides["planner"] = planner

        executor = self.get_executor_agent_path()
        if executor:
            overrides["executor"] = executor

        return overrides

    def get_index_path(self) -> Path:
        """Get the absolute path to index."""
        index_path = Path(self.config.index_path)
        if not index_path.is_absolute():
            index_path = self.project_root / index_path
        return index_path.resolve()

    def should_auto_index(self) -> bool:
        """Check if auto-indexing should be performed."""
        if not self.config.auto_index:
            return False

        # Check if index is fresh enough
        cache_dir = self.project_root / ".peppy_cache"
        marker = cache_dir / ".last_indexed"

        if not marker.exists():
            return True

        import time
        age_minutes = (time.time() - marker.stat().st_mtime) / 60
        return age_minutes >= self.config.reindex_interval

    def mark_indexed(self):
        """Mark that indexing was performed."""
        cache_dir = self.project_root / ".peppy_cache"
        cache_dir.mkdir(exist_ok=True)
        marker = cache_dir / ".last_indexed"
        marker.touch()

    def get_mcp_config(self) -> dict:
        """
        Get MCP server configuration for Peppy.

        Returns:
            Dict suitable for Claude Code MCP settings.
        """
        return {
            "peppy": {
                "command": "python",
                "args": ["-m", "peppy.server"],
                "env": {
                    "PEPPY_PROJECT_ROOT": str(self.project_root),
                    "PEPPY_CACHE_DIR": str(self.project_root / ".peppy_cache"),
                }
            }
        }

    def generate_setup_instructions(self) -> str:
        """Generate setup instructions for the user."""
        mcp_config = json.dumps({"mcpServers": self.get_mcp_config()}, indent=2)

        return f"""
# Peppy + SIGI Setup Instructions

## 1. Install Peppy (if not already installed)
```bash
pip install peppy
# Or from source:
# pip install -e /path/to/peppy
```

## 2. Add Peppy to Claude Code MCP settings
Add this to your MCP configuration:

```json
{mcp_config}
```

## 3. Enable in .siggy.yml
```yaml
plugins:
  peppy:
    enabled: true
    auto_index: true
    use_enhanced_agents: true
```

## 4. Start using SIGI with Peppy
```bash
/siggy "Your task here"
```

Peppy will automatically:
- Index your codebase on first use
- Use optimized agents for 65-75% token savings
- Re-index periodically based on your config
"""

    def setup(self) -> dict:
        """
        Perform plugin setup.

        Returns:
            Setup result with status and any modifications to apply.
        """
        result = {
            "success": True,
            "messages": [],
            "agent_overrides": {},
            "hooks": [],
        }

        if not self.is_enabled:
            result["messages"].append("Peppy plugin is disabled in config")
            return result

        if not self.is_available():
            result["success"] = False
            result["messages"].append(
                "Peppy is not available. Install with: pip install peppy"
            )
            return result

        # Get agent overrides
        overrides = self.get_agent_overrides()
        if overrides:
            result["agent_overrides"] = overrides
            result["messages"].append(
                f"Using Peppy-enhanced agents: {list(overrides.keys())}"
            )

        # Check if auto-indexing needed
        if self.should_auto_index():
            result["hooks"].append({
                "event": "session_start",
                "action": "index_codebase",
                "path": str(self.get_index_path()),
            })
            result["messages"].append(
                f"Auto-indexing scheduled for: {self.get_index_path()}"
            )

        return result


def create_plugin(siggy_config: dict, project_root: Optional[Path] = None) -> PeppySigiPlugin:
    """
    Factory function to create a Peppy plugin instance.

    This is the main entry point for SIGI to load the plugin.

    Args:
        siggy_config: The full .siggy.yml config dict
        project_root: Project root path

    Returns:
        Configured PeppySigiPlugin instance
    """
    return PeppySigiPlugin(siggy_config, project_root)


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import yaml

    # Load .siggy.yml from current directory or provided path
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".siggy.yml")

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    plugin = create_plugin(config)

    print("Peppy SIGI Plugin Status")
    print("=" * 40)
    print(json.dumps(plugin.get_status(), indent=2))
    print()

    if plugin.is_enabled and plugin.is_available():
        print("Setup Result:")
        print(json.dumps(plugin.setup(), indent=2))
    else:
        print(plugin.generate_setup_instructions())
