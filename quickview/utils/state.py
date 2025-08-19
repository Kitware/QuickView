"""
View state management classes for QuickView.

This module contains the ViewContext and ViewRegistry classes that manage
the persistent state and configuration of visualization views across
variable selection cycles.
"""

from typing import Dict, List, Optional


class ViewRegistry:
    """Central registry for managing views - tracks only currently selected variables."""

    def __init__(self):
        self._contexts: Dict[str, "ViewContext"] = {}
        self._view_order: List[str] = []

    def register_view(self, variable: str, context: "ViewContext"):
        """Register a new view or update existing one."""
        self._contexts[variable] = context
        if variable not in self._view_order:
            self._view_order.append(variable)

    def get_view(self, variable: str) -> Optional["ViewContext"]:
        """Get view context for a variable."""
        return self._contexts.get(variable)

    def remove_view(self, variable: str):
        """Remove a view from the registry."""
        if variable in self._contexts:
            del self._contexts[variable]
            self._view_order.remove(variable)

    def get_ordered_views(self) -> List["ViewContext"]:
        """Get all views in order they were added."""
        return [
            self._contexts[var] for var in self._view_order if var in self._contexts
        ]

    def get_all_variables(self) -> List[str]:
        """Get all registered variable names."""
        return list(self._contexts.keys())

    def items(self):
        """Iterate over variable-context pairs."""
        return self._contexts.items()

    def clear(self):
        """Clear all registered views."""
        self._contexts.clear()
        self._view_order.clear()

    def __len__(self):
        """Get number of registered views."""
        return len(self._contexts)

    def __contains__(self, variable: str):
        """Check if a variable is registered."""
        return variable in self._contexts


class ViewContext:
    """Context storing ParaView objects and persistent configuration.
    
    This class is critical for maintaining user configuration across
    variable selection/deselection cycles. It stores both the ParaView
    rendering objects and the user's chosen visualization settings.
    """

    def __init__(self, variable: str, index: int):
        self.variable = variable
        self.index = index  # Current position in state arrays
        self.view_proxy = None  # ParaView render view
        self.data_representation = None  # ParaView data representation

        # Persistent configuration that survives variable selection changes
        self.colormap = None  # Will persist colormap choice
        self.use_log_scale = False
        self.invert_colors = False
        self.min_value = None  # Computed or manual
        self.max_value = None  # Computed or manual
        self.override_range = False  # Track if manually set
        self.has_been_configured = False  # Track if user has modified settings


def build_color_information(state: Dict) -> ViewRegistry:
    """Build a ViewRegistry from saved state information.
    
    This function is used for backward compatibility with saved states.
    It creates an empty registry and preserves layout information if present.
    
    Args:
        state: Dictionary containing saved state with optional 'layout' key
        
    Returns:
        ViewRegistry: A new registry instance with saved layout if available
    """
    registry = ViewRegistry()

    # Store layout if provided (for backward compatibility)
    layout = state.get("layout", None)
    if layout:
        registry._saved_layout = [item.copy() for item in layout]

    return registry