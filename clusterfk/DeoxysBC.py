import Trail, UI, Propagation, Probability, Utils
from Tkinter import Label, StringVar
from Utils import COLORS

# external modules
import math

STATE_ROW = 4
STATE_COL = 4
STATE_SIZE = STATE_ROW * STATE_COL
STATE_BIT_SIZE = 128

SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
]

SBOX_I = [
    0x52, 0x09, 0x6A, 0xD5, 0x30, 0x36, 0xA5, 0x38, 0xBF, 0x40, 0xA3, 0x9E, 0x81, 0xF3, 0xD7, 0xFB,
    0x7C, 0xE3, 0x39, 0x82, 0x9B, 0x2F, 0xFF, 0x87, 0x34, 0x8E, 0x43, 0x44, 0xC4, 0xDE, 0xE9, 0xCB,
    0x54, 0x7B, 0x94, 0x32, 0xA6, 0xC2, 0x23, 0x3D, 0xEE, 0x4C, 0x95, 0x0B, 0x42, 0xFA, 0xC3, 0x4E,
    0x08, 0x2E, 0xA1, 0x66, 0x28, 0xD9, 0x24, 0xB2, 0x76, 0x5B, 0xA2, 0x49, 0x6D, 0x8B, 0xD1, 0x25,
    0x72, 0xF8, 0xF6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xD4, 0xA4, 0x5C, 0xCC, 0x5D, 0x65, 0xB6, 0x92,
    0x6C, 0x70, 0x48, 0x50, 0xFD, 0xED, 0xB9, 0xDA, 0x5E, 0x15, 0x46, 0x57, 0xA7, 0x8D, 0x9D, 0x84,
    0x90, 0xD8, 0xAB, 0x00, 0x8C, 0xBC, 0xD3, 0x0A, 0xF7, 0xE4, 0x58, 0x05, 0xB8, 0xB3, 0x45, 0x06,
    0xD0, 0x2C, 0x1E, 0x8F, 0xCA, 0x3F, 0x0F, 0x02, 0xC1, 0xAF, 0xBD, 0x03, 0x01, 0x13, 0x8A, 0x6B,
    0x3A, 0x91, 0x11, 0x41, 0x4F, 0x67, 0xDC, 0xEA, 0x97, 0xF2, 0xCF, 0xCE, 0xF0, 0xB4, 0xE6, 0x73,
    0x96, 0xAC, 0x74, 0x22, 0xE7, 0xAD, 0x35, 0x85, 0xE2, 0xF9, 0x37, 0xE8, 0x1C, 0x75, 0xDF, 0x6E,
    0x47, 0xF1, 0x1A, 0x71, 0x1D, 0x29, 0xC5, 0x89, 0x6F, 0xB7, 0x62, 0x0E, 0xAA, 0x18, 0xBE, 0x1B,
    0xFC, 0x56, 0x3E, 0x4B, 0xC6, 0xD2, 0x79, 0x20, 0x9A, 0xDB, 0xC0, 0xFE, 0x78, 0xCD, 0x5A, 0xF4,
    0x1F, 0xDD, 0xA8, 0x33, 0x88, 0x07, 0xC7, 0x31, 0xB1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xEC, 0x5F,
    0x60, 0x51, 0x7F, 0xA9, 0x19, 0xB5, 0x4A, 0x0D, 0x2D, 0xE5, 0x7A, 0x9F, 0x93, 0xC9, 0x9C, 0xEF,
    0xA0, 0xE0, 0x3B, 0x4D, 0xAE, 0x2A, 0xF5, 0xB0, 0xC8, 0xEB, 0xBB, 0x3C, 0x83, 0x53, 0x99, 0x61,
    0x17, 0x2B, 0x04, 0x7E, 0xBA, 0x77, 0xD6, 0x26, 0xE1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0C, 0x7D
]

H = (1, 6, 11, 12, 5, 10, 15, 0, 9, 14, 3, 4, 13, 2, 7, 8)

# helper
M = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
M_I = [[14, 11, 13, 9], [9, 14, 11, 13], [13, 9, 14, 11], [11, 13, 9, 14]]
p = [0, 1, 2, 3]


class DeoxysBCState(Trail.State):
    """
     A representation of the 4x4 state of DeoxysBCState
     """

    def __init__(self, name, state, filename=None, jsontrail=None):
        Trail.State.__init__(self, name, state, statebitsize=STATE_BIT_SIZE)

    def __repr__(self):
        return """
    {}:
        {}{}{}{}
        {}{}{}{}
        {}{}{}{}
        {}{}{}{}""".strip().format(self.name, *[x for y in self.state for x in y])

    def getActiveOnlyState(self):
        newstate = DeoxysBCState(self.name, getUndefinedState())
        for row in range(STATE_ROW):
            for col in range(STATE_COL):
                if newstate.at(row, col) != [0]:
                    newstate.set(row, col, {i for i in range(1, STATE_SIZE)})


def getUndefinedState():
    return [[{i for i in range(STATE_SIZE)} for _ in range(STATE_COL)] for _ in range(STATE_ROW)]


class DeoxysBCTrail(Trail.Trail):
    def __init__(self, rounds, filename=None, jsontrail=None):
        self.sboxDDT_I = Utils.initDDT(SBOX_I)
        Trail.Trail.__init__(self, rounds, filename, jsontrail, DeoxysBCState, SBOX, statebitsize=STATE_BIT_SIZE,
                             alpha_reflection=False)

    def _addProbability(self):
        self.probabilities = []
        for i in range(1, self.rounds):
            self.probabilities.append(Probability.RoundStepDeoxys(i,
                                                                  self.states["A" + str(i)], self.states["T" + str(i)],
                                                                  self.states["S" + str(i)], self.states["R" + str(i)],
                                                                  self.states["M" + str(i)],
                                                                  self.states["A" + str(i + 1)],
                                                                  self.sboxDDT, M, p))

    def _addPropagation(self):
        for i in range(1, self.rounds + 1):
            self.propagations.append(Propagation.XORStep(self.states["A" + str(i)],
                                                         self.states["S" + str(i)],
                                                         self.states["T" + str(i)]))
            if i < self.rounds:
                self.propagations.append(Propagation.SBOXStep(self.states["S" + str(i)],
                                                              self.states["R" + str(i)], self.sboxDDT, self.sboxDDT_I))

                self.propagations.append(Propagation.ShiftRowsStep(self.states["R" + str(i)],
                                                                   self.states["M" + str(i)], p))

                self.propagations.append(
                    Propagation.MixColStepDeoxys(self.states["M" + str(i)], self.states["A" + str(i + 1)], M, M_I))

        # tweakey update
        # TODO: add tweakeyschedule

    def initUI(self, parentui):
        # tweak
        # TODO: update for TweakeySchedule
        col = 0
        row = 0
        for i in range(1, self.rounds + 1):
            UI.StateUI(parentui, row, col, self.states["T" + str(i)], gridopts={"columnspan": 3})
            col += 5

        # rounds
        col = 0
        row += 1
        for i in range(1, self.rounds + 1):
            if i is self.rounds:
                UI.StateUI(parentui, row, col, self.states["A" + str(i)])
                col += 2
                UI.StateUI(parentui, row, col, self.states["S" + str(i)])
                col += 1
            else:
                UI.StateUI(parentui, row, col, self.states["A" + str(i)])
                col += 2
                UI.StateUI(parentui, row, col, self.states["S" + str(i)])
                col += 1
                UI.StateUI(parentui, row, col, self.states["R" + str(i)])
                col += 1
                UI.StateUI(parentui, row, col, self.states["M" + str(i)])
                col += 1

        parentui.maxgridcol = col - 1

        col = 2
        row += 1
        for i in range(1, self.rounds + 1):
            # sbox
            v = StringVar()
            l = Label(parentui.trailframe, textvariable=v)
            l.textvar = v
            l.grid(fill=None, row=row, column=col, columnspan=2)
            parentui.probabilitylabels["S" + str(i)] = l

            col += 2

            # mixcol
            v = StringVar()
            l = Label(parentui.trailframe, textvariable=v)
            l.textvar = v
            l.grid(fill=None, row=row, column=col, columnspan=2)
            parentui.probabilitylabels["M" + str(i)] = l
            col += 3

    def getProbability(self, verbose=False):
        totalprob = 1.0

        # reset other stateprobs to 0, since they get recursivly calculated
        for state in self.states.values():
            state.stateprobs = [[0.0] * 2 ** (self.statebitsize / self.statesize) for _ in range(self.statesize)]

        # normalize AddState
        first_addstate = self.states["A1"]
        for i in range(self.statesize):
            for poss in first_addstate.atI(i):
                first_addstate.stateprobs[i][poss] = 1.0 / len(first_addstate.atI(i))

        # perform all prob calcs
        for prob in self.probabilities:
            totalprob *= prob.getProbability(verbose=verbose)[0]

        inputposs = 1
        outputposs = 1
        for i in range(STATE_SIZE):
            inputposs *= len(self.states["A1"].atI(i))
            outputposs *= len(self.states["A" + str(self.rounds)].atI(i))

        print "inputposs : 2**{}".format(math.log(inputposs, 2))
        print "outputposs: 2**{}".format(math.log(outputposs, 2))
        N = 2.0 / (totalprob * inputposs)
        N_phi = 2 ** (-64) * outputposs / totalprob
        if verbose:
            print "Overall Probability: 2**{}".format(math.log(totalprob, 2))
            print "N                  : 2**{}".format(math.log(N, 2))
            print "N_phi              : 2**{}".format(math.log(N_phi, 2))
        return totalprob

    # TODO adapt and make dynamic
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
        \newcommand{\SR}{\textsf{R}}
        \newcommand{\MC}{\textsf{M}}
        \newcommand{\AC}{\textsf{+}}
    
        \begin{document}
        \pagestyle{empty}
    
        \begin{figure}[p]
        \centering
        """)
        hi = r"\hi"  # tweaks
        lo = r"\lo"  # states
        mid = "  0"  # labels
        tin = "I"  # r"{\text{in}}"
        tout = "O"  # r"{\text{out}}"
        x = 0
        stepnext = 7
        stepxor = 3.5
        numrounds = self.rounds
        rnds = range(1, numrounds)
        rows = range(4)
        cols = range(4)
        dirs = ['in', 'out']

        output.append(
            r"\caption{" + "Deoxys-BC-{R}: $2^{{{P:.2f}}}$ probability".format(R=numrounds,
                                                                               P=math.log(
                                                                                   self.getProbability(), 2)) + r"}")

        #     r"\caption{" + "Deoxys-BC-{R}: {S} active S-boxes, $2^{{{P:.2f}}}$ probability".format(R=numrounds,
        #                                                                                            S=sum([1 if
        #                                                                                                   self.states[
        #                                                                                                       "S" + str(
        #                                                                                                           s)].atI(
        #                                                                                                       i) != [
        #                                                                                                       0] else 0
        #                                                                                                   for i
        #                                                                                                   in
        #                                                                                                   range(
        #                                                                                                       16)
        #                                                                                                   for s
        #                                                                                                   in
        #                                                                                                   range(
        #                                                                                                       self.rounds + 1) + range(
        #                                                                                                       self.rounds + 2,
        #                                                                                                       self.rounds * 2 + 3)]),
        #                                                                                            P=math.log(
        #                                                                                                self.getProbability(),
        #                                                                                                2)) + r"}")
        # output.append(r"\vspace{1cm}")

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

        # outer rounds
        for rnd in rnds:
            prob = self.probabilities[rnd - 1]
            overallprob, sboxprob, mixcolprob = prob.getProbability()
            # TODO fix label
            # output.append(labelprob(x + 1 * stepxor + 1.5 * stepnext, r"1.1 * " + lo, "$2^{" + \
            #                        "{0:.2f}".format(math.log(overallprob, 2)) + "}$"))

            r = str(rnd)
            output.append(label(x, x + 2 * stepxor + 3 * stepnext, "Round " + r))

            # Add
            output.append(state2sbs(x, mid, "Xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("A", "in", rnd)))
            x += stepxor
            output.append(state2sbs(x, hi, "th" + r, "$t_{" + r + "}\qquad$", getstate("T", None, rnd)))
            if rnd > 1:
                output.append(nextstate("th" + str(rnd - 1).replace("-", "_"), "th" + r, "tweakey schedule"))
            x += stepxor
            # XOR
            output.append(xor(x - stepxor, mid, "ai" + r))

            # Sbox
            output.append(state2sbs(x, mid, "xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("S", "in", rnd)))
            x += stepnext

            # Shift Row
            output.append(state2sbs(x, mid, "yi" + r, "$y^" + tin + "_{" + r + "}$", getstate("R", "in", rnd)))
            x += stepnext

            # Mix Columns
            output.append(state2sbs(x, mid, "mi" + r, "", getstate("M", "in", rnd)))

            output.append(
                r"  \draw[next] (mi" + r + r"_east) -- node[above,font=\scriptsize] {\MC} ++(" + str(int(stepnext/2)) + ",0);")
            output.append(nextstate("Xi" + r, "ai" + r) + " " + nextstate("ai" + r, "xi" + r) + " " +
                          linkstate("th" + r + "_south", "ai" + r + "_north"))
            output.append(nextstate("xi" + r, "yi" + r, "\SB"))
            output.append(nextstate("yi" + r, "mi" + r, "\SR"))

            x += stepnext

        # finalization
        r = str(self.rounds)
        output.append(label(x, x + stepnext, "Final"))

        # Add
        output.append(state2sbs(x, mid, "Xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("A", "in", self.rounds)))
        x += stepxor
        output.append(state2sbs(x, hi, "th" + r, "$t_{" + r + "}\qquad$", getstate("T", None, self.rounds)))
        output.append(nextstate("th" + str(self.rounds - 1).replace("-", "_"), "th" + r, "tweakey schedule"))
        x += stepxor
        # XOR
        output.append(xor(x - stepxor, mid, "ai" + r))
        output.append(state2sbs(x, mid, "xi" + r, "$x^" + tin + "_{" + r + "}$", getstate("S", "in", self.rounds)))
        output.append(nextstate("Xi" + r, "ai" + r) + " " + nextstate("ai" + r, "xi" + r) + " " +
                      linkstate("th" + r + "_south", "ai" + r + "_north"))

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
