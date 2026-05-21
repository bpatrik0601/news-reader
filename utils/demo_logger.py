class DemoLogger:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def step(self, icon: str, message: str):
        if self.enabled:
            print(f"\n{icon} {message}")

    def info(self, message: str):
        if self.enabled:
            print(f"   • {message}")

    def decision(self, message: str):
        if self.enabled:
            print(f"   → {message}")