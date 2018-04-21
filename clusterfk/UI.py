import Tkinter
import unicodedata
from Tkinter import Tk, Canvas, Frame, Button, Entry, Toplevel, Label, Menu, Checkbutton, BooleanVar
from Tkinter import BOTH, TOP, BOTTOM, LEFT, RIGHT
import tkFileDialog
import math
import json
from json import dumps, loads, JSONEncoder, JSONDecoder
from jsonschema import validate
import yaml

from clusterfk import Utils

try:
    import cPickle as pickle
except Exception:
    import pickle

import Mantis
import Qarma

NUM_STATE_CELLS = (4, 4)  # TODO make dynamic
MARGIN = 4  # Pixels around the board
SIDE = 12  # Width of every state cell.

# TODO put this elsewhere?
CIPHER_TRAILS = {
    "Mantis": Mantis.MantisTrail,
    "Qarma": Qarma.QarmaTrail
}


class StatePopup(object):
    def __init__(self, master, default_value, state_probs):
        top = self.top = Toplevel(master)
        self.l = Label(top, text="New State")
        self.l.pack()
        self.e = Entry(top)
        self.e.insert(0, default_value)
        self.e.bind("<Control-KeyRelease-a>", lambda x: self.select_all())
        self.e.pack()
        self.e.select_range(0, 'end')
        self.e.icursor('end')
        self.e.focus()
        self.b = Button(top, text='Ok', command=self.check_cleanup)
        self.b.pack()
        self.l2 = Label(top, text="Probabilities")
        self.l2.pack()
        for i, x in enumerate(state_probs):
            if x > 0:
                l = Label(top, text=hex(i)[2:] + ":" + str(x))
                l.pack()
        self.top.bind("<Return>", lambda x: self.check_cleanup())
        self.top.bind("<Escape>", lambda x: self.top.destroy())
        self.value = None

    def select_all(event):
        event.e.select_range(0, 'end')
        # move cursor to the end
        event.e.icursor('end')
        return 'break'

    def check_cleanup(self):
        newstate = self.e.get()
        if newstate == "":
            self.value = range(16)
        elif newstate == "*":
            self.value = range(1, 16)
        else:
            try:
                state = []
                for x in newstate.split(","):
                    x = x.strip()
                    assert len(x) == 1
                    state.append(int(x, 16))
                assert len(state) > 0
                self.value = state
            except Exception as e:
                print e
                self.value = None
                return
        self.top.destroy()


class StateUI(Frame):
    def __init__(self, trailui, row, col, state, scale=1, gridopts={}):
        self.state = state
        self.__row = row
        self.__col = col
        self.__parent = trailui.trailframe
        self.__trailui = trailui
        self.__scale = scale

        self.__setScaling(scale)
        Frame.__init__(self, self.__parent)
        self.__initUI(gridopts)
        trailui.states.append(self)

    def __setScaling(self, scale):
        self.__dim = {}
        self.__dim["MARGIN"] = int(MARGIN * scale)
        self.__dim["SIDE"] = int(SIDE * scale)
        self.__dim["WIDTH"] = self.__dim["SIDE"] * 4 + self.__dim["MARGIN"] * 2
        self.__dim["HEIGHT"] = self.__dim["SIDE"] * 4 + self.__dim["MARGIN"] * 2

    def __initUI(self, gridopts):
        self.grid(fill=None, row=self.__row, column=self.__col, **gridopts)
        self.canvas = Canvas(self,
                             width=self.__dim["WIDTH"],
                             height=self.__dim["HEIGHT"])
        self.canvas.pack(fill=None)

        self.redraw_state()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __draw_grid(self):
        """
        Draws grid divided with blue lines into 4x4 squares
        """
        self.canvas.delete("grid")
        for i in xrange(5):
            color = "blue" if i % 4 == 0 else "gray"

            x0 = self.__dim["MARGIN"] + i * self.__dim["SIDE"]
            y0 = self.__dim["MARGIN"]
            x1 = self.__dim["MARGIN"] + i * self.__dim["SIDE"]
            y1 = self.__dim["HEIGHT"] - self.__dim["MARGIN"]
            self.canvas.create_line(x0, y0, x1, y1, fill=color, tags="grid")

            x0 = self.__dim["MARGIN"]
            y0 = self.__dim["MARGIN"] + i * self.__dim["SIDE"]
            x1 = self.__dim["WIDTH"] - self.__dim["MARGIN"]
            y1 = self.__dim["MARGIN"] + i * self.__dim["SIDE"]
            self.canvas.create_line(x0, y0, x1, y1, fill=color, tags="grid")

    def redraw_state(self):
        self.canvas.delete("state")
        # self.__draw_grid()
        for i in xrange(NUM_STATE_CELLS[0]):
            for j in xrange(NUM_STATE_CELLS[1]):
                val = self.state.at(i, j)

                if val == [0] or val == {0}:
                    color = "white"
                else:
                    color = self.__trailui.trail.colorlist[frozenset(val)]

                x = self.__dim["MARGIN"] + j * self.__dim["SIDE"]
                y = self.__dim["MARGIN"] + i * self.__dim["SIDE"]
                self.canvas.create_rectangle(x, y, x + self.__dim["SIDE"], y + self.__dim["SIDE"], fill=color,
                                             tags="state")

                # if len(val) != 1 or val == [0]:
                # textval = ""
                # else:
                # textval = "{:x}".format(val[0])
                if self.state.statenumbers[i * NUM_STATE_CELLS[0] + j] != 0:
                    x = self.__dim["MARGIN"] + j * self.__dim["SIDE"] + self.__dim["SIDE"] / 2
                    y = self.__dim["MARGIN"] + i * self.__dim["SIDE"] + self.__dim["SIDE"] / 2
                    self.canvas.create_text(x, y, text=str(self.state.statenumbers[i * NUM_STATE_CELLS[0] + j]),
                                            tags="state", fill="black")

    def __key_pressed(self, event):
        print event

    def __cell_clicked(self, event):
        state_col = (event.x - self.__dim["MARGIN"]) // self.__dim["SIDE"]
        state_row = (event.y - self.__dim["MARGIN"]) // self.__dim["SIDE"]
        oldstate = self.state.at(state_row, state_col)
        if 0 <= state_col < 4 and 0 <= state_row < 4:
            print "Cell ({},{}) = {}".format(state_row, state_col, oldstate)
        oldstatestr = ",".join(["{:x}".format(x) for x in oldstate])

        x = self.__dim["MARGIN"] + state_col * self.__dim["SIDE"]
        y = self.__dim["MARGIN"] + state_row * self.__dim["SIDE"]
        self.canvas.create_rectangle(x, y, x + self.__dim["SIDE"], y + self.__dim["SIDE"], fill='', outline="red",
                                     width=2.0, tags="statehighlight")
        dialog = StatePopup(self.__parent, oldstatestr, self.state.stateprobs[state_row * 4 + state_col])
        self.__parent.wait_window(dialog.top)
        self.canvas.delete("statehighlight")
        newstate = dialog.value
        if newstate is not None:
            self.state.set(state_row, state_col, set(newstate))
            self.__trailui.redraw_all()


class TrailUI:
    def __init__(self, parent, trail=None):
        self.parent = parent
        self.trail = trail
        self.states = []
        self.probabilitylabels = {}
        self.trailframe = Frame(parent)
        self.trailframe.pack(fill=Tkinter.X, expand=1)
        self.infoframe = Frame(parent)
        self.infoframe.pack(fill=Tkinter.X, expand=1, side=BOTTOM)
        self.canvas = Canvas(self.infoframe, width=1000, height=200)
        self.canvas.pack()
        self.b = Button(self.infoframe, text='Disable Propagation', command=self.__toggle_prop)
        self.b.pack()
        self.b2 = Button(self.infoframe, text='Make active only', command=self.__activeonly)
        self.b2.pack()
        self.parent.title("ClusterF**k")
        self.enable_propagation = True
        self.trail.updateColorList()
        self.trail.initUI(self)

    def __toggle_prop(self):
        self.enable_propagation = not self.enable_propagation
        if self.enable_propagation:
            self.b.config(text="Disable Propagation")
            self.redraw_all()
        else:
            self.b.config(text="Enable Propagation")

    def __activeonly(self):
        self.trail.makeActiveOnly()
        self.redraw_all()

    def redraw_all(self):
        if self.enable_propagation:
            self.trail.propagate()
            self.trail.getProbability(verbose=True)
        self.redrawColorList()
        self.redraw_states()
        if self.enable_propagation:
            self.redraw_probablities()

    def redraw_states(self):
        for state in self.states:
            state.redraw_state()

    def redraw_probablities(self):
        for i, prob in enumerate(self.trail.probabilities):
            overallprob, sboxprob, mixcolprob = prob.getProbability()
            if i < self.trail.rounds:
                self.probabilitylabels["S" + str(i)].textvar.set("2^{0:.2f}".format(math.log(sboxprob, 2)))
                self.probabilitylabels["M" + str(i + 1)].textvar.set("2^{0:.2f}".format(math.log(mixcolprob, 2)))
            elif i >= self.trail.rounds + 1:
                self.probabilitylabels["S" + str(i + 2)].textvar.set("2^{0:.2f}".format(math.log(sboxprob, 2)))
                self.probabilitylabels["M" + str(i + 1)].textvar.set("2^{0:.2f}".format(math.log(mixcolprob, 2)))
            else:  # inner round
                self.probabilitylabels["I"].textvar.set("2^{0:.2f}".format(math.log(overallprob, 2)))

    def redrawColorList(self):
        self.canvas.delete("colorlist")
        self.trail.updateColorList()
        for i, (state, color) in enumerate(self.trail.colorlist.items()):
            statestr = ",".join(["{:x}".format(x) for x in state])
            x = 15 + int(i / 5) * 250
            y = 15 + (i % 5) * 40
            self.canvas.create_rectangle(x, y, x + 25, y + 25, fill=color, tags="colorlist")

            textx = x + 40
            texty = y + 12
            self.canvas.create_text(textx, texty, text=statestr, tags="colorlist", fill="black", anchor="w")

    def cleanup(self):
        self.infoframe.destroy()
        self.trailframe.destroy()


class ClusterFK:
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """

    def __init__(self, rounds, filename, trail):
        self.root = Tk()

        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save Trail", command=self.saveTrail)
        self.filemenu.add_command(label="Load Trail", command=self.loadTrail)
        self.filemenu.add_command(label="Export to Tex", command=self.exportToLatex)
        self.filemenu.add_command(label="Quit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.root.config(menu=self.menubar)
        self.trailUI = None
        if filename.endswith(".cfk"):
            self._loadTrailFromFile(open(filename, "rb"))
        elif filename.endswith(".trail"):
            self._initTrailUI(trail(rounds, filename=filename))
        elif filename.endswith(".json"):
            self._loadTrailFromJson(open(filename, "rb"))
        else:
            print "File extensions not supported. Use .trail, .cfk or .json"
            raise IOError()
        # self.mantis.printTrail()
        self.root.geometry("{:d}x{:d}".format(1920, 1080))
        self.root.mainloop()

    def _initTrailUI(self, trail):

        if self.trailUI is not None:
            self.trailUI.cleanup()
        self.trail = trail
        self.trail.propagate()
        self.trailUI = TrailUI(self.root, self.trail)
        self.trailUI.redraw_all()
        self.trailUI.redrawColorList()

    def saveTrail(self):
        f = tkFileDialog.asksaveasfile(mode="w", defaultextension=".json")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        # pickle.dump(self.trail, f)
        json_trail = self.trail.toJSON()
        validate(json_trail, Utils.json_schema)
        json.dump(json_trail, f, sort_keys=True, indent=2)
        f.close()

    def _loadTrailFromJson(self, f):
        if f is None:
            return

        #load JSON data as string, not unicode string
        imported_trail = _byteify(json.load(f, object_hook=_byteify), ignore_dicts=True)

        f.close()

        trail = CIPHER_TRAILS[imported_trail["cipher"]](imported_trail["rounds"], jsontrail=imported_trail)
        self._initTrailUI(trail)

    def _loadTrailFromFile(self, f):
        # for old exports
        if f is None:
            return
        trail = pickle.load(f)
        self._initTrailUI(trail)
        f.close()

    def loadTrail(self):
        f = tkFileDialog.askopenfile(mode="r", defaultextension=".json")
        if f is None:
            return

        if f.name.endswith(".cfk"):
            self._loadTrailFromFile(f)
        elif f.name.endswith(".json"):
            self._loadTrailFromJson(f)
        else:
            print "File extensions not supported. Use .trail, .cfk or .json"
            raise IOError()

    def exportToLatex(self):
        f = tkFileDialog.asksaveasfile(mode="w", defaultextension=".tex")
        if f is None:
            return

        self.trail.exportToLatex(f)
        f.close()


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data
