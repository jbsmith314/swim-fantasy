class Entry:
    """
    Holds all information for an entry in an event
    """
    def __init__(self, event: str, time: float):
        self.event = event
        self.time = time
        self.seed = None
        self.projected_points = None
    
    def __repr__(self) -> str:
        return "Event: " + self.event + "\nTime: " + self.time + "\nSeed: " + self.seed + "\nProjected points: " + self.projected_points

    def __lt__(self, other):
        return self.time < other.time