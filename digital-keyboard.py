#!/usr/bin/env python

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QBrush, QPalette, QKeySequence
from mingus.core import progressions, intervals
from mingus.core import chords as ch
from mingus.containers import NoteContainer, Note
from mingus.midi import fluidsynth
import time
import sys
from random import random
from pygame import key
from enum import Enum
from sound import Sound
from db import db

create_sound = Sound()
mapping_db = db()

# TODO: remove global keywords
# TODO: remove needless returns
pedal_pressed = False
play_over = False
mapping_notes = []


class PianoKeyItem(QGraphicsRectItem):
  def mousePressEvent(self, event):
    if hasattr(self, 'note') and self.note is not None:
      if not self.note in mapping_notes:
        mapping_notes.append(self.note)
      else:
        mapping_notes.remove(self.note)
      self.instrumentWidget.updateUI()


class DiscreteNotes(Enum):
  C0   = 0
  Cs0  = 1
  D0   = 2
  Ds0  = 3
  E0   = 4
  F0   = 5
  Fs0  = 6
  G0   = 7
  Gs0  = 8
  A0   = 9
  As0  = 10
  B0   = 11
  C1   = 12
  Cs1  = 13
  D1   = 14
  Ds1  = 15
  E1   = 16
  F1   = 17
  Fs1  = 18
  G1   = 19
  Gs1  = 20
  A1   = 21
  As1  = 22
  B1   = 23


class DigitalInstrumentWidget(QGraphicsView):

  def __init__(self):
    super(DigitalInstrumentWidget, self).__init__()
    self.initInsturment()
    self.initUI()

  def initUI(self):
    self.resize(800, 500)
    self.move(100, 100)
    self.setWindowTitle('EECS 481 Digital Instrument')
    self.show()

    # Set up graphics stuff
    scene = QGraphicsScene()
    windowWidth = self.size().width()
    windowHeight = self.size().height()
    keyAreaBounds = QRect(0, 0, windowWidth * .85, windowHeight * 0.4)

    # Reset Key Mappings Button
    self.layout = QVBoxLayout()
    self.reset_button = QPushButton()
    self.reset_button.setText('Reset Mappings')
    #QShortcut(QKeySequence(Qt.Key_AsciiTilde), self.reset_button, self.resetButton())
    self.reset_button.show()
    self.reset_button.clicked.connect(self.resetButton)
    self.layout.addWidget(self.reset_button, 100, Qt.AlignCenter)

    # Save Key Mappings Button
    self.save_button = QPushButton()
    self.save_button.setText('Save Mappings')
    self.save_button.show()
    self.save_button.clicked.connect(self.saveButton)
    self.layout.addWidget(self.save_button, 110, Qt.AlignCenter)

    # Load Key Mappings Button
    self.load_button = QPushButton()
    self.load_button.setText('Load Mappings')
    self.load_button.show()
    self.load_button.clicked.connect(self.loadButton)
    self.layout.addWidget(self.load_button, 100, Qt.AlignCenter)

    self.delete_button = QPushButton()
    self.delete_button.setText('Delete Mappings')
    self.delete_button.show()
    self.delete_button.clicked.connect(self.deleteButton)
    self.layout.addWidget(self.delete_button, 100, Qt.AlignCenter)

    self.layout.addSpacerItem(QSpacerItem(100, 500))
    self.setLayout(self.layout)




    #add chord mappings to gui
    self.chordMappings = QGraphicsTextItem("Chord Mappings:" + '\n' + "None")
    self.chordMappings.setZValue(100)
    self.chordMappings.setPos(0, -300)
    self.chordMappings.adjustSize()
    scene.addItem(self.chordMappings)

    # add labels for current octaves over piano keys
    self.octaveLeft = QGraphicsTextItem("Octave: " + str(self.octave))
    self.octaveLeft.setZValue(100)
    self.octaveLeft.setPos(150, -30)
    self.octaveLeft.adjustSize()
    scene.addItem(self.octaveLeft)

    self.octaveRight = QGraphicsTextItem("Octave: " + str(self.octave + 1))
    self.octaveRight.setZValue(100)
    self.octaveRight.setPos(475, -30)
    scene.addItem(self.octaveRight)

    # Draw white keys
    self.whiteKeys = []
    whiteKeyWidth = keyAreaBounds.width() / 14
    whiteKeyIndices = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 22]
    for i in range(14):
      key = PianoKeyItem(keyAreaBounds.x() + i * whiteKeyWidth, keyAreaBounds.y(), whiteKeyWidth, keyAreaBounds.height())
      key.instrumentWidget = self

      key.note = DiscreteNotes(whiteKeyIndices[i])

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
      key.instrumentWidget = self

      key.note = DiscreteNotes(blackKeyIndices[i])

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

    chordMapString = "Chord Mappings:" + '\n'

    if self.customMapping:
      for key in self.customMapping:
        chordMapString += QKeySequence(key).toString() + ': '

        for chord in self.customMapping[key]:
          chordMapString += chord.name
          chordMapString += ", "

        chordMapString += '\n\n'

    else:
      chordMapString += "None"

    self.chordMappings.setPlainText(chordMapString)

    #update octaves seen on screen
    self.octaveLeft.setPlainText("Octave: " + str(self.octave))
    self.octaveRight.setPlainText("Octave: " + str(self.octave + 1))

    keyMappings = {}
    for k in self.noteDict:
      keyMappings[self.noteDict[k]] = k

    # Update color of white keys (pressed or not)
    whiteKeyIndices = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 22]
    for i in range(len(self.whiteKeys)):
      key = self.whiteKeys[i]
      curNote = key.note
      if curNote not in mapping_notes:
        if self.pressedKeys[whiteKeyIndices[i]]:
          key.setBrush(Qt.gray)
        else:
          key.setBrush(Qt.white)
      else:
        key.setBrush(Qt.blue)

      # Update key mapping string
      note = DiscreteNotes(whiteKeyIndices[i])
      key.mappingLabel.setPlainText(QKeySequence(keyMappings[note]).toString())
      for k, v in self.customMapping.iteritems():
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
      if curNote not in mapping_notes:
        if self.pressedKeys[blackKeyIndices[i]]:
          key.setBrush(Qt.gray)
        else:
          key.setBrush(Qt.black)
      else:
        key.setBrush(Qt.blue)

      # Update key mapping string
      note = DiscreteNotes(blackKeyIndices[i])
      key.mappingLabel.setPlainText(QKeySequence(keyMappings[note]).toString())
      for k, v in self.customMapping.iteritems():
        if str(note) in str(v):
          key.mappingLabel.setPlainText(QKeySequence(k).toString())
          break
        elif keyMappings[note] == k:
          key.mappingLabel.setPlainText("")

    self.scene().update(self.scene().sceneRect())


  def initInsturment(self):
    #init octave to 0
    self.octave = 1;

    #keys A-K map to notes G-F
    #keys W, E and T-U map to notes C#-A#
    self.noteDict = {
      Qt.Key_Z: DiscreteNotes.C0,
      Qt.Key_X: DiscreteNotes.D0,
      Qt.Key_C: DiscreteNotes.E0,
      Qt.Key_A: DiscreteNotes.F0,
      Qt.Key_S: DiscreteNotes.G0,
      Qt.Key_D: DiscreteNotes.A0,
      Qt.Key_F: DiscreteNotes.B0,
      Qt.Key_Q: DiscreteNotes.Cs0,
      Qt.Key_W: DiscreteNotes.Ds0,
      Qt.Key_E: DiscreteNotes.Fs0,
      Qt.Key_R: DiscreteNotes.Gs0,
      Qt.Key_T: DiscreteNotes.As0,
      Qt.Key_B: DiscreteNotes.C1,
      Qt.Key_N: DiscreteNotes.D1,
      Qt.Key_M: DiscreteNotes.E1,
      Qt.Key_H: DiscreteNotes.F1,
      Qt.Key_J: DiscreteNotes.G1,
      Qt.Key_K: DiscreteNotes.A1,
      Qt.Key_L: DiscreteNotes.B1,
      Qt.Key_Y: DiscreteNotes.Cs1,
      Qt.Key_U: DiscreteNotes.Ds1,
      Qt.Key_I: DiscreteNotes.Fs1,
      Qt.Key_O: DiscreteNotes.Gs1,
      Qt.Key_P: DiscreteNotes.As1,
    }

    #init octave dict to map to the number keys
    #key up and down are special cases caught by updateOctave
    self.octaveDict = {
      Qt.Key_Up:   -2,
      Qt.Key_Down: -1,
      Qt.Key_1:     1,
      Qt.Key_2:     2,
      Qt.Key_3:     3,
      Qt.Key_4:     4,
      Qt.Key_5:     5,
    }

    self.soundDict = {
      Qt.Key_F1: "HS Synth Collection I.sf2",
    }

    #so far, utils dict only maps esc to quitting
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

    self.updateUI()

    create_sound.set_octave(self.octave)

  def startNote(self, note):
    print(str(note) + " started")

    create_sound.play_note(note.value)

  def endNote(self, note):
    print(str(note) + " ended")
    if play_over or not pedal_pressed:
      create_sound.stop_note(note.value)

    #else:
    #  create_sound.note_decay(note.value)

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
    global pedal_pressed
    global play_over
    global mapping_notes

    #if key is in the utility dictionary
    #call function mapped to that key
    if key in self.utilsDict:
      self.utilsDict[key]()
      return True

    #if key pressed is mapped to an octave,
    #change current octave to that key
    elif key in self.octaveDict:
      argument = self.octaveDict[key]
      self.updateOctave(argument)
      return True

    #If we already started mapping notes by clicking on keys,
    #map the clicked notes the the pressed key, stop mapping,
    #then return False so that the note can be played
    elif mapping_notes and key not in self.reservedKeys:
      print 'mapping notes: ' + str(mapping_notes)
      self.customMapping[key] = mapping_notes
      print self.customMapping[key]
      mapping_notes = []
      return False

    elif key in self.soundDict:
      argument = self.soundDict[key]
      fluidsynth.init(argument, "alsa")
      return True

    elif key == Qt.Key_Space:
      if not pedal_pressed:
        pedal_pressed = True

      else:
        pedal_pressed = False
        play_over = False
        create_sound.stop_all()
      return True

    elif key == Qt.Key_Tab or key == Qt.Key_CapsLock:
      play_over = not play_over
      return True

    #else key pressed is not a command
    else:
      return False

  def keyPressEvent(self, event):
    if event.isAutoRepeat():
      return

    #if the key pressed is a command, return
    #command mapper takes care of the command's actions
    if self.commandMapper(event.key()):
      return

    #note mapper maps a key to a note
    #returns false if key is not maped to a note
    notes = self.noteMapper(event.key())

    #if key is mapped to a note, start the note
    for note in notes:
      print 'Prinring notes:' + str(note)
      self.startNote(note)

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
    notes = self.noteMapper(event.key())

    #if the key is mapped, end the note
    for note in notes:
      self.endNote(note)

      # Mark the key as released for the UI
      self.pressedKeys[note.value] = False
      self.updateUI()

  def resetButton(self):
    print("Reset Button Pressed")
    global mapping_notes
    if mapping_notes:
      mapping_notes = []
    else:
      self.customMapping = {}
    self.updateUI()

  def saveButton(self):
    print("Save Button Pressed")
    if not self.customMapping:
      return

    # Save popup
    dialog_output = QInputDialog().getText(self, 'Save Key Mapping', 'Enter key mapping name here')
    mapping_name = dialog_output[0]
    dialog_accepted = dialog_output[1]
    if not (mapping_name and dialog_accepted):
      print 'Save canceled'
      return

    save_mapping = []
    for key, val in self.customMapping.iteritems():
      for note in val:
        save_mapping.append((mapping_name, key, note.value))

    mapping_db.insert_mapping(save_mapping)
    print('New mapping saved:\n{0}'.format(save_mapping))


  def loadButton(self):
    print("Load Button Pressed")
    mapping_names = mapping_db.get_all_mapping_names()
    dropdown_options = [' - '] + [i[0] for i in mapping_names]

    dialog_output = QInputDialog().getItem(self, 'Load Key Mapping',
        'Select key mapping', dropdown_options)
    mname = dialog_output[0]
    dialog_accepted = dialog_output[1]
    if mname == ' - ' or not dialog_accepted:
      print 'Load canceled'

    loaded_mapping = mapping_db.get_mapping_from_name(mname)
    print loaded_mapping
    for maps in loaded_mapping:
      if maps[0] in self.customMapping:
        self.customMapping[maps[0]].append(DiscreteNotes(maps[1]))
      else:
        self.customMapping[maps[0]] = [DiscreteNotes(maps[1])]

    self.updateUI()

  def deleteButton(self):
    print("Delete Button Pressed")
    mapping_names = mapping_db.get_all_mapping_names()
    dropdown_options = [' - '] + [i[0] for i in mapping_names]

    dialog_output = QInputDialog().getItem(self, 'Delete Saved Key Mapping',
        'Delete key mapping (PERMANENT)', dropdown_options)
    mname = dialog_output[0]
    dialog_accepted = dialog_output[1]
    if mname == ' - ' or not dialog_accepted:
      print 'Delete canceled'

    mapping_db.delete_mapping_from_name(mname)


def main():
  fluidsynth.init("HS Synth Collection I.sf2", "alsa")
  # fluidsynth.init("Nice-Keys.sf2", "alsa")
  app = QApplication(sys.argv)
  window = DigitalInstrumentWidget()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
