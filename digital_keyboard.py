import time
import sys

from random import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QBrush, QPalette, QKeySequence
from mingus.core import progressions, intervals
from mingus.core import chords as ch
from mingus.containers import NoteContainer, Note
from mingus.midi import fluidsynth
from pygame import key

import constants
from sound import Sound
from db import db

# TODO:
'''
remove global keywords and add to classes
remove needless returns


Features:
allow users to change soundfont/synth
'''

# TODO: remove this and add to classes
# mapping_notes = []

class PianoKeyItem(QGraphicsRectItem):
    def mousePressEvent(self, event):
        if hasattr(self, 'note') and self.note is not None:
            mapping_notes = self.instrument_widget.digital_keyboard.mapping_notes
            if not self.note in mapping_notes:
                mapping_notes.append(self.note)
            else:
                mapping_notes.remove(self.note)
            self.instrument_widget.updateUI()


class DigitalKeyboard(object):
    def __init__(self):
        # self.DigitalInstrumentWidget = DigitalInstrumentWidget()
        self.sound = Sound()
        self.mapping_db = db()
        self.initKeyboard()

        self.octave = 1;
        self.noteDict = constants.keyboard_types[constants.selected_keyboard]
        self.pedal_pressed = False
        self.play_over = False
        self.mapping_notes = []

    def initKeyboard(self):
        # Contains override keys that will be hit first
        self.utilsDict = {
            Qt.Key_Escape: QCoreApplication.instance().quit
        }

        self.customMapping = {}

        self.reservedKeys = [
            Qt.Key_Escape,
            Qt.Key_Space,
            Qt.Key_Tab,
            Qt.Key_CapsLock,
        ]

    def updateOctave(self, value):
        #if value is -2, up key was pressed
        #so move octave up one step
        if value == -2:
            if self.octave == 5:
                self.octave = 1
            else:
                self.octave = (self.octave + 1) % 6

        #if value is -1, down key was pressed
        #so move octave down one step
        elif value == -1 and self.octave > 1:
            self.octave = (self.octave - 1) % 6

        #update octave to value mod 8
        else:
            self.octave = value % 6

        self.sound.set_octave(self.octave)

    def startNote(self, note):
        print(str(note) + " started")

        self.sound.play_note(note.value)

    def endNote(self, note):
        print(str(note) + " ended")
        if self.play_over or not self.pedal_pressed:
            self.sound.stop_note(note.value)

    def noteMapper(self, key):
        #check custom mapping first, so it takes priority
        notes = []
        if key in self.customMapping:
            notes = self.customMapping[key]

        #if key pressed is mapped to a note,
        #return that note, else return false
        elif key in self.noteDict:
            notes.append(self.noteDict[key])

        return notes

    def commandMapper(self, key):
        # if key is in the utility dictionary
        # call function mapped to that key
        if key in self.utilsDict:
            self.utilsDict[key]()
            return True

        # if key pressed is mapped to an octave,
        # change current octave to that key
        elif key in constants.octaveDict:
            argument = constants.octaveDict[key]
            self.updateOctave(argument)
            return True

        # If we already started mapping notes by clicking on keys,
        # map the clicked notes the the pressed key, stop mapping,
        # then return False so that the note can be played
        elif self.mapping_notes and key not in self.reservedKeys:
            print 'mapping notes: ' + str(self.mapping_notes)
            self.customMapping[key] = self.mapping_notes
            print self.customMapping[key]
            self.mapping_notes = []
            return False

        elif key == Qt.Key_Space:
            if not self.pedal_pressed:
                self.pedal_pressed = True

            else:
                self.pedal_pressed = False
                self.play_over = False
                self.sound.stop_all()
            return True

        elif key == Qt.Key_Tab or key == Qt.Key_CapsLock:
            self.play_over = not self.play_over
            return True

        # else key pressed is not a command
        else:
            return False

    def defaultButton(self, dialog_output):
        print("Default button pressed")

        keyboard_name = dialog_output[0]
        dialog_accepted = dialog_output[1]
        if not (keyboard_name and dialog_accepted):
            print 'Keyboard change canceled'
            return False

        self.noteDict = constants.keyboard_types[keyboard_name]
        return True


    def resetButton(self):
        print("Reset Button Pressed")
        if self.mapping_notes:
            self.mapping_notes = []
        else:
            self.customMapping = {}
        return True

    def saveButton(self, dialog_output):
        print("Save Button Pressed")
        mapping_name = dialog_output[0]
        dialog_accepted = dialog_output[1]
        if not (mapping_name and dialog_accepted):
            print 'Save canceled'
            return False

        save_mapping = []
        for key, val in self.customMapping.iteritems():
            for note in val:
                save_mapping.append((mapping_name, key, note.value))

        self.mapping_db.insert_mapping(save_mapping)
        print('New mapping saved:\n{0}'.format(save_mapping))

    def getMappingNames(self):
        return self.mapping_db.get_all_mapping_names()

    def loadButton(self, dialog_output):
        print("Load Button Pressed")
        mname = dialog_output[0]
        dialog_accepted = dialog_output[1]
        if mname == ' - ' or not dialog_accepted:
            print 'Load canceled'
            return False

        loaded_mapping = self.mapping_db.get_mapping_from_name(mname)
        print loaded_mapping
        for maps in loaded_mapping:
            if maps[0] in self.customMapping:
                self.customMapping[maps[0]].append(constants.DiscreteNotes(maps[1]))
            else:
                self.customMapping[maps[0]] = [constants.DiscreteNotes(maps[1])]

        return True

    def deleteButton(self, dialog_output):
        print("Delete Button Pressed")
        mname = dialog_output[0]
        dialog_accepted = dialog_output[1]
        if mname == ' - ' or not dialog_accepted:
            print 'Delete canceled'
            return False

        self.mapping_db.delete_mapping_from_name(mname)

class DigitalInstrumentWidget(QGraphicsView):

    def __init__(self):
        super(DigitalInstrumentWidget, self).__init__()

        self.digital_keyboard = DigitalKeyboard()
        self.initUI()

    def initUI(self):
        self.resize(800, 500)
        self.move(100, 100)
        self.setWindowTitle('Digital Keyboard')
        self.show()

        # Set up graphics stuff
        scene = QGraphicsScene()
        windowWidth = self.size().width()
        windowHeight = self.size().height()
        keyAreaBounds = QRect(0, 0, windowWidth * .85, windowHeight * 0.4)

        self.layout = QVBoxLayout()

        # Default Keyboard Button
        self.default_button = QPushButton()
        self.default_button.setText('Set Keyboard Type')
        self.default_button.show()
        self.default_button.clicked.connect(self.defaultButtonEvent)
        self.layout.addWidget(self.default_button, 100, Qt.AlignCenter)

        # Reset Key Mappings Button
        self.reset_button = QPushButton()
        self.reset_button.setText('Reset Mappings')
        #QShortcut(QKeySequence(Qt.Key_AsciiTilde), self.reset_button, self.resetButton())
        self.reset_button.show()
        self.reset_button.clicked.connect(self.resetButtonEvent)
        self.layout.addWidget(self.reset_button, 100, Qt.AlignCenter)

        # Save Key Mappings Button
        self.save_button = QPushButton()
        self.save_button.setText('Save Mappings')
        self.save_button.show()
        self.save_button.clicked.connect(self.saveButtonEvent)
        self.layout.addWidget(self.save_button, 100, Qt.AlignCenter)

        # Load Key Mappings Button
        self.load_button = QPushButton()
        self.load_button.setText('Load Mappings')
        self.load_button.show()
        self.load_button.clicked.connect(self.loadButtonEvent)
        self.layout.addWidget(self.load_button, 100, Qt.AlignCenter)

        self.delete_button = QPushButton()
        self.delete_button.setText('Delete Mappings')
        self.delete_button.show()
        self.delete_button.clicked.connect(self.deleteButtonEvent)
        self.layout.addWidget(self.delete_button, 100, Qt.AlignCenter)

        self.layout.addSpacerItem(QSpacerItem(100, 500))
        self.setLayout(self.layout)




        #add chord mappings to gui
        self.chordMappings = QGraphicsTextItem("Key Mappings:" + '\n' + "None")
        self.chordMappings.setZValue(100)
        self.chordMappings.setPos(0, -300)
        self.chordMappings.adjustSize()
        scene.addItem(self.chordMappings)

        # add labels for current octaves over piano keys
        self.octaveLeft = QGraphicsTextItem("Octave: " + str(self.digital_keyboard.octave))
        self.octaveLeft.setZValue(100)
        self.octaveLeft.setPos(150, -30)
        self.octaveLeft.adjustSize()
        scene.addItem(self.octaveLeft)

        self.octaveRight = QGraphicsTextItem("Octave: " + str(self.digital_keyboard.octave + 1))
        self.octaveRight.setZValue(100)
        self.octaveRight.setPos(475, -30)
        scene.addItem(self.octaveRight)

        # Draw white keys
        self.whiteKeys = []
        whiteKeyWidth = keyAreaBounds.width() / 14
        whiteKeyIndices = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 22]
        for i in range(14):
            key = PianoKeyItem(keyAreaBounds.x() + i * whiteKeyWidth, keyAreaBounds.y(), whiteKeyWidth, keyAreaBounds.height())
            key.instrument_widget = self

            key.note = constants.DiscreteNotes(whiteKeyIndices[i])

            # Set up key mapping label
            key.mappingLabel = QGraphicsTextItem()
            key.mappingLabel.setZValue(100)
            key.mappingLabel.setPlainText('A')
            key.mappingLabel.setPos(key.boundingRect().x() + key.boundingRect().width()/2 - key.mappingLabel.boundingRect().width()/2, key.boundingRect().y() + key.boundingRect().height()*0.8)
            key.mappingLabel.setDefaultTextColor(Qt.black)
            scene.addItem(key.mappingLabel)

            key.setBrush(Qt.white)
            self.whiteKeys.append(key)
            scene.addItem(key)

        # Draw black keys
        self.blackKeys = []
        blackKeyWidth = whiteKeyWidth / 2
        blackKeyHeight = keyAreaBounds.height() * 0.6
        blackKeyIndices = [1, 3, 6, 8, 10, 13, 15, 18, 20, 23]

        for i in range(10):
            startX = keyAreaBounds.x() + 2 * i * blackKeyWidth + blackKeyWidth * 1.5

            if i > 6:
                startX += 3*whiteKeyWidth
            elif i > 4:
                startX += 2*whiteKeyWidth
            elif i > 1:
                startX += whiteKeyWidth

            key = PianoKeyItem(startX, keyAreaBounds.y(), blackKeyWidth, blackKeyHeight)
            key.instrument_widget = self

            key.note = constants.DiscreteNotes(blackKeyIndices[i])

            # Set up key mapping label
            key.mappingLabel = QGraphicsTextItem()
            key.mappingLabel.setZValue(100)
            key.mappingLabel.setPlainText('A')
            key.mappingLabel.setPos(key.boundingRect().x() + key.boundingRect().width()/2 - key.mappingLabel.boundingRect().width()/2, key.boundingRect().y() + key.boundingRect().height()*0.8)
            key.mappingLabel.setDefaultTextColor(Qt.white)
            scene.addItem(key.mappingLabel)

            key.setBrush(Qt.black)
            self.blackKeys.append(key)
            scene.addItem(key)

        self.setScene(scene)
        self.updateUI()


    def updateUI(self):
        # Make sure the pressedKeys exists
        if not hasattr(self, 'pressedKeys') or self.pressedKeys is None:
            self.pressedKeys = [False] * 24

        chordMapString = "Key Mappings:" + '\n'

        # TODO: take out of here
        customMapping = self.digital_keyboard.customMapping
        if customMapping:
            for key in customMapping:
                chordMapString += QKeySequence(key).toString() + ': '

                for chord in customMapping[key]:
                    chordMapString += chord.name
                    chordMapString += ", "

                chordMapString += '\n\n'

        else:
            chordMapString += "None"

        self.chordMappings.setPlainText(chordMapString)

        #update octaves seen on screen
        self.octaveLeft.setPlainText("Octave: " + str(self.digital_keyboard.octave))
        self.octaveRight.setPlainText("Octave: " + str(self.digital_keyboard.octave + 1))

        keyMappings = {}
        for key, val in self.digital_keyboard.noteDict.iteritems():
            keyMappings[val] = key

        # Update color of white keys (pressed or not)
        whiteKeyIndices = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 22]
        for i in range(len(self.whiteKeys)):
            key = self.whiteKeys[i]
            curNote = key.note
            if curNote not in self.digital_keyboard.mapping_notes:
                if self.pressedKeys[whiteKeyIndices[i]]:
                    key.setBrush(Qt.gray)
                else:
                    key.setBrush(Qt.white)
            else:
                key.setBrush(Qt.blue)

            # Update key mapping string
            note = constants.DiscreteNotes(whiteKeyIndices[i])
            key.mappingLabel.setPlainText(QKeySequence(keyMappings[note]).toString())
            for k, v in self.digital_keyboard.customMapping.iteritems():
                if str(note) in str(v):
                    key.mappingLabel.setPlainText(QKeySequence(k).toString())
                    break
                elif keyMappings[note] == k:
                    key.mappingLabel.setPlainText("")

        # Update color of black keys
        blackKeyIndices = [1, 3, 6, 8, 10, 13, 15, 18, 20, 23]
        for i in range(len(self.blackKeys)):
            key = self.blackKeys[i]
            curNote = key.note
            if curNote not in self.digital_keyboard.mapping_notes:
                if self.pressedKeys[blackKeyIndices[i]]:
                    key.setBrush(Qt.gray)
                else:
                    key.setBrush(Qt.black)
            else:
                key.setBrush(Qt.blue)

            # Update key mapping string
            note = constants.DiscreteNotes(blackKeyIndices[i])
            key.mappingLabel.setPlainText(QKeySequence(keyMappings[note]).toString())
            for k, v in self.digital_keyboard.customMapping.iteritems():
                if str(note) in str(v):
                    key.mappingLabel.setPlainText(QKeySequence(k).toString())
                    break
                elif keyMappings[note] == k:
                    key.mappingLabel.setPlainText("")

        self.scene().update(self.scene().sceneRect())

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        #if the key pressed is a command, return
        #command mapper takes care of the command's actions
        if self.digital_keyboard.commandMapper(event.key()):
            # TODO: only used for updateOctave(), refactor
            self.updateUI()
            return

        #note mapper maps a key to a note
        #returns false if key is not maped to a note
        notes = self.digital_keyboard.noteMapper(event.key())

        #if key is mapped to a note, start the note
        for note in notes:
            print 'Printing notes:' + str(note)
            self.digital_keyboard.startNote(note)

            # Mark the key as pressed for the UI
            self.pressedKeys[note.value] = True
            self.updateUI()

        if not notes:
            #else the key pressed does nothing currently
            print("key not mapped")

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return

        #key release only matters for notes
        #because notes can be held
        notes = self.digital_keyboard.noteMapper(event.key())

        #if the key is mapped, end the note
        for note in notes:
            self.digital_keyboard.endNote(note)

            # Mark the key as released for the UI
            self.pressedKeys[note.value] = False
            self.updateUI()

    def defaultButtonEvent(self):
        dialog_output = QInputDialog().getItem(self, 'Select Keyboard Type',
                '', constants.keyboard_types.keys())
        if self.digital_keyboard.defaultButton(dialog_output):
            self.updateUI()

    def saveButtonEvent(self):
        if not self.digital_keyboard.customMapping:
            return

        # Save popup
        dialog_output = QInputDialog().getText(self, 'Save Key Mapping', 'Enter key mapping name here')
        self.digital_keyboard.saveButton(dialog_output)

    def resetButtonEvent(self):
        if self.digital_keyboard.resetButton():
            self.updateUI()

    def loadButtonEvent(self):
        mapping_names = self.digital_keyboard.getMappingNames()
        dropdown_options = [' - '] + [i[0] for i in mapping_names]
        dialog_output = QInputDialog().getItem(self, 'Load Key Mapping',
                'Select key mapping', dropdown_options)

        if self.digital_keyboard.loadButton(dialog_output):
            self.updateUI()

    def deleteButtonEvent(self):
        mapping_names = self.digital_keyboard.getMappingNames()
        dropdown_options = [' - '] + [i[0] for i in mapping_names]
        dialog_output = QInputDialog().getItem(self, 'Delete Saved Key Mapping',
                'Delete key mapping (PERMANENT)', dropdown_options)

        self.digital_keyboard.deleteButton(dialog_output)


def main():
    fluidsynth.init("HS Synth Collection I.sf2", "alsa")
    # fluidsynth.init("Nice-Keys.sf2", "alsa")
    app = QApplication(sys.argv)
    DigitalInstrumentWidget()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
