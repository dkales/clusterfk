from . import Utils
from .Utils import COLORS
from clusterfk import Propagation

# external
import re

class State:
    """
    A representation of the 4x4 state
    """

    def __init__(self, name, state, staterow=4, statecol=4, statebitsize=64):
        self.name = name
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.statebitsize = statebitsize
        self.state = state
        self.stateprobs = [[0.0] * 2**(self.statebitsize//self.statesize) for _ in range(self.statesize)]
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

    def __next__(self):
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
                    self.set(row, col, {i for i in range(0, 2 ** (self.statebitsize / self.statesize))})

    def statesEqual(self, state):
        for row in range(self.staterow):
            for col in range(self.statecol):
                if len(self.at(row, col) ^ state[row][col]) != 0:
                    return False
        return True


class Trail:
    """
    A representation of the differential Trail, containing the state objects
    and also the connecting operations between them
    """

    def __init__(self, rounds, filename, jsontrail, stateclass, SBOX, statebitsize=64, staterow=4, statecol=4,
                 alpha_reflection=True):
        self.stateclass = stateclass
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.statebitsize = statebitsize
        self.rounds = rounds
        self.states = {}
        self.sboxDDT = Utils.initDDT(SBOX)
        self.propagations = []
        self.alpha_reflection = alpha_reflection

        if filename is None and jsontrail is None:
            raise Exception("Provide either trail-file (.trail) or jsontrail (.json)")

        if filename is not None:
            with open(filename, "r") as f:
                content = f.readlines()

            content = [x for x in content if x.strip() != ""]

            for i in range(0, len(content), self.staterow):
                self._parseStateBlock([x.strip() for x in content[i:i + self.staterow]])

        elif jsontrail is not None:
            self._parseJSONTrail(jsontrail)

        self._addPropagation()
        self._addProbability()

    def initUI(self, parent):
        raise NotImplementedError("Subclasses should implement this")

    def _parseStateBlock(self, stateblock):
        assert len(stateblock) == self.staterow
        curr_rounds = [int(x.split(" ")[0]) for x in stateblock]
        assert all(x == curr_rounds[0] for x in curr_rounds)
        curr_round = curr_rounds[0]
        num_states = [x.count(":") for x in stateblock]
        assert all(x == num_states[0] for x in num_states)
        num_states = num_states[0]
        assert num_states in (4, 5, 8)

        cellregex = re.compile("([a-zA-Z]): ([-x*]*)")

        if num_states in (4, 5):
            state = []
            name = ""
            for s in stateblock:
                result = re.findall(cellregex, s)
                assert len(result) >= 4
                row = []
                for i in range(4):
                    match = result[i]
                    assert name == "" or name == match[0]
                    name = match[0]
                    statestr = match[1].replace("x", "1").replace("-", "0")
                    if "*" in statestr:
                        row.append({i for i in range(0, self.statebitsize / self.statesize)})
                    else:
                        row.append({int(statestr, 2)})
                state.append(row)

            res_name = name + str(curr_round)
            # assert name not in self.states
            assert res_name not in self.states or curr_round == self.rounds + 1  # double inner steps for Qarma
            if res_name in self.states:
                res_name = name + "_i" + str(curr_round)
            self.states[res_name] = self.stateclass(res_name, state)

        elif num_states == 8:
            state = []
            state2 = []
            name = ""
            name2 = ""
            for s in stateblock:
                result = re.findall(cellregex, s)
                assert len(result) >= 4
                row = []
                for i in range(4):
                    match = result[i]
                    assert name == "" or name == match[0]
                    name = match[0]
                    statestr = match[1].replace("x", "1").replace("-", "0")
                    if "*" in statestr:
                        row.append({i for i in range(0, self.statebitsize / self.statesize)})
                    else:
                        row.append({int(statestr, 2)})
                state.append(row)
                row = []
                for i in range(4, 8):
                    match = result[i]
                    assert name2 == "" or name2 == match[0]
                    name2 = match[0]
                    statestr = match[1].replace("x", "1").replace("-", "0")
                    row.append({int(statestr, 2)})
                state2.append(row)

            name += str(curr_round)
            name2 += str(curr_round)
            assert name not in self.states
            assert name2 not in self.states

            self.states[name] = self.stateclass(name, state)
            self.states[name2] = self.stateclass(name2, state2)

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

        print("Finished Propagation")

    def toJSON(self):
        states = [state.toJSON() for state in list(self.states.values())]

        json_str = {}
        json_str["cipher"] = self.__class__.__name__.replace("Trail", "")
        json_str["rounds"] = self.rounds
        json_str["dimensions"] = {"cells": self.statesize, "rows": self.staterow, "cols": self.statecol}
        json_str["states"] = states

        return json_str

    def makeActiveOnly(self):
        for name, state in list(self.states.items()):
            if "T" not in name:
                state.makeActiveOnly()

    def getSetOfCurrentStates(self):
        stateset = set()
        for state in list(self.states.values()):
            for cell in state:
                if cell != {0}:
                    stateset.add(frozenset(cell))

        return stateset

    def updateColorList(self):
        stateset = self.getSetOfCurrentStates()
        #self.colorlist = #{state: color for state, color in zip(stateset, COLORS.values())}
        self.colorlist = {state: color for state, color in
                          zip(stateset, list(COLORS.values()) + ["#999999"] * (len(stateset) - len(list(COLORS.values()))))}
        # for familarity, guarantee that 0xa is red
        diff, colorname = frozenset([0xa]), "red"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in list(self.colorlist.values()):
                old_red = list(self.colorlist.keys())[list(self.colorlist.values()).index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]
        # for familarity, guarantee that a,f,d,5 is green
        diff, colorname = frozenset([0xa, 0xd, 0xf, 0x5]), "green"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in list(self.colorlist.values()):
                old_red = list(self.colorlist.keys())[list(self.colorlist.values()).index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]

        # for familarity, guarantee that 0-f is grey
        diff, colorname = frozenset(
            [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e,
             0x0f]), "grey"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in list(self.colorlist.values()):
                old_red = list(self.colorlist.keys())[list(self.colorlist.values()).index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]

        # for familarity, guarantee that a,f is yellow
        diff, colorname = frozenset([0xa, 0xf]), "yellow"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in list(self.colorlist.values()):
                old_red = list(self.colorlist.keys())[list(self.colorlist.values()).index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]

    def printTrail(self):
        for k, v in list(self.states.items()):
            print(v)

    def getActiveOnlyTrail(self):
        # TODO: check if this correctly calls child-ctor
        newtrail = type(self)(self.rounds)
        for k, v in list(self.states.items()):
            newtrail.states[k] = v.getActiveOnlyState()
