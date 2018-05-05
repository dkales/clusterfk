import Tkinter
import unicodedata
from Tkinter import Tk, Canvas, Frame, Button, Entry, Toplevel, Label, Menu, Checkbutton, BooleanVar
from Tkinter import BOTH, TOP, BOTTOM, LEFT, RIGHT, LAST, FIRST
import tkFileDialog
import math
import json
from json import dumps, loads, JSONEncoder, JSONDecoder
from jsonschema import validate
import yaml

from clusterfk import Utils, DeoxysBC, Mantis, Qarma

try:
    import cPickle as pickle
except Exception:
    import pickle

MARGIN_LR = 10  # Pixels left and right of the board (x)
MARGIN_TB = 12  # Pixels above and below board (y)
SIDE = 12  # Width of every state cell.

# TODO put this elsewhere?
CIPHER_TRAILS = {
    "Mantis": Mantis.MantisTrail,
    "Qarma": Qarma.QarmaTrail,
    "DeoxysBC": DeoxysBC.DeoxysBCTrail
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
        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.b.pack()
        self.l2 = Label(top, text="Probabilities")
        self.l2.pack()
        for i, x in enumerate(state_probs):
            if x > 0:
                l = Label(top, text=hex(i)[2:] + ":" + str(x))
                l.pack()
        self.top.bind("<Return>", lambda x: self.check_cleanup())
        self.top.bind("<Escape>", lambda x: self.close())
        self.value = None
        self.top.wait_visibility()
        self.top.grab_set()
        # stop interaction in other gui

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

        self.close()

    def close(self):
        self.top.grab_release()
        self.top.destroy()


class StateUI(Frame):
    def __init__(self, trailui, row, col, state, scale=1, gridopts={}):
        self.state = state
        self._row = row
        self._col = col
        self._parent = trailui.trailframe
        self._trailui = trailui
        self._scale = scale

        self.__setScaling(scale)
        Frame.__init__(self, self._parent)
        self.__initUI(gridopts)
        trailui.states.append(self)

    def __setScaling(self, scale):
        self._dim = {}
        # self.__dim["MARGIN"] = int(MARGIN * scale)
        self._dim["MARGIN_LR"] = int(MARGIN_LR)
        self._dim["MARGIN_TB"] = int(MARGIN_TB)
        self._dim["SIDE"] = int(SIDE * scale)
        self._dim["WIDTH"] = self._dim["SIDE"] * self.state.staterow + self._dim["MARGIN_LR"] * 2
        self._dim["HEIGHT"] = self._dim["SIDE"] * self.state.statecol + self._dim["MARGIN_TB"] * 2

    def __initUI(self, gridopts):
        self.grid(fill=None, row=self._row, column=self._col, **gridopts)
        self.canvas = Canvas(self,
                             width=self._dim["WIDTH"],
                             height=self._dim["HEIGHT"])
        self.canvas.pack(fill=None)

        self.redraw_state()

        # bind keyboard
        # self.canvas.focus_set()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __draw_grid(self):
        """
        Draws grid divided with blue lines into 4x4 squares
        """
        self.canvas.delete("grid")
        for i in xrange(5):
            color = "blue" if i % 4 == 0 else "gray"

            x0 = self._dim["MARGIN_LR"] + i * self._dim["SIDE"]
            y0 = self._dim["MARGIN_TB"]
            x1 = self._dim["MARGIN_LR"] + i * self._dim["SIDE"]
            y1 = self._dim["HEIGHT"] - self._dim["MARGIN_TB"]
            self.canvas.create_line(x0, y0, x1, y1, fill=color, tags="grid")

            x0 = self._dim["MARGIN_LR"]
            y0 = self._dim["MARGIN_TB"] + i * self._dim["SIDE"]
            x1 = self._dim["WIDTH"] - self._dim["MARGIN_LR"]
            y1 = self._dim["MARGIN_TB"] + i * self._dim["SIDE"]
            self.canvas.create_line(x0, y0, x1, y1, fill=color, tags="grid")

    def redraw_state(self):
        self.canvas.delete("state")

        # draw grid
        for i in xrange(self.state.staterow):
            for j in xrange(self.state.statecol):
                val = self.state.at(i, j)

                if val == [0] or val == {0}:
                    color = "white"
                else:
                    color = self._trailui.trail.colorlist[frozenset(val)]

                x = self._dim["MARGIN_LR"] + j * self._dim["SIDE"]
                y = self._dim["MARGIN_TB"] + i * self._dim["SIDE"]
                self.canvas.create_rectangle(x, y, x + self._dim["SIDE"], y + self._dim["SIDE"], fill=color,
                                             tags="state")

                # numbers in state cells for same propagation
                if self.state.statenumbers[i * self.state.staterow + j] != 0:
                    x = self._dim["MARGIN_LR"] + j * self._dim["SIDE"] + self._dim["SIDE"] / 2
                    y = self._dim["MARGIN_TB"] + i * self._dim["SIDE"] + self._dim["SIDE"] / 2
                    self.canvas.create_text(x, y, text=str(self.state.statenumbers[i * self.state.staterow + j]),
                                            tags="state", fill="black")

        # print name
        if "T" in self.state.name:
            if self._trailui.alpha_reflection is True:
                self.canvas.create_text(self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.staterow / 2,
                                        self._dim["MARGIN_TB"] / 2,
                                        text=self.state.name)
            else:
                self.canvas.create_text(self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.staterow / 2,
                                        self._dim["MARGIN_TB"] / 2,
                                        text=self.state.name)
        else:
            self.canvas.create_text(self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.staterow / 2,
                                    self._dim["MARGIN_TB"] / 2,
                                    text=self.state.name)

    def redraw_propagation(self):
        #TODO enhance
        self.canvas.delete("prop")

        if "T" in self.state.name:
            #self.canvas.create_line(
            #    self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.statecol / 2,
            #    self._dim["MARGIN_TB"] + self._dim["SIDE"] * self.state.staterow,
            #    self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.statecol / 2,
            #    self._dim["MARGIN_TB"] * 2 + self._dim["SIDE"] * self.state.staterow,
            #    tags="prop", fill="black")
            pass

        else:
            xl_0 = 0
            xl_1 = self._dim["MARGIN_LR"]
            xr_0 = self._dim["MARGIN_LR"] + self._dim["SIDE"] * self.state.statecol
            xr_1 = self._dim["MARGIN_LR"] * 2 + self._dim["SIDE"] * self.state.statecol
            y = self._dim["MARGIN_TB"] + self._dim["SIDE"] * self.state.staterow / 2

            if (self._trailui.alpha_reflection is True and self.grid_info()[
                "row"] < 3) or self._trailui.alpha_reflection is False:
                if self.grid_info()["row"] < 3:  # Todo remove hardcoded value
                    # arrow to state
                    self.canvas.create_line(xl_0, y, xl_1, y,
                                            tags="prop", fill="black", arrow=LAST)

                    # line out of state
                    self.canvas.create_line(xr_0, y, xr_1, y,
                                            tags="prop", fill="black")
            else:
                # line in state
                self.canvas.create_line(xl_0, y, xl_1, y,
                                        tags="prop", fill="black")

                # arrow out of self
                self.canvas.create_line(xr_0, y, xr_1, y,
                                        tags="prop", fill="black", arrow=FIRST)

    def __key_pressed(self, event):
        print event

    def __cell_clicked(self, event):
        state_col = (event.x - self._dim["MARGIN_LR"]) // self._dim["SIDE"]
        state_row = (event.y - self._dim["MARGIN_TB"]) // self._dim["SIDE"]
        oldstate = self.state.at(state_row, state_col)
        state_probs = self.state.stateprobs[state_row * self.state.statecol + state_col]
        selected_cell = {"stateUI": self, "row": state_row, "col": state_col, "oldstate": oldstate,
                         "state_probs": state_probs}

        if selected_cell in self._trailui.selectedcells:
            # deselect cell if it is already selected
            self.deselect_cell(selected_cell)
            self.remove_cell_from_selectionlist(selected_cell)
        else:
            self.select_cell(selected_cell)

        if self._trailui.multiselection is False:
            self._trailui.open_cell_dialogue()

    def select_cell(self, selected_cell):
        if 0 <= selected_cell["col"] < self.state.statecol and 0 <= selected_cell["row"] < self.state.staterow:
            print "Cell ({},{}) = {}".format(selected_cell["row"], selected_cell["col"], selected_cell["oldstate"])

        x = self._dim["MARGIN_LR"] + selected_cell["col"] * self._dim["SIDE"]
        y = self._dim["MARGIN_TB"] + selected_cell["row"] * self._dim["SIDE"]
        self.canvas.create_rectangle(x, y, x + self._dim["SIDE"], y + self._dim["SIDE"], fill='',
                                     outline="red",
                                     width=2.0, tags="statehighlight" + str(selected_cell["row"]) + "_" + str(
                selected_cell["col"]))

        self._trailui.selectedcells.append(selected_cell)

    def deselect_cell(self, selected_cell):
        self.canvas.delete("statehighlight" + str(selected_cell["row"]) + "_" + str(selected_cell["col"]))

    def remove_cell_from_selectionlist(self, selected_cell):
        self._trailui.selectedcells.remove(selected_cell)


class TrailUI:
    def __init__(self, parent, trail=None, alpha_reflection=True):
        self.parent = parent
        self.trail = trail
        self.alpha_reflection = alpha_reflection
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

        # Multi Cell Selection
        self.multiselection = False
        self.selectedcells = []
        self.parent.bind("<Control_L>", self.__selection_start)
        self.parent.bind("<KeyRelease-Control_L>", self.__selection_end)

    def __selection_start(self, event):
        print "Selection started"
        self.multiselection = True

    def __selection_end(self, event):
        print "Selection ended"
        self.multiselection = False
        self.open_cell_dialogue()

    def open_cell_dialogue(self):
        if len(self.selectedcells) is 0:
            return

        # oldstate = self.__clickedcells[0]["oldstate"]
        # oldstatestr = ",".join(["{:x}".format(x) for x in oldstate])
        oldstatestr = ""

        dialog = StatePopup(self.canvas, oldstatestr,
                            self.selectedcells[0]["state_probs"])  # TODO add probs

        self.trailframe.wait_window(dialog.top)

        newstate = dialog.value
        # set each cell of the selection to the new state
        if newstate is not None:
            for i, cell in enumerate(self.selectedcells):
                cell["stateUI"].state.set(cell["row"], cell["col"], set(newstate))

        self._clear_selection()
        self.redraw_all()

    def _clear_selection(self):
        for i, cell in enumerate(self.selectedcells):
            cell["stateUI"].deselect_cell(cell)

        self.selectedcells = []

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

        for state in self.states:
            state.redraw_propagation()

    def redraw_probablities(self):
        if self.alpha_reflection is True:
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
        else:
            for i, prob in enumerate(self.trail.probabilities):
                overallprob, sboxprob, mixcolprob = prob.getProbability()
                self.probabilitylabels["S" + str(i + 1)].textvar.set("2^{0:.2f}".format(math.log(sboxprob, 2)))
                self.probabilitylabels["M" + str(i + 1)].textvar.set("2^{0:.2f}".format(math.log(mixcolprob, 2)))

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

        # TODO: check against json schema
        # load JSON data as string, not unicode string
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
