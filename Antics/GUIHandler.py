import tkinter
import os
from Game import *
from GameState import *
from GamePane import *
from SettingsPane import *
from StatsPane import *
from Constants import *
import RedoneWidgets
import base64
import pickle
import datetime


#########################################################
# Class GUIHandler
#
# This class is to be instantiated by the game engine
# whenever the ReAntics GUI is needed. This class will
# handle all interactions with GUI threads and methods
# and needed callbacks to the game engine.
#
# The goal of this class is to keep the UI as separate as
# possible from the game engine so that the game can be
# easily configured to run without a GUI if desired.
#
# This could be accomplished by replacing all referenced to
# UI in the main thread with if self.ui is not None: {do thing}.
#########################################################
class GUIHandler:

    def __init__(self, game):
        self.game = game

        # bookKeeping
        self.currentFrame = 0
        self.currentState = None
        self.setup = False
        self.waitingForHuman = False
        self.waitingForAttack = False
        self.attackingAntLoc = None
        self.phase = None

        # set up tkinter things
        self.root = tkinter.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.onClose)
        self.root.title("ReAntics")
        icon = tkinter.PhotoImage(file="Textures/queenRed.gif")
        self.root.tk.call('wm', 'iconphoto', self.root._w, icon)

        self.baseFrame = tkinter.Frame(self.root)
        self.settingsFrame = tkinter.Frame(self.baseFrame)
        self.statsFrame = tkinter.Frame(self.baseFrame)
        self.gameFrame = tkinter.Frame(self.baseFrame)

        # shared tkinter variables
        # note these have to be here after root is made
        self.pauseVar = tkinter.StringVar()
        self.pauseVar.set("Pause")
        self.statsText = tkinter.StringVar()
        self.statsText.set("Print Stats On")
        self.blue = "#8bbcda"
        self.stats = False
        self.paused = False

        self.settingsFrame.pack_propagate(False)
        self.statsFrame.pack_propagate(False)
        self.gameFrame.pack_propagate(False)

        self.settingsHandler = GameSettingsFrame(self, self.settingsFrame)
        self.statsHandler = StatsPane(self, self.statsFrame)
        self.gameHandler = GamePane(self, self.gameFrame)

        menubar = tkinter.Menu(self.root)

        filemenu = tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Reload Agents", command=self.reloadAgentPressed)
        menubar.add_cascade(label="File", menu=filemenu)

        # helpmenu = tkinter.Menu(menubar, tearoff=0)
        # helpmenu.add_command(label="About", command=self.menuPressed)
        # menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)

        # hot keys
        self.root.bind("<Return>", self.gameHandler.endTurnPressed)
        self.root.bind("<space>", self.stepPressed)
        self.root.bind("<p>", self.pausePressed)
        self.root.bind("<Shift-N>", self.secretPressed)
        self.root.bind("<r>", self.regGPressed)
        self.root.bind("<Shift-C>", self.secret2Pressed)
        self.root.bind("<s>", self.setSeasonalGraphics)

        # we want the game to start on the settings screen, so show it first
        self.settingsFrame.pack(fill="both")

        # pack main GUI
        self.baseFrame.pack(fill="both")

        self.count = 0
        self.closed = False
        # self.pausePressed()
        self.setup = True

    # def menuPressed(self):
    #     print("Omg a menu button was pressed!")

    def reloadAgentPressed(self):
        if self.currentFrame == 0:
            self.game.loadAIs()
            self.game.UI.settingsHandler.changePlayers([ai[0].author for ai in self.game.players])
            self.game.UI.settingsHandler.addGameChanged("QuickStart")
            self.game.UI.settingsHandler.addGameType.set("QuickStart")

    def secretPressed(self, event=None):
        with open("Textures/secret1.sec", "rb") as f:
            string_d = pickle.load(f)
            self.gameHandler.textures["queenRed"] = tkinter.PhotoImage(data=string_d)
        self.reDrawBoard()

    def regGPressed(self, event = None):
        resets = ["queenRed", "queenBlue", "food", "grass", "carrying"]
        for r in resets:
            self.gameHandler.textures[r] = tkinter.PhotoImage(file="Textures/"+r+".gif")
        self.reDrawBoard()

    def secret2Pressed(self, event = None):
        files = ["a","b","c"]
        for f in files:
            f1 = "Textures/secret2"+f+".sec"
            with open(f1, "rb") as fi:
                string_d = pickle.load(fi)
                if f == "a":
                    self.gameHandler.textures["queenRed"] = tkinter.PhotoImage(data=string_d)
                elif f == "b":
                    self.gameHandler.textures["queenBlue"] = tkinter.PhotoImage(data=string_d)
                elif f == "c":
                    self.gameHandler.textures["food"] = tkinter.PhotoImage(data=string_d)
        self.reDrawBoard()

    def setSeasonalGraphics(self, event = None) :
        now = datetime.datetime.now()
        if now.month == 3:
            self.secret3enabled()

    def secret3enabled(self):
        files = ["a","b","c","d_x24_y6"] # still need to do the last part
        for f in files:
            f1 = "Textures/secret3"+f+".sec"
            with open(f1, "rb") as fi:
                string_d = pickle.load(fi)
                if f == "a":
                    self.gameHandler.textures["grass"] = tkinter.PhotoImage(data=string_d)
                elif f == "b":
                    self.gameHandler.textures["food"] = tkinter.PhotoImage(data=string_d)
                elif f == "c":
                    self.gameHandler.textures["carrying"] = tkinter.PhotoImage(data=string_d)
        self.reDrawBoard()

        

            
    ##
    # is called when the program is closed
    # to clean up
    #
    def onClose(self):
        self.game.endClient()
        self.root.after(100, self.continueClose)
        #self.continueClose()

    def continueClose(self):
        if self.game.gameThread.is_alive():
            self.root.after(50, self.continueClose)
            return
        self.game.gameThread.join()
        self.root.destroy()

    ##
    # reDrawBoard
    #
    # Calls the reDraw() method on all the tiles on the board
    #
    ##
    def reDrawBoard(self):
        for x in range(10):
            for y in range(10):
                self.gameHandler.boardIcons[x][y].reDraw()


    ##
    # showFrame
    #
    # The GUI handler never destroys the windows in order to
    # be memory and CPU efficient. This method shows whichever
    # frame needs to be present and hides the others.
    #
    #   @param frameNum - integer representing which frame to show
    #       0: settings frame
    #       1: stats frame
    #       2: game frame
    ##
    def showFrame(self, frameNum):
        if frameNum not in [0, 1, 2]:
            return

        if frameNum == self.currentFrame:
            return

        self.currentFrame = frameNum

        self.settingsFrame.pack_forget()
        self.statsFrame.pack_forget()
        self.gameFrame.pack_forget()

        if frameNum == 0:
            self.settingsFrame.pack(fill="both")
        elif frameNum == 1:
            self.statsFrame.pack(fill="both")
        else:
            self.gameFrame.pack(fill="both")
            if self.currentState is not None:
                self.gameHandler.setToGameState(self.currentState)
                if self.waitingForHuman and self.phase in [SETUP_PHASE_1, SETUP_PHASE_2]:
                    self.gameHandler.showSetupConstructions(self.phase)

    ##
    # showState
    #
    # updates the current gameState of the GUI and updates the
    # GUI itself if appropriate to do so
    #
    def showState(self, state):
        self.currentState = state

        if self.currentFrame == 2 and self.currentState is not None:
            self.gameHandler.setToGameState(state)

    ##
    # setPlayers
    #
    # sets the name of the current players
    #
    def setPlayers(self, p1, p2):
        self.gameHandler.p1Name.set(p1[0:6] + '..' + p1[-3:] if len(p1) > 11 else p1)
        self.gameHandler.p2Name.set(p2[0:6] + '..' + p2[-3:] if len(p2) > 11 else p2)

        self.enableAllButtons()
        if p1 == "Human" or p2 == "Human":
            self.disableHumanButtons()
        else:
            self.gameHandler.undoButton.disable()

    def enableAllButtons(self):
        self.gameHandler.UIbutton.enable()
        self.gameHandler.stepButton.enable()

        self.gameHandler.killButton.enable()
        self.gameHandler.restartButton.enable()
        self.gameHandler.settingsButton.enable()

        self.statsHandler.killButton.enable()
        self.statsHandler.restartButton.enable()
        self.statsHandler.settingsButton.enable()

    def disableHumanButtons(self):
        self.gameHandler.UIbutton.disable()
        self.gameHandler.stepButton.disable()

    ##
    # getHumanMove
    #
    # sets up GUI to receive a game move from a human player
    #
    def getHumanMove(self, phase):
        if phase not in [SETUP_PHASE_1, SETUP_PHASE_2, PLAY_PHASE]:
            print("Game in wrong phase for human move")
            return

        # disable undo button at beginning of setup moves
        if phase == SETUP_PHASE_1:
            self.gameHandler.undoButton.disable()
            self.gameHandler.setInstructionText("Select where to build your anthill.")
        elif phase == SETUP_PHASE_2:
            self.gameHandler.undoButton.disable()
            self.gameHandler.setInstructionText("Select where to place your enemy's food. 2 remaining.")
        else:
            # enable undo if there are states to undo to
            if len(self.game.undoStates) > 0:
                self.gameHandler.undoButton.enable()
            else:
                self.gameHandler.undoButton.disable()
            self.gameHandler.setInstructionText("Submit a move.")

        self.waitingForHuman = True
        self.phase = phase

    ##
    # getHumanAttack
    #
    # sets up the GUI to receive an attack from a human player
    # the location passed from the game is already swapped back to P1 at top
    #
    def getHumanAttack(self, location):
        # disable undo during attacks
        self.gameHandler.undoButton.disable()
        self.gameHandler.setInstructionText("Select an ant to attack.")
        self.waitingForHuman = True
        self.waitingForAttack = True
        self.attackingAntLoc = location
        self.gameHandler.highlightValidAttacks(getAntAt(self.currentState, location))

    ##
    # submitHumanSetup
    #
    #
    #
    def submitHumanSetup(self, locations):
        self.gameHandler.setInstructionText("")
        self.game.submitHumanSetup(locations)
        self.waitingForHuman = False

    ##
    # submitHumanMove
    #
    # sends a given move to the game however it needs to go
    #
    def submitHumanMove(self, move):
        self.gameHandler.undoButton.disable()
        self.gameHandler.setInstructionText("")
        self.game.submitHumanMove(move)
        self.waitingForHuman = False

    ##
    # submitHumanAttack
    #
    #
    def submitHumanAttack(self, attack):
        self.gameHandler.setInstructionText("")
        self.game.submitHumanAttack(attack)
        self.waitingForAttack = False
        self.waitingForHuman = False
        self.attackingAntLoc = None

    ##################################################
    # Button Call Methods
    #
    # here because they need to be synced between stats
    # and game pane
    #
    def pausePressed(self, event=None):
        if self.paused:
            self.paused = False
            self.pauseVar.set("Pause")
            self.gameHandler.pauseButton.config(bg = self.blue)
            self.statsHandler.pauseButton.config(bg = self.blue)
            self.statsHandler.startCurLogItem()
            self.statsHandler.timeLabel.Start()
            # should only wake if the game is "paused" on an AI turn
            if self.game.waitingOnAI:
                self.game.generalWake()
        else:
            self.paused = True
            self.pauseVar.set("Play")
            self.gameHandler.pauseButton.config(bg = 'green')
            self.statsHandler.pauseButton.config(bg = 'green')
            self.statsHandler.stopCurLogItem()
            self.statsHandler.timeLabel.Stop()

    def stepPressed(self, event=None):
        # should only wake if the game is "paused" on an AI turn
        if self.game.waitingOnAI:
            self.game.generalWake()

    def statsPressed(self):
        if self.stats:
            self.stats = False
            self.statsText.set("Print Stats On")
            self.game.verbose = True
        else:
            self.stats = True
            self.statsText.set("Print Stats Off")
            self.game.verbose = False

    def killPressed(self):
        # only kill if there's something to kill and game is not already killed
        if not self.game.running or self.game.killed:
            return

        # pause the game during the resolution of the kill button
        pause = False
        if not self.paused:
            self.pausePressed()
            pause = True

        res = RedoneWidgets.askQuestion("Kill Game", "Do you want to kill the game immediately?\n"
                                                     "Note that ending running games may damage AIs.", self.root)

        if res == "yes":
            self.gameHandler.killButton.disable()
            self.statsHandler.killButton.disable()

            self.game.kill()
            self.gameHandler.setInstructionText("Game Killed")
            if self.paused:
                self.pausePressed()

        # unpause the game if we paused it
        if self.paused and pause:
            self.pausePressed()

    def restartPressed(self):
        if self.game.restarted:
            return

        # pause the game during the resolution of the restart button
        pause = False
        if not self.paused and self.game.running:
            self.pausePressed()
            pause = True

        if self.game.running:
            self.game.restart()
            self.killPressed()
        else:
            self.game.restartFromEnd()

        self.gameHandler.restartButton.disable()
        self.statsHandler.restartButton.disable()

        # unpause the game if we paused it
        if pause and self.paused:
            self.pausePressed()

    def settingsPressed(self):
        self.game.gamesToPlay = []
        self.game.goToSettings = True
        self.killPressed()

        if not self.game.gameThread.is_alive():
            self.game.gameThread = threading.Thread(target=self.game.start, daemon=True)
            self.game.gameThread.start()
            self.showFrame(0)

        self.gameHandler.settingsButton.disable()
        self.statsHandler.settingsButton.disable()

        # needs to be reset so that it does not restart when cleared
        self.game.autorestart = False 

        # only wake the game thread if it's not running games ATM
        if not self.game.running:
            self.game.generalWake()
