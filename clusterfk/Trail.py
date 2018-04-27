import json
import pickle
from json import JSONEncoder

import Utils
from clusterfk import Propagation


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
        self.stateprobs = [[0.0] * self.statesize for _ in range(self.statesize)]
        self.statenumbers = [0 for _ in range(self.statesize)]
        self.__iterindex = 0
        self.columnprobs = None

    def __iter__(self):
        return self

    def __repr__(self):
        raise NotImplementedError("Subclasse should implement this")

    def toJSON(self):
        # change sets to lists for easy and readable export
        list_state = [list(list(self.at(row, col)) for row in range(self.staterow)) for col in range(self.statecol)]
        json_rep = {"name": self.name, "state": list_state}
        return json_rep

    def next(self):
        if self.__iterindex >= self.statesize:
            self.__iterindex = 0
            raise StopIteration
        else:
            self.__iterindex += 1
            return self.atI(self.__iterindex - 1)

    def at(self, row, col):
        return self.state[row][col]

    def atI(self, index):
        return self.state[index // self.statecol][index % self.statecol]

    def getRowColDict(self):
        return {(row, col): list(self.at(row, col)) for row in range(self.staterow) for col in range(self.statecol)}

    def set(self, row, col, state):
        self.state[row][col] = state

    def setI(self, index, state):
        self.state[index // self.statecol][index % self.statecol] = state

    def getActiveOnlyState(self):
        raise NotImplementedError("Subclasse should implement this")

    def makeActiveOnly(self):
        for row in range(self.staterow):
            for col in range(self.statecol):
                if self.at(row, col) != {0}:
                    self.set(row, col, {i for i in range(0, 16)})

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

    def __init__(self, rounds, filename, jsontrail, stateclass, staterow, statecol, SBOX):
        self.stateclass = stateclass
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.rounds = rounds
        self.states = {}
        self.sboxDDT = Utils.initDDT(SBOX)
        self.propagations = []

        if filename is not None:
            with open(filename, "r") as f:
                content = f.readlines()

            content = [x for x in content if x.strip() != ""]

            for i in range(0, len(content), self.staterow):
                self._parseStateBlock(map(lambda x: x.strip(), content[i:i + self.staterow]))
        elif jsontrail is not None:
            self._parseJSONTrail(jsontrail)

        self._addPropagation()
        self._addProbability()

    def initUI(self, parent):
        raise NotImplementedError("Subclasses should implement this")

    def _parseStateBlock(self, stateblock):
        raise NotImplementedError("Subclasses should implement this")

    def _parseJSONTrail(self, jsontrail):
        for state in jsontrail["states"]:
            state_sets = [[set(state["state"][row][col]) for row in range(self.staterow)] for col in
                          range(self.statecol)]
            self.states[state["name"]] = self.stateclass(state["name"], state_sets)

    def _addPropagation(self):
        raise NotImplementedError("Subclasses should implement this")

    def _addProbability(self):
        raise NotImplementedError("Subclasses should implement this")

    def propagate(self):
        # do one propagation without mixcolumns, to speed them up later
        for p in self.propagations:
            if not isinstance(p, Propagation.MixColStepDeoxys) and not isinstance(p, Propagation.MixColStep):
                p.propagate()

        # TODO: also restrict to the back
        changed = True
        start = 0
        while changed:
            new_start = len(self.propagations) + 1
            changed = False
            for i, p in enumerate(self.propagations, start):
                p.propagate()
                if p.inchanged or p.outchanged:
                    changed = True
                    if i < new_start:
                        new_start = i
                        if p.inchanged and i > 0:
                            new_start = i - 1

            start = new_start

    def toJSON(self):
        states = map(lambda state: state.toJSON(), self.states.values())

        json_str = {}
        json_str["cipher"] = self.__class__.__name__.replace("Trail", "")
        json_str["rounds"] = self.rounds
        json_str["dimensions"] = {"cells": self.statesize, "rows": self.staterow, "cols": self.statecol}
        json_str["states"] = states

        return json_str

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
