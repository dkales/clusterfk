import Utils

class State:
    """
    A representation of the 4x4 state
    """
    def __init__(self, staterow, statecol, name, state):
        self.name = name
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.state = state
        self.stateprobs = [[0.0]*self.statesize for _ in range(self.statesize)]
        self.statenumber = [0 for _ in range(self.statesize)]
        self.__iterindex = 0
        self.columnprobs = None

    def __iter__(self):
        return self

    def __repr__(self):
        raise NotImplementedError("Subclasse should implement this")

    def next(self):
        if self.__iterindex >= self.statesize:
            self.__iterindex = 0
            raise StopIteration
        else:
            self.__iterindex += 1
            return self.atI(self.__iterindex-1)

    def at(self, row, col):
        return self.state[row][col]
    def atI(self, index):
        return self.state[index//self.statecol][index%self.statecol]

    def getRowColDict(self):
        return { (row,col) : list(self.at(row,col)) for row in range(self.staterow) for col in range(self.staterow)}

    def set(self, row, col, state):
        self.state[row][col] = state
    def setI(self, index, state):
        self.state[index//self.statecol][index%self.statecol] = state

    def getActiveOnlyState(self):
        raise NotImplementedError("Subclasse should implement this")

    def makeActiveOnly(self):
        for row in range(self.staterow):
            for col in range(self.statecol):
                if self.at(row, col) != {0}:
                    self.set(row, col, {i for i in range(0,self.statesize)})

    def statesEqual(self, state):
        for row in range(self.staterow):
            for col in range(self.statecol):
                if len(self.at(row, col) ^ state[row][col]) is not 0:
                    return False
        return True

class Trail:
    """
    A representation of the differential Trail, containing the state objects
    and also the connecting operations between them
    """
    def __init__(self, rounds, filename, staterow, statecol, SBOX):
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.rounds = rounds
        self.states = {}
        self.sboxDDT = Utils.initDDT(SBOX)

        with open(filename, "r") as f:
            content = f.readlines()

        content = [x for x in content if x.strip() != ""]

        for i in range(0, len(content), self.staterow):
            self._parseStateBlock(map(lambda x: x.strip(), content[i:i + self.staterow]))

        self._addPropagation()
        self._addProbability()

    def initUI(self, parent):
        raise NotImplementedError("Subclasses should implement this")

    def _parseStateBlock(self, stateblock):
        raise NotImplementedError("Subclasses should implement this")

    def _addPropagation(self):
        raise NotImplementedError("Subclasses should implement this")

    def _addProbability(self):
        raise NotImplementedError("Subclasses should implement this")

    def makeActiveOnly(self):
        for name, state in self.states.items():
            if "T" not in name:
                state.makeActiveOnly()

    def getSetOfCurrentStates(self):
        stateset = set()
        for state in self.states.values():
            for cell in state:
                if cell != {0}:
                    stateset.add(frozenset(cell))

        return stateset