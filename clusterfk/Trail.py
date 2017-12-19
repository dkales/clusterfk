class State:
    """
    A representation of the 4x4 state
    """
    pass


class Trail:
    """
    A representation of the differential Trail, containing the state objects
    and also the connecting operations between them
    """
    def initUI(self, parent):
        raise NotImplementedError("Subclasses should implement this")

