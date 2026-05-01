class RenderMixin:
    def draw(self, screen, camera_offset_x: float = 0, camera_offset_y: float = 0) -> None:
        raise NotImplementedError("Subclasses must implement draw()")