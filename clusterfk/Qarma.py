
import Trail, UI, Propagation, Probability, Utils
from Tkinter import Label, StringVar
from Utils import COLORS

# external modules
import re
import math
import itertools
from copy import deepcopy
import time

STATE_ROW = 4
STATE_COL = 4
STATE_SIZE = STATE_ROW * STATE_COL

SBOX = [0, 14, 2, 10, 9, 15, 8, 11, 6, 4, 3, 7, 13, 12, 1, 5] #Sbox0
SBOX_1 = [10, 13, 14, 6, 15, 7, 3, 5, 9, 8, 0, 12, 11, 1, 2, 4]
SBOX_2 = [11, 6, 8, 15, 13, 0, 9, 14, 3, 7, 4, 5, 12, 2, 1, 10]
P = (0, 11, 6, 13, 10, 1, 12, 7, 5, 14, 3, 8, 15, 4, 9, 2)
P_I = (P.index(x) for x in range(16))
H = (6, 5, 14, 15, 0, 1, 2, 3, 7, 12, 13, 4, 8, 9, 10, 11)

#helper
LFSR_LOOKUP = (0, 8, 9, 1, 2, 10, 11, 3, 4, 12, 13, 5, 6, 14, 15, 7)
LFSR_COMPUTATION_MATRIX = [1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0]
M4_3 = [[0, 1, 2, 1], [1, 0, 1, 2], [2, 1, 0, 1], [1, 2, 1, 0]]

class QarmaState(Trail.State):
    """
     A representation of the 4x4 state of QARMA
     """

    def __init__(self, name, state):
        Trail.State.__init__(self, STATE_ROW, STATE_COL, name, state)

    def __repr__(self):
        return """
    {}:
        {}{}{}{}
        {}{}{}{}
        {}{}{}{}
        {}{}{}{}""".strip().format(self.name, *[x for y in self.state for x in y])

    def getActiveOnlyState(self):
        newstate = QarmaState(self.name, getUndefinedState())
        for row in range(STATE_ROW):
            for col in range(STATE_COL):
                if newstate.at(row, col) != [0]:
                    newstate.set(row, col, {i for i in range(1, STATE_SIZE)})

def getUndefinedState():
    return [[{i for i in range(STATE_SIZE)} for _ in range(STATE_COL)] for _ in range(STATE_ROW)]


class QarmaTrail(Trail.Trail):
    def __init__(self, rounds, filename):
        Trail.Trail.__init__(self, rounds, filename, STATE_ROW, STATE_COL, SBOX)

    def _addProbability(self):
        self.probabilities = []
        for i in range(self.rounds):
            self.probabilities.append(
                Probability.FullroundStepQarma(i,
                                          self.states["S" + str(i)], self.states["A" + str(i + 1)],
                                          self.states["T" + str(i + 1)],
                                          self.states["P" + str(i + 1)], self.states["M" + str(i + 1)],
                                          self.states["S" + str(i + 1)], self.sboxDDT, P, M4_3))

        self.probabilities.append(
            Probability.InnerRoundStepQarma(
                self.states["S" + str(self.rounds)],
                self.states["A" + str(self.rounds + 1)],
                self.states["I" + str(self.rounds + 1)],
                self.states["I" + str(self.rounds + 1) + "_i"],
                self.states["A" + str(self.rounds + 1) + "_i"],
                self.states["S" + str(self.rounds + 2)], self.sboxDDT, P, M4_3))

        for i in range(self.rounds + 2, (self.rounds + 1) * 2):
            self.probabilities.append(
                Probability.FullroundInverseStepQarma(i,
                                                 self.states["S" + str(i)], self.states["M" + str(i)],
                                                 self.states["P" + str(i)], self.states["A" + str(i)],
                                                 self.states["T" + str((self.rounds + 1) * 2 - i)],
                                                 self.states["S" + str(i + 1)], self.sboxDDT, P, M4_3))

    def _addPropagation(self):
        self.propagations = []
        for i in range(self.rounds + 1):
            if i == 0:
                self.propagations.append(
                    Propagation.XORStep(self.states["A" + str(i)],
                                        self.states["S" + str(i)], self.states["T" + str(i)]))
                self.propagations.append(
                    Propagation.SBOXStep(self.states["S" + str(i)],
                                         self.states["A" + str(i + 1)], self.sboxDDT))
            else:
                self.propagations.append(
                    Propagation.XORStep(self.states["A" + str(i)],
                                        self.states["P" + str(i)], self.states["T" + str(i)]))
                self.propagations.append(
                    Propagation.PermutationStep(self.states["P" + str(i)],
                                                self.states["M" + str(i)], P))
                self.propagations.append(
                    Propagation.MixColStep(self.states["M" + str(i)],
                                           self.states["S" + str(i)], M4_3))
                self.propagations.append(
                    Propagation.SBOXStep(self.states["S" + str(i)],
                                         self.states["A" + str(i + 1)], self.sboxDDT))

        # inner round
        self.propagations.append(
            Propagation.PermutationStep(self.states["A" + str(self.rounds + 1)],
                                        self.states["I" + str(self.rounds + 1)], P))
        self.propagations.append(
            Propagation.MixColStep(self.states["I" + str(self.rounds + 1)],
                                   self.states["I" + str(self.rounds + 1) + "_i"], M4_3))
        self.propagations.append(
            Propagation.PermutationStep(self.states["I" + str(self.rounds + 1) + "_i"],
                                        self.states["A" + str(self.rounds + 1) + "_i"], P))

        # tweak
        for i in range(self.rounds):
            self.propagations.append(Propagation.UpdateTweakeyStepQarma(
                                                                 self.states["T" + str(i)],
                                                                 self.states["T" + str(i + 1)],
                                                                 H, LFSR_COMPUTATION_MATRIX, LFSR_LOOKUP))

        # backwards rounds
        for i in range((self.rounds + 1) * 2, self.rounds + 1, -1):
            if i == ((self.rounds + 1) * 2):
                self.propagations.append(
                    Propagation.XORStep(self.states["A" + str(i)],
                                        self.states["S" + str(i)],
                                        self.states["T" + str((self.rounds + 1) * 2 - i)]))
                self.propagations.append(
                    Propagation.SBOXStep(self.states["S" + str(i)],
                                         self.states["A" + str(i - 1)], self.sboxDDT))
            else:
                self.propagations.append(
                    Propagation.XORStep(self.states["A" + str(i)],
                                        self.states["P" + str(i)],
                                        self.states["T" + str((self.rounds + 1) * 2 - i)]))
                self.propagations.append(
                    Propagation.PermutationStep(self.states["P" + str(i)],
                                                self.states["M" + str(i)], P))
                self.propagations.append(
                    Propagation.MixColStep(self.states["M" + str(i)],
                                           self.states["S" + str(i)], M4_3))
                if i == self.rounds + 2:
                    self.propagations.append(
                        Propagation.SBOXStep(self.states["S" + str(i)],
                                             self.states["I" + str(i - 1) + "_i"], self.sboxDDT))
                else:
                    self.propagations.append(
                        Propagation.SBOXStep(self.states["S" + str(i)],
                                             self.states["A" + str(i - 1)], self.sboxDDT))

    def _parseStateBlock(self, stateblock):
        assert len(stateblock) == 4
        curr_rounds = map(lambda x: int(x.split(" ")[0]), stateblock)
        assert all(x == curr_rounds[0] for x in curr_rounds)
        curr_round = curr_rounds[0]
        num_states = map(lambda x: x.count(":"), stateblock)
        assert all(x == num_states[0] for x in num_states)
        num_states = num_states[0]
        assert num_states in (4, 5, 8)

        cellregex = re.compile("([a-zA-Z]): ([-x]*)")

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
                    row.append({int(statestr, 2)})
                state.append(row)

            name = name + str(curr_round)
            assert name not in self.states or curr_round == self.rounds + 1
            if name in self.states:
                name = name + "_i"
            self.states[name] = QarmaState(name, state)

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

            self.states[name] = QarmaState(name, state)
            self.states[name2] = QarmaState(name2, state2)

    def initUI(self, parentui):
        # forward rounds
        col = 1
        row = 0
        for i in range(self.rounds + 1):
            if i != 0:
                col += 2
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.textvar = v
                l.grid(fill=None, row=row, column=col, columnspan=2)
                parentui.probabilitylabels["M" + str(i)] = l
                col += 1
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.textvar = v
                l.grid(fill=None, row=row, column=col, columnspan=2)
                parentui.probabilitylabels["S" + str(i)] = l
                col += 2
            else:
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.textvar = v
                l.grid(fill=None, row=row, column=col, columnspan=3)
                parentui.probabilitylabels["S" + str(i)] = l
                col += 3

        col = 0
        row += 1
        for i in range(self.rounds + 1):
            UI.StateUI(parentui, row, col, self.states["A" + str(i)])
            col += 2
            if i != 0:
                UI.StateUI(parentui, row, col, self.states["P" + str(i)])
                col += 1
                UI.StateUI(parentui, row, col, self.states["M" + str(i)])
                col += 1
            UI.StateUI(parentui, row, col, self.states["S" + str(i)])
            col += 1

        # inner round forwards
        UI.StateUI(parentui, row, col, self.states["A" + str(self.rounds+1)])
        col += 1
        UI.StateUI(parentui, row, col, self.states["I" + str(self.rounds+1)])

        # tweak
        col = 0
        row += 1
        for i in range(self.rounds + 1):
            UI.StateUI(parentui, row, col, self.states["T" + str(i)], gridopts={"columnspan": 3})
            if i != 0:
                col += 2
            col += 3

        col -= 1

        v = StringVar()
        l = Label(parentui.trailframe, textvariable=v)
        l.textvar = v
        l.grid(fill=None, row=row, column=col, columnspan=3)
        parentui.probabilitylabels["I"] = l

        # backwards rounds
        col = 0
        row += 1
        for i in range((self.rounds + 1) * 2, self.rounds + 1, -1):
            UI.StateUI(parentui, row, col, self.states["A" + str(i)])
            col += 2
            if i != (self.rounds + 1) * 2:
                UI.StateUI(parentui, row, col, self.states["P" + str(i)])
                col += 1
                UI.StateUI(parentui, row, col, self.states["M" + str(i)])
                col += 1
            UI.StateUI(parentui, row, col, self.states["S" + str(i)])
            col += 1

        # inner round backwards
        UI.StateUI(parentui, row, col, self.states["I" + str(self.rounds+1) + "_i"])
        col += 1
        UI.StateUI(parentui, row, col, self.states["A" + str(self.rounds+1) + "_i"])

        col = 1
        row += 1
        for i in range(self.rounds + 1):
            if i != 0:
                col += 2
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.textvar = v
                l.grid(fill=None, row=row, column=col, columnspan=2)
                parentui.probabilitylabels["M" + str((self.rounds + 1) * 2 - i)] = l
                col += 1
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.grid(fill=None, row=row, column=col, columnspan=2)
                l.textvar = v
                parentui.probabilitylabels["S" + str((self.rounds + 1) * 2 - i)] = l
                col += 2
            else:
                v = StringVar()
                l = Label(parentui.trailframe, textvariable=v)
                l.grid(fill=None, row=row, column=col, columnspan=3)
                l.textvar = v
                parentui.probabilitylabels["S" + str((self.rounds + 1) * 2 - i)] = l
                col += 3

    def updateColorList(self):
        stateset = self.getSetOfCurrentStates()
        # assert len(stateset) <= len(COLORS)
        colors = COLORS.values()
        if len(stateset) > len(COLORS):
            colors = colors + ["#999999"]*(len(stateset)- len(COLORS.values()))

            
        self.colorlist = {state: color for state, color in zip(stateset, colors)}

        # for familarity, guarantee that 0xa is red
        diff, colorname = frozenset([0xa]), "red"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in self.colorlist.values():
                old_red = self.colorlist.keys()[self.colorlist.values().index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]
        # for familarity, guarantee that a,f,d,5 is green
        diff, colorname = frozenset([0xa, 0xd, 0xf, 0x5]), "green"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in self.colorlist.values():
                old_red = self.colorlist.keys()[self.colorlist.values().index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]
        # for familarity, guarantee that a,f is yellow
        diff, colorname = frozenset([0xa, 0xf]), "yellow"
        if diff in self.colorlist and self.colorlist[diff] != COLORS[colorname]:
            if COLORS[colorname] in self.colorlist.values():
                old_red = self.colorlist.keys()[self.colorlist.values().index(COLORS[colorname])]
                self.colorlist[diff], self.colorlist[old_red] = COLORS[colorname], self.colorlist[diff]
            else:
                self.colorlist[diff] = COLORS[colorname]

    def printTrail(self):
        for k, v in self.states.items():
            print v

    def getActiveOnlyTrail(self):
        newtrail = QarmaTrail(self.rounds)
        for k, v in self.states.items():
            newtrail.states[k] = v.getActiveOnlyState()

    def propagate(self):
        # do one propagation without mixcolumns, to speed them up later
        for p in self.propagations:
            if not isinstance(p, Propagation.MixColStep):
                p.propagate()

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

        self._propagateSameCells()

    def _propagateSameCells(self):
        '''
        cellcounter = 1
        for state in self.states.values():
            state.statenumbers = [0 for _ in range(16)]
        for i in range(1, self.rounds + 1) + range(self.rounds + 2, (self.rounds + 1) * 2):
            instate = self.states["M" + str(i)]
            outstate = self.states["S" + str(i)]
            permstate = self.states["P" + str(i)]
            addstate = self.states["A" + str(i)]
            for col in range(STATE_COL):
                incol = [instate.at(row, col) for row in range(STATE_ROW)]
                outcol = [outstate.at(row, col) for row in range(STATE_ROW)]
                if incol.count([0]) + outcol.count([0]) == 4:
                    states = [x for x in incol + outcol if x != [0]]
                    newstate = ((states[0] & states[1]) & states[2]) & states[3]
                    inidx = [i for i in range(4) if incol[i] != [0]]
                    outidx = [i for i in range(4) if outcol[i] != [0]]
                    if len(newstate) > 1:
                        for row in inidx:
                            instate.statenumbers[row * 4 + col] = cellcounter
                            permstate.statenumbers[P[row * 4 + col]] = cellcounter
                            addstate.statenumbers[P[row * 4 + col]] = cellcounter
                        for row in outidx:
                            outstate.statenumbers[row * 4 + col] = cellcounter
                        cellcounter += 1

        instate = self.states["A" + str(self.rounds + 1)]
        outstate = self.states["a" + str(self.rounds + 1)]
        for col in range(4):
            incol = [instate.at(row, col) for row in range(4)]
            outcol = [outstate.at(row, col) for row in range(4)]
            if incol.count([0]) + outcol.count([0]) == 4:
                states = [x for x in incol + outcol if x != [0]]
                newstate = ((states[0] & states[1]) & states[2]) & states[3]
                inidx = [i for i in range(4) if incol[i] != [0]]
                outidx = [i for i in range(4) if outcol[i] != [0]]
                if len(newstate) > 1:
                    for row in inidx:
                        instate.statenumbers[row * 4 + col] = cellcounter
                    for row in outidx:
                        outstate.statenumbers[row * 4 + col] = cellcounter
                    cellcounter += 1
        '''

    def getProbability(self, verbose=False):
        totalprob = 1.0

        # reset other stateprobs to 0, since they get recursivly calculated
        for state in self.states.values():
            state.stateprobs = [[0.0] * 16 for _ in range(16)]

        # set the probability of the first state to a uniform distribution
        self.states["S0"].columnprobs = {}
        for col in range(4):
            self.states["S0"].columnprobs[(0 + col, 4 + col, 8 + col, 12 + col)] = {}
            total = len(self.states["S0"].at(0, col)) * len(self.states["S0"].at(1, col)) * len(
                self.states["S0"].at(2, col)) * len(self.states["S0"].at(3, col))
            for a, b, c, d in itertools.product(self.states["S0"].at(0, col), self.states["S0"].at(1, col),
                                                self.states["S0"].at(2, col), self.states["S0"].at(3, col)):
                self.states["S0"].columnprobs[(0 + col, 4 + col, 8 + col, 12 + col)][(a, b, c, d)] = 1.0 / total
        for i in range(16):
            for poss in self.states["S0"].atI(i):
                self.states["S0"].stateprobs[i][poss] = 1.0 / len(self.states["S0"].atI(i))

        for prob in self.probabilities:
            totalprob *= prob.getProbability(verbose=verbose)[0]

        inputposs = 1
        outputposs = 1
        for i in range(STATE_SIZE):
            inputposs *= len(self.states["A0"].atI(i))
            outputposs *= len(self.states["A" + str((self.rounds + 1) * 2)].atI(i))

        print "inputposs : 2**{}".format(math.log(inputposs, 2))
        print "outputposs: 2**{}".format(math.log(outputposs, 2))
        N = 2.0 / (totalprob * inputposs)
        N_phi = 2 ** (-64) * outputposs / totalprob
        if verbose:
            print "Overall Probability: 2**{}".format(math.log(totalprob, 2))
            print "N                  : 2**{}".format(math.log(N, 2))
            print "N_phi              : 2**{}".format(math.log(N_phi, 2))
        return totalprob

    #TODO adapt and make dynamic
    def exportToLatex(self, filehandle):
        output = []
        output.append(r"""
    \documentclass[a4paper,landscape,11pt]{article}

    \usepackage[margin=.5in]{geometry}
    \usepackage{amsmath}
    \usepackage{xcolor}
    \usepackage{tikz}
    \usetikzlibrary{calc}
    \usetikzlibrary{arrows.meta}
    """)
        for color, hexcode in COLORS.items():
            output.append("\definecolor{solarized" + color + "}{HTML}{" + hexcode[1:] + "}")

        output.append(r"""
    \colorlet{raster}{black}

    \pgfmathsetmacro\hi{5}
    \pgfmathsetmacro\lo{-5}
    \pgfmathsetmacro{\xmax}{4}
    \pgfmathsetmacro{\ymax}{4}
    \pgfmathsetmacro{\xmaxm}{int(\xmax-1)}
    \pgfmathsetmacro{\ymaxm}{int(\ymax-1)}

    \tikzset{next/.style={->,>=latex}}
    \newcommand{\drawstate}[4][]{
        \begin{scope}[#1]
          \foreach \row/\col/\colour in {#4} {\fill[\colour] (\col,-\row) rectangle ++(1,-1);}
          \foreach \x in {1,...,\xmaxm} \draw[raster] (\x,0) -- ++(0,-\ymax); 
          \foreach \y in {1,...,\ymaxm} \draw[raster] (0,-\y) -- ++(\xmax,0); 
          \draw (0,0) rectangle (\xmax,-\ymax);
          \coordinate (#2_west) at (0,-2);
          \coordinate (#2_east) at (\xmax,-2);
          \coordinate (#2_south) at (2,-\ymax);
          \coordinate (#2_north) at (2,0);
          %\node[above] at (2,0) {#3};
        \end{scope}
    }
    \newcommand{\drawxor}[2][]{
        \begin{scope}[#1]
          \draw[thin] (2,-2) circle (2ex)
                       +(-2ex,0) coordinate[name=#2_west] -- +(2ex,0) coordinate[name=#2_east]
                       +(0,-2ex) coordinate[name=#2_south] -- +(0,2ex) coordinate[name=#2_north];
        \end{scope}
    }

    \newcommand{\SB}{\textsf{S}}
    \newcommand{\SR}{\textsf{P}}
    \newcommand{\MC}{\textsf{M}}
    \newcommand{\AC}{\textsf{+}}

    \begin{document}
    \pagestyle{empty}

    \begin{figure}[p]
    \centering
    """)
        hi = r"\hi"
        lo = r"\lo"
        tin = "I"  # r"{\text{in}}"
        tout = "O"  # r"{\text{out}}"
        ct = "  0"
        x = 0
        stepnext = 6
        stepxor = 3
        numrounds = self.rounds
        rnds = range(numrounds)
        rows = range(4)
        cols = range(4)
        dirs = ['in', 'out']

        output.append(r"\caption{" + "Mantis-{R}: {S} active S-boxes, $2^{{{P:.2f}}}$ probability".format(R=numrounds,
                                                                                                          S=sum([1 if
                                                                                                                 self.states[
                                                                                                                     "S" + str(
                                                                                                                         s)].atI(
                                                                                                                     i) != [
                                                                                                                     0] else 0
                                                                                                                 for i
                                                                                                                 in
                                                                                                                 range(
                                                                                                                     16)
                                                                                                                 for s
                                                                                                                 in
                                                                                                                 range(
                                                                                                                     self.rounds + 1) + range(
                                                                                                                     self.rounds + 2,
                                                                                                                     self.rounds * 2 + 3)]),
                                                                                                          P=math.log(
                                                                                                              self.getProbability(),
                                                                                                              2)) + r"}")
        output.append(r"\vspace{1cm}")

        def getstate(shortname, dir, rnd):
            if dir == "in" or dir == None:
                return self.states[shortname + str(rnd)].getRowColDict()
            elif dir == "out":
                return self.states[shortname + str((numrounds + 1) * 2 - rnd)].getRowColDict()

        def state2sbs(xshift, yshift, sname, sName, vrcs):
            return r"  \drawstate[xshift=" + str(xshift) + " cm,yshift=" + str(yshift) + \
                   r" cm]{" + str(sname) + r"}{" + str(sName) + r"}{" + \
                   ",".join([str(row) + "/" + str(col) + "/solarized" + \
                             COLORS.keys()[COLORS.values().index(self.colorlist[frozenset(vrcs[row, col])])] for row in
                             rows for col in cols if vrcs[row, col] != [0]]) + \
                   r"}"

        def xor(xshift, yshift, sname):
            return r"  \drawxor[xshift=" + str(xshift) + " cm,yshift=" + str(yshift) + r" cm]{" + str(sname) + r"}"

        def nextstate(Pin, Pout, fun=""):
            return linkstate(Pin + "_east", Pout + "_west", fun)

        def prevstate(Pin, Pout, fun=""):
            return linkstate(Pout + "_west", Pin + "_east", fun)

        def linkstate(Pin, Pout, fun="", extra=""):
            # TODO: add latex arrow.meta definitions since xor nodes are too close for arrows
            if fun:
                return r"  \draw[next] (" + Pin + r") -- node[above, font=\scriptsize] {" + fun + "} (" + Pout + r");"
            else:
                return r"  \draw[next] (" + Pin + r") -- (" + Pout + r");"

        def label(xin, xout, ltext):
            return r"  \draw[|<->|,>=latex] (" + str(xin + 2) + ",2*" + str(hi) + ") -- node[above=1ex] {" + ltext + \
                   "} (" + str(xout + 2) + ",2*" + str(hi) + ");"

        def labelprob(xin, yin, ltext):
            return r"  \draw node[above=1ex] at (" + str(xin + 2) + ",1*" + str(yin) + r") {\scriptsize " + ltext + "};"

        output.append(r"""\begin{tikzpicture}[scale=.15]""")

        # initialization, finalization
        x -= 2 * stepxor
        output.append(label(x, x + 2 * stepxor, "Initialization"))
        output.append(state2sbs(x, hi, "xi_1", "$x^" + tin + "_{-1}$", getstate("A", "in", 0)))
        output.append(state2sbs(x, lo, "xo_1", "$x^" + tout + "_{-1}$", getstate("A", "out", 0)))
        x += stepxor
        output.append(state2sbs(x, ct, "th_1", "$t_{-1}\qquad$", getstate("T", None, 0)))
        x += stepxor
        output.append(xor(x - stepxor, hi, "ai_1"))
        output.append(xor(x - stepxor, lo, "ao_1"))
        output.append(
            nextstate("xi_1", "ai_1") + " " + linkstate("ai_1_east", r"0,\hi-2") + " " + linkstate("th_1_north",
                                                                                                   "ai_1_south"))
        output.append(
            prevstate("xo_1", "ao_1") + " " + linkstate(r"0,\lo-2", "ao_1_east") + " " + linkstate("th_1_south",
                                                                                                   "ao_1_north"))

        # outer rounds
        for rnd in rnds:
            prob = self.probabilities[rnd]
            overallprob, sboxprob, mixcolprob = prob.getProbability()
            output.append(labelprob(x + 1 * stepxor + 1.5 * stepnext, hi, "$2^{" + \
                                    "{0:.2f}".format(math.log(overallprob, 2)) + "}$"))
            prob = self.probabilities[-rnd - 1]
            overallprob, sboxprob, mixcolprob = prob.getProbability()
            output.append(labelprob(x + 1 * stepxor + 1.5 * stepnext, r"2.75*" + lo, "$2^{" + \
                                    "{0:.2f}".format(math.log(overallprob, 2)) + "}$"))
            r = str(rnd)
            output.append(label(x, x + 2 * stepxor + 3 * stepnext, "Round " + r))
            output.append(state2sbs(x, hi, "xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("S", "in", rnd)))
            output.append(state2sbs(x, lo, "xo" + r, "$x^" + tout + "_{" + r + "}$", getstate("S", "out", rnd)))
            x += stepnext
            output.append(state2sbs(x, hi, "Xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("A", "in", rnd + 1)))
            output.append(state2sbs(x, lo, "Xo" + r, "$x^" + tout + "_{" + r + "}$", getstate("A", "out", rnd + 1)))
            output.append(nextstate("xi" + r, "Xi" + r, r"\SB"))
            output.append(prevstate("xo" + r, "Xo" + r, r"\SB"))
            x += stepxor
            output.append(state2sbs(x, ct, "th" + r, "$t_{" + r + "}\qquad$", getstate("T", None, rnd + 1)))
            output.append(nextstate("th" + str(rnd - 1).replace("-", "_"), "th" + r, "$h$"))
            x += stepxor
            output.append(state2sbs(x, hi, "yi" + r, "$y^" + tin + "_{" + r + "}$", getstate("P", "in", rnd + 1)))
            output.append(state2sbs(x, lo, "yo" + r, "$y^" + tout + "_{" + r + "}$", getstate("P", "out", rnd + 1)))
            output.append(xor(x - stepxor, hi, "ai" + r))
            output.append(xor(x - stepxor, lo, "ao" + r))
            output.append(nextstate("Xi" + r, "ai" + r) + " " + nextstate("ai" + r, "yi" + r) + " " + linkstate(
                "th" + r + "_north", "ai" + r + "_south"))
            output.append(prevstate("Xo" + r, "ao" + r) + " " + prevstate("ao" + r, "yo" + r) + " " + linkstate(
                "th" + r + "_south", "ao" + r + "_north"))
            x += stepnext
            output.append(state2sbs(x, hi, "Pi" + r, "", getstate("M", "in", rnd + 1)))
            output.append(state2sbs(x, lo, "Po" + r, "", getstate("M", "out", rnd + 1)))
            output.append(nextstate("yi" + r, "Pi" + r, r"\SR"))
            output.append(prevstate("yo" + r, "Po" + r, r"\SR"))
            x += stepnext
            output.append(r"  \draw[next] (Pi" + r + r"_east) -- node[above,font=\scriptsize] {\MC} ++(2,0);")
            output.append(r"  \draw[next] (Po" + r + r"_east) +(2,0) -- node[above,font=\scriptsize] {\MC} ++(0,0);")

        # middle rounds
        prob = self.probabilities[self.rounds]
        overallprob, sboxprob, mixcolprob = prob.getProbability()
        output.append(labelprob(x + 0.8 * stepnext, r"0.9*" + lo, "$2^{" + \
                                "{0:.2f}".format(math.log(overallprob, 2)) + "}$"))
        output.append(label(x, x + 7 + stepnext, "Inner"))
        output.append(state2sbs(x, hi, "xi" + str(numrounds), "$x^" + tin + "_{" + str(numrounds) + "}$",
                                getstate("S", "in", numrounds)))
        output.append(state2sbs(x, lo, "xo" + str(numrounds), "$x^" + tout + "_{" + str(numrounds) + "}$",
                                getstate("S", "out", numrounds)))
        x += stepnext
        output.append(state2sbs(x, hi, "Xi" + str(numrounds), "$x^" + tin + "_{" + str(numrounds) + "}$",
                                getstate("A", "in", numrounds + 1)))
        output.append(state2sbs(x, lo, "Xo" + str(numrounds), "$x^" + tout + "_{" + str(numrounds) + "}$",
                                getstate("a", "out", numrounds + 1)))
        output.append(nextstate("xi" + str(numrounds), "Xi" + str(numrounds), r"\SB"))
        output.append(prevstate("xo" + str(numrounds), "Xo" + str(numrounds), r"\SB"))
        output.append(r"  \draw[next] (Xi" + str(
            numrounds) + r"_east) -| ++(1,\lo) node[right,font=\scriptsize] {\MC} |- (Xo" + str(numrounds) + "_east);")

        # legend for state colors

        for i, (state, color) in enumerate(self.colorlist.items()):
            statestr = ",".join(["{:x}".format(x) for x in state])
            colorstring = "solarized" + COLORS.keys()[COLORS.values().index(self.colorlist[frozenset(state)])]
            x = 5
            y = -15 - i * 2
            output.append(
                r"\node [draw, rectangle, fill=" + colorstring + r", minimum width=1, minimum height=1, label=right:{\tiny " + statestr + r"}] at (" + str(
                    x) + "," + str(y) + r") {};")

        output.append(r"""\end{tikzpicture}
    \end{figure}

    \end{document}
    """)
        output = "\n".join(output)

        filehandle.write(output)
