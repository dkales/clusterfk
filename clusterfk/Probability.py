import Utils

import itertools
import math
import operator

def prod(factors):
    return reduce(operator.mul, factors, 1)

class ProbabilityStep:
    def __init__(self):
        pass

    def getProbability(self,verbose=False):
        raise NotImplementedError("Subclasses need to implement this")

    def AddTweakeyProbability(self, statesize, instate, outstate, tweak):
        # TODO: add Qarma-LFSR in any way?
        for i in range(statesize):
            assert len(tweak.atI(i)) == 1
            t = Utils.first(tweak.atI(i))
            if t != {0}:
                outstate.stateprobs[i] = [instate.stateprobs[i][x ^ t] for x in
                                                range(statesize)]
            else:
                outstate.stateprobs[i] = [instate.stateprobs[i][x] for x in range(statesize)]

    def PermuteProbs(self, statesize, instate, outstate, P):
        for i in range(statesize):
            outstate.stateprobs[i] = instate.stateprobs[P[i]]

    def NormalizeStateProbs(self, statesize, state):
        for i in range(statesize):
            state.stateprobs[i] = [float(x)/sum(state.stateprobs[i]) for x in state.stateprobs[i]]

    def SBOXProbability(self, statesize, instate, outstate, ddt):
        overall_prob = 1.0

        for i in range(statesize):
            sboxprob = 0.0
            for x in instate.atI(i):
                sboxprob += float(sum([ddt[x][y] for y in outstate.atI(i)])) / sum(ddt[x])
                for y in outstate.atI(i):
                    outstate.stateprobs[i][y] += instate.stateprobs[i][x] * float(ddt[x][y]) / sum(ddt[x])
            #sboxprob /= len(self.instate.atI(i))
            overall_prob *= sboxprob

            outstate.stateprobs[i] = [float(x) / sum(outstate.stateprobs[i]) for x in
                                           outstate.stateprobs[i]]

        #print instate.name, overall_prob, math.log(overall_prob, 2)
        return overall_prob

    def SBOXProbabilityForColumnProbs(self, instate, outstate, ddt):
        overall_prob = 1.0

        for column, probs in instate.columnprobs.items():
            sboxprob = 0.0
            for values, prob in probs.items():
                part = prob
                for idx,x in enumerate(values):
                    j = column[idx]
                    part *= float(sum([ddt[x][y] for y in outstate.atI(j)])) / sum(ddt[x]) # guenstige/moegliche
                    for y in outstate.atI(j):
                        outstate.stateprobs[j][y] += prob * float(ddt[x][y]) / sum(ddt[x])
                sboxprob += part

            # if verbose:
                # print "SBOX", column, math.log(sboxprob,2)
            overall_prob *= sboxprob
        return overall_prob

    def MixColProbability(self, staterow, statecol, instate, outstate, M = None):
        overall_prob = 1.0

        outstate.columnprobs = {}
        for col in range(statecol):
            # print "-"*40
            incol = [instate.at(row, col) for row in range(staterow)]
            outset = set()
            colprob = 0.0
            colprob_all = 0.0

            outstate.columnprobs[(0 + col, 4 + col, 8 + col, 12 + col)] = {}
            for a, b, c, d in itertools.product(outstate.at(0, col), outstate.at(1, col),
                                                outstate.at(2, col), outstate.at(3, col)):
                outset.add((a, b, c, d))
            for a, b, c, d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                prob = instate.stateprobs[0 + col][a] * instate.stateprobs[4 + col][b] * \
                       instate.stateprobs[8 + col][c] * instate.stateprobs[12 + col][d]
                if M is None:
                    result = (b ^ c ^ d, a ^ c ^ d, a ^ b ^ d, a ^ b ^ c)
                else:
                    result = (Utils.rotl(b, M[0][1]) ^ Utils.rotl(c, M[0][2]) ^ Utils.rotl(d, M[0][3]),
                          Utils.rotl(a, M[1][0]) ^ Utils.rotl(c, M[1][2]) ^ Utils.rotl(d, M[1][3]),
                          Utils.rotl(a, M[2][0]) ^ Utils.rotl(b, M[2][1]) ^ Utils.rotl(d, M[2][3]),
                          Utils.rotl(a, M[3][0]) ^ Utils.rotl(b, M[3][1]) ^ Utils.rotl(c, M[3][2]))

                if result in outset:
                    colprob += prob
                    outstate.columnprobs[(0 + col, 4 + col, 8 + col, 12 + col)][result] = prob
                colprob_all += prob

            # print col, colprob, colprob_all
            overall_prob *= colprob

        # temporary hack for inner rounds, assume uniform distribution in inner step
        # for i in range(16):
        #    self.mixcolstateout.stateprobs[i] = [
        #        1.0 / len(self.mixcolstateout.atI(i)) if x in self.mixcolstateout.atI(i) else 0.0 for x in range(16)]

        # correct way
        for col, probs in outstate.columnprobs.items():
            total = sum(probs.values())
            for val, prob in probs.items():
                probs[val] = prob / total

            for val, prob in probs.items():
                outstate.stateprobs[col[0]][val[0]] += prob
                outstate.stateprobs[col[1]][val[1]] += prob
                outstate.stateprobs[col[2]][val[2]] += prob
                outstate.stateprobs[col[3]][val[3]] += prob

        return overall_prob


class FullroundStepMantis(ProbabilityStep):
    def __init__(self, round, staterow, statecol, sboxstate, addstate, tweak, permstate, mixcolstate, sboxstate2, sboxDDT, P):
        self.round = round
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.ddt = sboxDDT
        self.P = P

    def getProbability(self,verbose=False):

        overall_prob = 1.0

        # sbox step
        sboxprob = self.SBOXProbabilityForColumnProbs(self.sboxstate, self.addstate, self.ddt)

        # normalize addstate
        self.NormalizeStateProbs(self.statesize, self.addstate)

        # calculate perm-state probs
        self.AddTweakeyProbability(self.statesize, self.addstate, self.permstate, self.tweak)

        # permute state probs - calculate mixcol probs
        self.PermuteProbs(self.statesize, self.permstate, self.mixcolstate, self.P)

        # mixcol step
        mixcolprob = self.MixColProbability(self.staterow, self.statecol, self.mixcolstate, self.sboxstate2)

        # normalize sboxstate2
        self.NormalizeStateProbs(self.statesize, self.sboxstate2)

        overall_prob = sboxprob * mixcolprob
        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)


class InnerRoundStepMantis(ProbabilityStep):
    def __init__(self, staterow, statecol, sboxstatein, mixcolstatein, mixcolstateout, sboxstateout, sboxDDT):
        self.statesize = staterow * statecol
        self.staterow = staterow
        self.statecol = statecol
        self.sboxstatein = sboxstatein
        self.sboxstateout = sboxstateout
        self.mixcolstatein = mixcolstatein
        self.mixcolstateout = mixcolstateout
        self.ddt = sboxDDT

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        # sbox forward round:
        overall_prob *= self.SBOXProbability(self.statesize, self.sboxstatein, self.mixcolstatein, self.ddt)

        # mixcol Step
        for col in range(4):
            columnin = [set(self.sboxstatein.at(row, col)) for row in range(self.staterow)]
            columnout = [set(self.sboxstateout.at(row, col)) for row in range(self.staterow)]
            mcolumnin = [set(self.mixcolstatein.at(row, col)) for row in range(self.staterow)]
            mcolumnout = [set(self.mixcolstateout.at(row, col)) for row in range(self.staterow)]
            if columnin.count(set([0x0])) == 4 and columnout.count(set([0x0])) == 4:
                continue

            if columnin.count(set([0xa])) == 2 and columnin.count(set([0x0])) == 2 and columnout.count(
                    set([0xa])) == 2 and columnout.count(set([0x0])) == 2:
                if mcolumnin.count(set([0xa])) == 2 and mcolumnin.count(set([0x0])) == 2 and mcolumnout.count(
                        set([0xa])) == 2 and mcolumnout.count(set([0x0])) == 2:
                    overall_prob *= 1.0  # overall 2**-8
                    continue
                elif mcolumnin.count(set([0xa, 0x5, 0xd, 0xf])) == 2 and mcolumnin.count(
                        set([0x0])) == 2 and mcolumnout.count(set([0xa, 0x5, 0xd, 0xf])) == 2 and mcolumnout.count(
                        set([0x0])) == 2:
                    overall_prob *= 1.0  # overall 2**-4
                    continue

            raise NotImplementedError("Superbox case not specified")

        # temporary hack for mixcol, assume uniform distribution in inner step
        for i in range(self.statesize):
            self.mixcolstateout.stateprobs[i] = [
                1.0 / len(self.mixcolstateout.atI(i)) if x in self.mixcolstateout.atI(i) else 0.0 for x in
                range(self.statesize)]

        # sbox backward round
        overall_prob *= self.SBOXProbability(self.statesize, self.mixcolstateout, self.sboxstateout, self.ddt)
        if verbose:
            print "I", overall_prob, math.log(overall_prob, 2)

        return (overall_prob, overall_prob, 1)


class FullroundInverseStepMantis(ProbabilityStep):
    def __init__(self, round, staterow, statecol, sboxstate, mixcolstate, permstate, addstate, tweak, sboxstate2, sboxDDT, P):
        self.round = round
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.ddt = sboxDDT
        self.P = P

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        # Mixcol step
        mixcolprob = self.MixColProbability(self.staterow, self.statecol, self.sboxstate, self.mixcolstate)

        # normalize probablities for mixcols
        self.NormalizeStateProbs(self.statesize, self.mixcolstate)

        # propagate to perm with correct permutation of probabilites
        for i in range(self.statesize):
            self.permstate.stateprobs[self.P[i]] = list(self.mixcolstate.stateprobs[i])
        self.permstate.columnprobs = {}
        for col, probs in self.mixcolstate.columnprobs.items():
            self.permstate.columnprobs[(self.P[col[0]], self.P[col[1]], self.P[col[2]], self.P[col[3]])] = probs.copy()

        # AddTweakey Step
        self.AddTweakeyProbability(self.statesize, self.permstate, self.addstate, self.tweak)

        self.addstate.columnprobs = {}
        for col, probs in self.permstate.columnprobs.items():
            self.addstate.columnprobs[col] = {}
            for values, prob in probs.items():
                self.addstate.columnprobs[col][
                    (values[0]^Utils.first(self.tweak.atI(col[0])),
                     values[1]^Utils.first(self.tweak.atI(col[1])),
                     values[2]^Utils.first(self.tweak.atI(col[2])),
                     values[3]^Utils.first(self.tweak.atI(col[3])))] = prob

        #Sbox step
        sboxprob = self.SBOXProbabilityForColumnProbs(self.addstate, self.sboxstate2, self.ddt)

        # normalize sbox2 probs
        self.NormalizeStateProbs(self.statesize, self.sboxstate2)

        overall_prob *= mixcolprob * sboxprob
        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)


class FullroundStepQarma(ProbabilityStep):
    def __init__(self, round, staterow, statecol, sboxstate, addstate, tweak, permstate, mixcolstate, sboxstate2, sboxDDT,
                 P, M):
        self.round = round
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.ddt = sboxDDT
        self.P = P
        self.M = M

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        # Calculate Props for SBOX-step
        sboxprob = self.SBOXProbabilityForColumnProbs(self.sboxstate, self.addstate, self.ddt)

        # normalize addstate
        self.NormalizeStateProbs(self.statesize, self.addstate)

        # calculate perm-state probs
        self.AddTweakeyProbability(self.statesize, self.addstate, self.permstate, self.tweak)

        # permute state probs - calculate mixcol probs
        self.PermuteProbs(self.statesize, self.permstate, self.mixcolstate, self.P)

        # mixcol step
        mixcolprob = self.MixColProbability(self.staterow, self.statecol, self.mixcolstate, self.sboxstate2, self.M)

        # normalize sboxstate2
        self.NormalizeStateProbs(self.statesize, self.sboxstate2)

        overall_prob *= sboxprob * mixcolprob
        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)


class InnerRoundStepQarma(ProbabilityStep):
    def __init__(self, staterow, statecol, sboxstatein, permstatein, mixcolstatein, mixcolstateout, permstateout, sboxstateout, sboxDDT, P, M):
        self.statesize = staterow * statecol
        self.staterow = staterow
        self.statecol = statecol
        self.sboxstatein = sboxstatein
        self.sboxstateout = sboxstateout
        self.permstatein = permstatein
        self.permstateout = permstateout
        self.mixcolstatein = mixcolstatein
        self.mixcolstateout = mixcolstateout
        self.ddt = sboxDDT
        self.P = P
        self.M = M

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        # sbox forward round:
        overall_prob *= self.SBOXProbability(self.statesize, self.sboxstatein, self.permstatein, self.ddt)

        # perm forward round - permute state probs
        self.PermuteProbs(self.statesize, self.permstatein, self.mixcolstatein, self.P)

        # mixcol step
        overall_prob *= self.MixColProbability(self.staterow, self.statecol, self.mixcolstatein, self.mixcolstateout, self.M)

        # perm backward round - permute state probs
        self.PermuteProbs(self.statesize, self.mixcolstateout, self.permstateout, self.P)

        # sbox backward round
        overall_prob *= self.SBOXProbability(self.statesize, self.permstateout, self.sboxstateout, self.ddt)
        if verbose:
            print "I", overall_prob, math.log(overall_prob, 2)

        return (overall_prob, overall_prob, 1)


class FullroundInverseStepQarma(ProbabilityStep):
    def __init__(self, round, staterow, statecol, sboxstate, mixcolstate, permstate, addstate, tweak, sboxstate2, sboxDDT,
                 P, M):
        self.round = round
        self.staterow = staterow
        self.statecol = statecol
        self.statesize = staterow * statecol
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.ddt = sboxDDT
        self.P = P
        self.M = M

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        # Mixcol step
        mixcolprob = self.MixColProbability(self.staterow, self.statecol, self.sboxstate, self.mixcolstate, self.M)

        # normalize probablities for mixcols
        self.NormalizeStateProbs(self.statesize, self.mixcolstate)

        # propagate to perm with correct permutation of probabilites
        for i in range(self.statesize):
            self.permstate.stateprobs[self.P[i]] = list(self.mixcolstate.stateprobs[i])
        self.permstate.columnprobs = {}
        for col, probs in self.mixcolstate.columnprobs.items():
            self.permstate.columnprobs[(self.P[col[0]], self.P[col[1]], self.P[col[2]], self.P[col[3]])] = probs.copy()

        # AddTweakey Step
        self.AddTweakeyProbability(self.statesize, self.permstate, self.addstate, self.tweak)

        self.addstate.columnprobs = {}
        for col, probs in self.permstate.columnprobs.items():
            self.addstate.columnprobs[col] = {}
            for values, prob in probs.items():
                self.addstate.columnprobs[col][(
                values[0] ^ Utils.first(self.tweak.atI(col[0])),
                values[1] ^ Utils.first(self.tweak.atI(col[1])),
                values[2] ^ Utils.first(self.tweak.atI(col[2])),
                values[3] ^ Utils.first(self.tweak.atI(col[3])))] = prob

        # Sbox step
        sboxprob = self.SBOXProbabilityForColumnProbs(self.addstate, self.sboxstate2, self.ddt)

        # normalize sbox2 probs
        self.NormalizeStateProbs(self.statesize, self.sboxstate2)

        overall_prob *= mixcolprob * sboxprob
        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)



