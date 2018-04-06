import Mantis
#internal imports
import Utils

# external imports
import itertools
def intersect(cell1, cell2):
    return list(set(cell1) & set(cell2))

def cellsdifferent(cell1, cell2):
    return len(cell1 ^ cell2) is not 0

class PropagationStep:
    def __init__(self, instate, outstate):
        self.instate = instate
        self.outstate = outstate
        self.statesize = instate.statesize
        self.staterow = instate.staterow
        self.statecol = instate.statecol
        self.inchanged = False
        self.outchanged = False

    def propagate(self):
        raise NotImplementedError("Subclasses need to implement this")


class PermutationStep(PropagationStep):
    def __init__(self, instate, outstate, perm):
        PropagationStep.__init__(self, instate, outstate)
        self.perm = perm

    def propagate(self):
        self.inchanged = False
        self.outchanged = False

        for i in range(self.statesize):
            intersection = self.instate.atI(self.perm[i]) & self.outstate.atI(i)
            if len(intersection) == 0:
                print "Error in: ", self.instate.name
                #intersection = {10}
                assert False

            if cellsdifferent(self.instate.atI(self.perm[i]), intersection):
                self.inchanged = True
            if cellsdifferent(self.outstate.atI(i), intersection):
                self.outchanged = True

            self.instate.setI(self.perm[i], intersection)
            self.outstate.setI(i, intersection)


class UpdateTweakeyStepQarma(PropagationStep):
    def __init__(self, instate, outstate, perm, lfsrcomputationmatrix, lfsrlookup):
        PropagationStep.__init__(self, instate, outstate)
        self.perm = perm
        self.lfsrlookup = lfsrlookup
        self.lfsrmatrix = lfsrcomputationmatrix
        self._initLFSRLookupInv(lfsrlookup)

    def _initLFSRLookupInv(self, lookup):
        self.lfsrlookupinv = [lookup.index(x) for x in range(self.statesize)]

    def propagate(self):
        self.inchanged = False
        self.outchanged = False

        for i in range(self.statesize):
            if self.lfsrmatrix[i] is 1:
                instate_i_shifted = set(map(lambda x: self.lfsrlookup[x], list(self.instate.atI(self.perm[i]))))
                intersection = instate_i_shifted & self.outstate.atI(i)
                in_intersection = set(map(lambda x: self.lfsrlookupinv[x], intersection))

                if cellsdifferent(self.instate.atI(self.perm[i]), in_intersection):
                    self.inchanged = True

                self.instate.setI(self.perm[i], in_intersection)
            else:
                intersection = self.instate.atI(self.perm[i]) & self.outstate.atI(i)

                if cellsdifferent(self.instate.atI(self.perm[i]), intersection):
                    self.inchanged = True
                self.instate.setI(self.perm[i], intersection)

            if len(intersection) == 0:
                print "Error in: ", self.instate.name
                assert False

            if cellsdifferent(self.outstate.atI(i), intersection):
                self.outchanged = True
            self.outstate.setI(i, intersection)


class XORStep(PropagationStep):
    def __init__(self, instate, outstate, tweak):
        PropagationStep.__init__(self, instate, outstate)
        self.tweak = tweak

    def propagate(self):
        self.inchanged = False
        self.outchanged = False

        for i in range(self.statesize):
            t = self.tweak.atI(i)
            assert(len(t) == 1)
            t = Utils.first(t)
            in_new = {x^t for x in self.outstate.atI(i)}
            out_new = {x^t for x in self.instate.atI(i)}

            instate_new = self.instate.atI(i) & in_new
            outstate_new = self.outstate.atI(i) & out_new

            if cellsdifferent(self.instate.atI(i), instate_new):
                self.inchanged = True
            if cellsdifferent(self.outstate.atI(i), outstate_new):
                self.outchanged = True

            self.instate.setI(i, instate_new)
            self.outstate.setI(i, outstate_new)

            if len(self.instate.atI(i)) == 0 or len(self.outstate.atI(i)) == 0:
                print "Error in: ", self.instate.name
                assert False


class SBOXStep(PropagationStep):
    def __init__(self, instate, outstate, DDT):
        PropagationStep.__init__(self, instate, outstate)
        self.ddt = DDT

    def _getDDTState(self, state):
        ret = set()
        for x in state:
            ret.update([i for i in range(self.statesize) if self.ddt[x][i] > 0])
        return ret

    def propagate(self):
        self.inchanged = False
        self.outchanged = False

        for i in range(self.statesize):
            outposs = self._getDDTState(self.instate.atI(i))
            inposs = self._getDDTState(self.outstate.atI(i))

            instate_new = self.instate.atI(i) & inposs
            outstate_new = self.outstate.atI(i) & outposs

            if cellsdifferent(self.instate.atI(i), instate_new):
                self.inchanged = True
            if cellsdifferent(self.outstate.atI(i), outstate_new):
                self.outchanged = True

            self.instate.setI(i, instate_new)
            self.outstate.setI(i, outstate_new)

            if len(self.instate.atI(i)) == 0 or len(self.outstate.atI(i)) == 0:
                print "Error in: ", self.instate.name
                #self.instate.setI(i, {0})
                #self.outstate.setI(i, {0})
                assert False


class MixColStep(PropagationStep):
    def __init__(self, instate, outstate, M = None):
        PropagationStep.__init__(self, instate, outstate)
        self.M = M

    def propagate(self):
        global cellcounter
        self.inchanged = False
        self.outchanged = False

        for col in range(self.statecol):
            incol = [self.instate.at(row, col) for row in range(self.staterow)]
            outcol = [self.outstate.at(row, col) for row in range(self.staterow)]

            # skip undefined blocks for now, will probably be resolved on their own
            if incol.count({0}) + outcol.count({0}) == 8:
                continue

            else:
                #print "WARNING MC not 4, but", 8-(incol.count([0]) + outcol.count([0])),": "+ self.instate.name + "," + self.outstate.name
               
                incol_old = set()
                outcol_old = set()
                incol_new = set()
                outcol_new = set()

                for a, b, c, d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                    incol_old.add((a,b,c,d))
                    if self.M is None:
                        outcol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))
                    else:
                        outcol_new.add(
                            (Utils.rotl(b, self.M[0][1]) ^ Utils.rotl(c, self.M[0][2]) ^ Utils.rotl(d, self.M[0][3]),
                             Utils.rotl(a, self.M[1][0]) ^ Utils.rotl(c, self.M[1][2]) ^ Utils.rotl(d, self.M[1][3]),
                             Utils.rotl(a, self.M[2][0]) ^ Utils.rotl(b, self.M[2][1]) ^ Utils.rotl(d, self.M[2][3]),
                             Utils.rotl(a, self.M[3][0]) ^ Utils.rotl(b, self.M[3][1]) ^ Utils.rotl(c, self.M[3][2])))

                for a, b, c, d in itertools.product(outcol[0], outcol[1], outcol[2], outcol[3]):
                    outcol_old.add((a,b,c,d))
                    if self.M is None:
                        incol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))
                    else:
                        incol_new.add(
                            (Utils.rotl(b, self.M[0][1]) ^ Utils.rotl(c, self.M[0][2]) ^ Utils.rotl(d, self.M[0][3]),
                             Utils.rotl(a, self.M[1][0]) ^ Utils.rotl(c, self.M[1][2]) ^ Utils.rotl(d, self.M[1][3]),
                             Utils.rotl(a, self.M[2][0]) ^ Utils.rotl(b, self.M[2][1]) ^ Utils.rotl(d, self.M[2][3]),
                             Utils.rotl(a, self.M[3][0]) ^ Utils.rotl(b, self.M[3][1]) ^ Utils.rotl(c, self.M[3][2])))

                newinstate = incol_old & incol_new
                newoutstate = outcol_old & outcol_new
                for row in range(self.staterow):
                    ni = set()
                    no = set()
                    for x in newinstate:
                        ni.add(x[row])
                    for x in newoutstate:
                        no.add(x[row])

                    if cellsdifferent(self.instate.at(row, col), ni):
                        self.inchanged = True
                    if cellsdifferent(self.outstate.at(row, col), no):
                        self.outchanged = True

                    self.instate.set(row, col, ni)
                    self.outstate.set(row, col, no)

                    if len(self.instate.at(row, col)) == 0 or len(self.outstate.at(row, col)) == 0:
                        print "Error in: ", self.instate.name
                        assert False