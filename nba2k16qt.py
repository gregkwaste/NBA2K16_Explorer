from PySide.QtCore import *
from PySide.QtGui import *

# pymedia
# import pymedia.audio.acodec as acodec
# import pymedia.audio.sound as sound
# import pymedia.muxer as muxer

from vlc_player import Player
# from unused_stuff import PhononAudioPlayer


# external imports
from pygl_widgets import *
from myqmodels import *

# internal imports
import sys
import struct
import time
import threading
import gc
import pylzma
import os
import zlib
import webbrowser
from StringIO import StringIO
from subprocess import call
# from collections import OrderedDict
# from pylzma import compress
# from pysideuic.Compiler.qtproxies import QtGui
from _winreg import *
from nba2k16commonvars import *

# Import Custom Modules/Libraries
sys.path.append('../gk_blender_lib/modules')
from string_func import *
from scheduler import *
from parsing_functions import *


class dataInitiate:

    def __init__(self, msg, datalen):
        self.msg = msg
        self.datalen = datalen


class scheduleItem:  # not used keep thinking...

    def __init__(self, datadict):
        for key in datadict:
            setattr(self, key, datadict[key])


class x38header:

    def __init__(self, f):
        self.id0 = struct.unpack('<I', f.read(4))[0]
        self.id1 = struct.unpack('<I', f.read(4))[0]
        self.type = struct.unpack('<Q', f.read(8))[0]
        self.size = struct.unpack('<Q', f.read(8))[0]
        self.comp_type = struct.unpack('<Q', f.read(8))[0]
        self.start = struct.unpack('<Q', f.read(8))[0]
        self.stop = struct.unpack('<Q', f.read(8))[0]
        f.read(8)  # zeroes

    def write(self, f):
        f.write(struct.pack('<2I6Q', self.id0, self.id1, self.type,
                            self.size, self.comp_type, self.start, self.stop, 0))


class file_entry:

    def __init__(self, f, custom=False, offset=None, id0=None, id1=None, type=None, g_id=None, size=None, data=None):
        if not custom:
            self.off = f.tell()
            self.id0 = struct.unpack('<I', f.read(4))[0]
            self.id1 = struct.unpack('<I', f.read(4))[0]
            self.type = struct.unpack('<Q', f.read(8))[0]
            self.g_id = 0  # used later
            self.size = 0  # used later
            if self.type == 1:  # zlib or lzma data
                self.data = struct.unpack('<Q', f.read(8))
            elif self.type == 2:  # zip files
                self.data = struct.unpack('<2Q', f.read(16))
            elif self.type == 3:  # empty /separators?
                self.data = struct.unpack('<3Q', f.read(24))
            else:
                print('unknown type: ', self.type)
            # data[1] contains the file offsets
        else:
            # Create Custom fileEntry
            self.off = offset
            self.id0 = id0
            self.id1 = id1
            self.type = type
            self.g_id = g_id
            self.size = size
            self.data = data


class cdf_file_entry:

    def __init__(self, f, custom=False, offset=None, id0=None, id1=None, type=None, g_id=None, size=None, data=None):
        if not custom:
            self.off = struct.unpack('<Q', f.read(8))[0]
            self.size = struct.unpack('<Q', f.read(8))[0]
            f.seek(0x8, 1)
            self.id0 = 0
            self.id1 = 0
            self.g_id = 0
            self.type = 0
            self.pad = struct.unpack('<Q', f.read(8))[0]  # used later
        else:
            # Create Custom fileEntry
            self.off = offset
            self.id0 = id0
            self.id1 = id1
            self.type = type
            self.g_id = g_id
            self.size = size
            self.data = data


class header16:

    def __init__(self, f):
        self.magic = struct.unpack('>I', f.read(4))[0]
        print(hex(self.magic))
        # exceptions
        if self.magic == 0x7EA1CFBB:  # handle ogg  files
            f.seek(0x14, 1)
            f_size = struct.unpack(
                '<I', f.read(4))[0] + struct.unpack('<I', f.read(4))[0] - 8
            f.read(4)  # skipp 2048
            preentries_num = struct.unpack('<I', f.read(4))[0]
            f.read(4)  # skip zeroes
            preentries_size = preentries_num * 0x8
            f_size -= preentries_size
            f.read(preentries_size)
            self.file_entries = []
            self.file_entries.append((f.tell(), f_size))
            return
        elif self.magic == 0x00000000:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic in index_table:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic == 0x5A4C4942:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic == 0x504B0304:  # zip files
            f.seek(-4, 1)
            off = f.tell()
            subfile = sub_file(f, 'ZIP', stop - off)
            self.file_entries = []
            self.file_entries.append((off, stop - off))
            print self.file_entries
            return
        # encrypted data
        elif self.magic in [0xC6B0581C, 0x4A50922A, 0xAAC40536]:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return

        if not self.magic in [0x305098F0, 0x94EF3BFF]:
            print('unknown magic ', self.magic)
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return


class header:

    def __init__(self, f):
        # self.main_offset=main_off
        self.magic = struct.unpack('>I', f.read(4))[0]
        # exceptions
        if self.magic == 0x7EA1CFBB:  # handle ogg  files
            f.seek(0x14, 1)
            f_size = struct.unpack(
                '<I', f.read(4))[0] + struct.unpack('<I', f.read(4))[0] - 8
            f.read(4)  # skipp 2048
            preentries_num = struct.unpack('<I', f.read(4))[0]
            f.read(4)  # skip zeroes
            preentries_size = preentries_num * 0x8
            f_size -= preentries_size
            f.read(preentries_size)
            self.file_entries = []
            self.file_entries.append((f.tell(), f_size))
            return
        elif self.magic == 0x00000000:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic in index_table:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic == 0x5A4C4942:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return
        elif self.magic == 0x504B0304:  # zip files
            f.seek(-4, 1)
            off = f.tell()
            subfile = sub_file(f, 'ZIP', stop - off)
            self.file_entries = []
            self.file_entries.append((off, stop - off))
            return
        # encrypted data
        elif self.magic in [0xC6B0581C, 0x4A50922A, 0xAAC40536]:
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return

        if not self.magic in [0x305098F0, 0x94EF3BFF]:
            print('unknown magic ', self.magic)
            self.file_entries = []
            self.file_entries.append((f.tell() - 4, 0))
            return

        self.header_length = struct.unpack('<I', f.read(4))[0]
        self.next_off = struct.unpack('>I', f.read(4))[0]
        f.read(4)
        self.sub_head_count = struct.unpack(
            '<Q', f.read(8))[0]  # x38 headers counter
        s = struct.unpack('<Q', f.read(8))[0]
        self.x38headersOffset = s + f.tell() - 8 - 1
        # additional information on the header counter
        self.head_count = (s - 9) // 16
        self.file_count = struct.unpack('<Q', f.read(8))[0]
        self.sub_heads = []
        # self.sub_heads.append(f.tell()-self.main_offset +
        # struct.unpack('<Q',f.read(8))[0]-1)
        self.sub_heads.append(f.tell() + struct.unpack('<Q', f.read(8))[0] - 1)
        if self.magic == 0x305098F0 and self.head_count > 1:
            # self.sub_heads.append(f.tell()-self.main_offset + struct.unpack('<Q',f.read(8))[0]-1)
            # self.sub_heads.append(f.tell()-self.main_offset +
            # struct.unpack('<Q',f.read(8))[0]-1)
            self.sub_heads.append(
                f.tell() + struct.unpack('<Q', f.read(8))[0] - 1)
            self.sub_heads.append(
                f.tell() + struct.unpack('<Q', f.read(8))[0] - 1)

        f.seek(self.x38headersOffset)
        self.x38headers = []
        for i in range(self.sub_head_count):
            self.x38headers.append(x38header(f))
        # Fix x38headers start
        # for x38 in self.x38headers:
        #    x38.start+=main_off
        self.sub_heads_data = []
        self.file_entries = []
        self.file_name = None
        self.file_sizes = []

        # Store Basic Information (Included to all archives)

        # small_base=self.main_offset+f.tell()-1
        # small_base=f.tell()-1

        for x38 in self.x38headers:
            x38_file_entries = []
            x38_file_sizes = []
            print('x38 Start: ', x38.start, 'x38 Type: ',
                  x38.type, 'x38 CompType: ', x38.comp_type)
            if x38.type == 1 and self.magic == 0x94EF3BFF:
                print('IFF File Container')
                f.seek(self.sub_heads[0])
                small_base = self.sub_heads[0] - 1
                print('File Description Offset Base: ',
                      small_base, 'file_count: ', self.file_count)

                templist = []
                small_base = 0
                for j in range(self.file_count):
                    templist.append(
                        struct.unpack('<Q', f.read(8))[0] + self.sub_heads[0] - 1 + small_base)
                    small_base += 8

                # print(templist)
                # force file_count for another weird kind of archives
                # if self.sub_head_count==1 and self.x38headers[0].type==8:      I will check if it works without this
                #    self.file_count=1
                g_id = 0
                mode = 0
                for j in range(self.file_count):
                    f.seek(templist[j])

                    temp = file_entry(f)
                    temp.g_id = g_id

                    if not temp.type == 3:
                        if mode == 0:
                            temp.size = temp.data[0]
                        else:
                            temp.size = temp.data[1]
                        x38_file_entries.append(temp)
                    else:
                        if not temp.data[0]:
                            mode = 1
                        else:
                            mode = 0
                        g_id += 1

                # file sizes calculation and offsets
                stop = x38.stop

                # for j in range(len(self.file_entries) - 1):
                #    self.file_sizes.append(self.file_entries[j + 1].size - self.file_entries[j].size)
                # self.file_sizes.append(stop - self.file_entries[-1].size)  #
                # store the last item size

                for j in range(len(x38_file_entries) - 1):
                    x38_file_sizes.append(
                        x38_file_entries[j + 1].size - x38_file_entries[j].size)
                # store the last item size
                x38_file_sizes.append(stop - x38_file_entries[-1].size)

                for entry in x38_file_entries:  # fix offsets
                    # print(entry.size,x38.start)
                    entry.size += x38.start
                    entry.off = entry.size
                    print(entry.off)

                # Append Lists to Parent
                self.file_entries.extend(x38_file_entries)
                self.file_sizes.extend(x38_file_sizes)

                self.sub_heads_data.append(templist)  # Append templist
            elif x38.type == 0x10 or (x38.type == 0x08 and x38.comp_type in [0x05, 0x06]):
                print('Zlib Section')
                temp = file_entry(f, custom=True, offset=x38.start, id0='ZLIB',
                                  id1=None, type=None, g_id=0, size=x38.stop, data=None)
                self.file_entries.append(temp)
                self.file_sizes.append(x38.stop)
            elif x38.type == 0x00 and x38.comp_type == 0x00:
                pass  # Empty Section
            elif x38.type == 0x08 and x38.comp_type == 0x00 and self.magic == 0x94EF3BFF:
                pass  # Empty Section
            elif x38.type == 0x01 and x38.comp_type == 0x00 and self.magic == 0x305098F0:
                print('CDF File Container')
                # Omitting practically FUCKING USELESS First Section
                big_base = self.sub_heads[1] - 1
                f.seek(big_base + 1)

                print('File Description Offset Base: ',
                      big_base, 'file_count: ', self.file_count)

                templist = []
                small_base = 0
                for j in range(self.file_count):
                    templist.append(
                        struct.unpack('<Q', f.read(8))[0] + big_base + small_base)
                    small_base += 8

                for j in range(self.file_count):
                    f.seek(templist[j])
                    self.file_entries.append(cdf_file_entry(f))

                # file sizes calculation and offsets
                for entry in self.file_entries:
                    self.file_sizes.append(entry.size)
                for entry in self.file_entries:
                    entry.off += x38.start  # fix offsets

                self.sub_heads_data.append(templist)  # Append templist

                # Parse CDF File Name
                f.seek(self.sub_heads[-1])
                self.file_name = read_string_2(f)
            else:
                print('Unimplemented Type: ', x38.type)

        # if self.head_count>1 and self.head_count<4:
            # temp=[]
            # for j in range(self.file_count):
            #    temp.append(struct.unpack('<Q',f.read(8))[0]+small_base)
            # self.sub_heads_data.append(temp)
            # file sizes
            # self.file_sizes=[]
            # temp=[]
            # for j in range(self.file_count*self.sub_head_count):
            #    self.file_sizes.append(struct.unpack('<2Q',f.read(16)))
            # if self.sub_head_count>1:
            #    temp=self.file_sizes
            #    self.file_sizes=[]
            #    for j in range(self.file_count):
            #        self.file_sizes.append(temp[self.sub_head_count*j])


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('NBA2K16 Explorer v' + version)
        self.setWindowIcon(QIcon('tool_icon.ico'))
        self.setupUi()
        self.actionOpen.triggered.connect(self.open_file_table)
        self.actionExit.triggered.connect(self.close_app)
        self.actionApply_Changes.triggered.connect(runScheduler)
        self.actionPreferences.triggered.connect(self.preferences_window)
        self.actionSave_Comments.triggered.connect(self.save_comments)
        self.clipboard = QClipboard()

        self.prepareUi()

        self.pref_window = PreferencesWindow()  # preferences window
        self.iffEditorWindow = IffEditorWindow()
        # Assign Corresponding Action
        self.actionShowIffWindow.triggered.connect(self.iffEditorWindow.show)

        # self properties
        self._active_file = None
        self.list = []  # List that will contain all the game file info
        self.list_names = {}  # List that will contain all the game file names
        self.comments = {}  # Initialize Comments
        self.parse_comments()
        print self.comments.keys()

        self.about_dialog = AboutDialog()  # Create About Dialog

    def setupUi(self):
        # self.setObjectName("MainWindow")
        self.resize(1400, 800)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        # self.gridLayout = QGridLayout(self.centralwidget)
        self.mainSplitter = QSplitter()
        self.mainSplitter.setOrientation(QtCore.Qt.Horizontal)

        # splitter is the Left Part Splitter
        self.splitter = QSplitter(self.mainSplitter)
        self.splitter.setLineWidth(1)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        # groupBox_2 stores the top left treeview
        self.groupBox_2 = QGroupBox(self.splitter)
        self.groupBox_2.setTitle("2K Archive List")
        self.groupBox_2VLayout = QVBoxLayout(self.groupBox_2)
        # ArchiveTabs is the widget which will store all the
        # different archive contents
        # I'm adding treeviews in the tab programmaticaly
        self.archiveTabs = QTabWidget(self.groupBox_2)
        self.archiveTabs.setMinimumSize(QtCore.QSize(0, 264))
        self.archiveTabs.setTabPosition(QTabWidget.North)
        self.archiveTabs.setTabShape(QTabWidget.Rounded)
        self.archiveTabs.setObjectName("archiveTabs")
        self.groupBox_2VLayout.addWidget(self.archiveTabs)

        # Horizontal Layout stores the tab widgets search stuff
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.searchLabel = QLabel(self.groupBox_2)
        self.searchLabel.setText("Search:")
        self.horizontalLayout.addWidget(self.searchLabel)
        self.searchBar = QLineEdit(self.groupBox_2)
        self.horizontalLayout.addWidget(self.searchBar)
        self.groupBox_2VLayout.addLayout(self.horizontalLayout)

        # treeView_2 will hold the archive contents
        self.horizSplitter = QSplitter(self.splitter)
        self.horizSplitter.setOrientation(QtCore.Qt.Horizontal)

        self.groupBox = QGroupBox(self.horizSplitter)
        self.groupBox.setTitle("Archive File List")
        self.groupBoxVLayout = QVBoxLayout(self.groupBox)
        # treeView_2 is the File List Treeview Bottom Left
        self.treeView_2 = QTreeView(self.groupBox)
        self.treeView_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView_2.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.treeView_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView_2.setUniformRowHeights(True)
        self.treeView_2.setObjectName("treeView_2")
        self.groupBoxVLayout.addWidget(self.treeView_2)
        # self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        # Right TabWidget
        self.tabWidget = QTabWidget(self.horizSplitter)

        # Tools Tab
        self.tab = QWidget()
        sizePolicy = QSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.tab.sizePolicy().hasHeightForWidth())
        self.tab.setSizePolicy(sizePolicy)
        # self.tab.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.tab)

        self.tabWidget.addTab(self.tab, "AudioPlayer")
        # self.gridLayout.addWidget(self.splitter_4, 0, 1, 1, 1)

        self.setCentralWidget(self.mainSplitter)

        # Status Bar
        self.statusBar = QStatusBar(self)
        self.statusBar.setStatusTip("")
        self.statusBar.setSizeGripEnabled(True)
        self.setStatusBar(self.statusBar)

        # Define MenuBar
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1276, 21))
        # File Menu
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setTitle("File")
        # Options Menu
        self.menuOptions = QMenu(self.menubar)
        self.menuOptions.setTitle("Options")

        self.actionOpen = QAction(self)
        self.actionOpen.setText("Load Archives")
        self.actionExit = QAction(self)
        self.actionExit.setText("Exit")
        self.actionPreferences = QAction(self)
        self.actionPreferences.setText("Preferences")
        self.actionApply_Changes = QAction(self)
        self.actionApply_Changes.setText("Apply Changes")
        self.actionSave_Comments = QAction(self)
        self.actionSave_Comments.setText("Save Comments")
        self.actionShowIffWindow = QAction(self)
        self.actionShowIffWindow.setText("Show Iff Editor")

        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionApply_Changes)
        self.menuFile.addAction(self.actionExit)
        self.menuOptions.addAction(self.actionPreferences)
        self.menuOptions.addAction(self.actionSave_Comments)
        self.menuOptions.addAction(self.actionShowIffWindow)

        # About Dialog
        about_action = QAction(self.menubar)
        about_action.setText("About")
        about_action.triggered.connect(self.about_window)

        # Add actions to menubar
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menubar.addAction(about_action)
        self.setMenuBar(self.menubar)

        self.tabWidget.setCurrentIndex(0)
        self.archiveTabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.archiveTabs, self.searchBar)
        self.setTabOrder(self.searchBar, self.treeView_2)
        self.setTabOrder(self.treeView_2, self.tabWidget)

    def prepareUi(self):
        self.main_viewer_sortmodels = []  # List for sortmodels storage
        self.current_sortmodel = None
        self.current_tableView = None
        self.current_tableView_index = None

        # Active File Data Attribs
        self._active_file_data = None
        self._active_file_handle = None
        self._active_file_path = None

        # ArchiveTabs Wigdet Functions
        self.archiveTabs.currentChanged.connect(self.set_currentTableData)

        # SearchBar Options
        self.searchBar.returnPressed.connect(self.mainViewerFilter)

        # Subfiles Treeview settings
        # self.treeView_2.doubleClicked.connect(self.read_subfile)

        self.treeView_2.setUniformRowHeights(True)
        self.treeView_2.header().setResizeMode(QHeaderView.Stretch)

        # Treeview 2 context menu
        # self.treeView_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.treeView_2.customContextMenuRequested.connect(self.ctx_menu)

        # Subfile Contents Treeview settings
        # self.treeView_3.clicked.connect(self.open_subfile)
        # self.treeView_3.entered.connect(self.open_subfile)

        # self.treeView_3.setUniformRowHeights(True)
        # self.treeView_3.header().setResizeMode(QHeaderView.Stretch)

        # GLWIDGET
        # self.glviewer = GLWidgetQ(self)
        # self.splitter_4.addWidget(self.glviewer)
        # self.glviewer.renderText(0.5, 0.5, "3dgamedevblog")
        # self.glviewer.changeObject()

        # self.glviewer.cubeDraw()

        # Media Widget
        self.sound_player = Player()
        soundPlayerLayout = QVBoxLayout()
        soundPlayerLayout.addWidget(QLabel('Audio Player'))
        soundPlayerLayout.addWidget(self.sound_player.widget)

        # self.tabWidget.addTab(self.sound_player, "Media Player") #  Vlc
        # Player
        tab = self.tabWidget.widget(0)  # Getting first tab
        tablayout = tab.layout()
        tablayout.addLayout(soundPlayerLayout)

        # Text Editor Tab
        # self.text_editor = QPlainTextEdit()
        # self.tabWidget.addTab(self.text_editor, "Text Editor")

        # Import Scheduler
        self.scheduler = QTreeView()
        self.scheduler.setUniformRowHeights(True)
        self.schedulerFiles = []
        # self.scheduler.header().setResizeMode(QHeaderView.Stretch)
        self.scheduler_model = None
        self.tabWidget.addTab(self.scheduler, 'Import Scheduler')

        # Statusbar
        self.progressbar = QProgressBar()
        self.progressbar.setMaximumSize(500, 19)
        self.progressbar.setAlignment(Qt.AlignRight)
        # self.main_viewer_model.progressTrigger.connect(self.progressbar.setValue)

        # 3dgamedevblog label
        # image_pix=QPixmap.fromImage(image)
        self.status_label = QLabel()
        # self.connect(self.status_label, SIGNAL('clicked()'), self.visit_url)
        self.status_label.setText(
            "<a href=\"https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=arianos10@gmail.com&lc=GR&item_name=3dgamedevblog&currency_code=EUR&bn=PP-DonationsBF:btn_donateCC_LG.gif:NonHosted\">Donate to 3dgamedevblog</a>")
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.status_label.setOpenExternalLinks(True)
        # self.status_label.setPixmap(image_pix)

        # self.statusBar.addPermanentWidget(self.progressbar)
        self.statusBar.addPermanentWidget(self.status_label)
        self.statusBar.showMessage('Ready')

        # Shortcuts
        # shortcut=QShortcut(QKeySequence(self.tr("Ctrl+F","Find")),self.treeView)
        # shortcut.activated.connect(self.find)

    def set_currentTableData(self, index):
        # Setting Current Sortmodel, to the Sortmodel of the TableView of the
        # Current Tab
        self.current_tableView = self.archiveTabs.widget(index)
        self.current_sortmodel = self.current_tableView.model()
        self.current_tableView_index = QModelIndex()

    def mainViewerFilter(self):
        index = self.current_sortmodel.findlayer(self.searchBar.text())
        selmod = self.current_tableView.selectionModel()
        selmod.clear()
        selmod.select(index, QItemSelectionModel.Rows)
        self.current_tableView.setCurrentIndex(index)

    # Show Preferences Window
    def preferences_window(self):
        self.pref_window.show()

    # About Window
    def about_window(self):
        self.about_dialog.show()

    # Main Functions
    def visit_url(self):
        webbrowser.open('http:\\3dgamedevblog.com')

    def main_ctx_menu(self, position):
        '''CONTEXT MENU ON THE TOP-LEFT TABLEVIEW'''
        print 'Executing Main Context'
        selmod = self.current_tableView.selectionModel().selectedIndexes()
        arch_name = self.archiveTabs.tabText(self.archiveTabs.currentIndex())
        name = self.current_sortmodel.data(selmod[0], Qt.DisplayRole)
        off = self.current_sortmodel.data(selmod[1], Qt.DisplayRole)
        size = self.current_sortmodel.data(selmod[3], Qt.DisplayRole)

        menu = QMenu()
        menu.addAction(self.tr("Copy Offset"))
        menu.addAction(self.tr("Copy Name"))
        menu.addAction(self.tr("Import Archive"))
        menu.addAction(self.tr("Export Archive"))
        menu.addAction(self.tr("Open in IFF Editor"))

        res = menu.exec_(
            self.current_tableView.viewport().mapToGlobal(position))

        if not res:
            return

        if res.text() == 'Copy Offset':
            self.clipboard.setText(str(off))
            self.statusBar.showMessage('Copied ' + str(off) + ' to clipboard.')
        elif res.text() == 'Copy Name':
            self.clipboard.setText(str(name))
            self.statusBar.showMessage(
                'Copied ' + str(name) + ' to clipboard.')
        elif res.text() == 'Import Archive':
            print('Importing iff File over: ', name, off, size)

            location = QFileDialog.getOpenFileName(
                caption='Select .iff file', filter='*.iff')
            t = open(location[0], 'rb')
            k = t.read()  # store file temporarily
            t.close()

            # Create Scheduler Entry
            sched = SchedulerEntry()
            # Scheduler Props

            sched.name = name
            sched.selmod = 0
            sched.arch_name = self._active_file.split('\\')[-1]
            sched.subarch_name = name
            sched.subarch_offset = off
            sched.subarch_size = size
            sched.subfile_name = ''
            sched.subfile_off = 0
            sched.subfile_type = 'IFF'
            sched.subfile_index = 0
            sched.subfile_size = 0
            sched.local_off = 0
            sched.oldCompSize = size
            sched.oldDecompSize = size
            sched.newCompSize = len(k)
            sched.newDataSize = sched.newCompSize
            sched.chksm = zlib.crc32(k)
            sched.diff = sched.newCompSize - sched.oldCompSize

            self.addToScheduler(sched, k)  # Add to Scheduler

        elif res.text() == 'Export Archive':
            location = QFileDialog.getSaveFileName(
                caption="Save File", dir=name, filter='*.iff')
            t = open(location[0], 'wb')
            f = open(self._active_file, 'rb')
            # Explicitly handle ogg files
            if 'wav' in name:
                f.seek(off + 0x2C)
            else:
                f.seek(off)
            t.write(f.read(size))
            f.close()
            t.close()
            self.statusBar.showMessage(
                'Exported .iff to : ' + str(location[0]))

    def test(self, rowMid):  # Sub Archive Reader
        # Check if Comments Section was Clicked
        if rowMid.column() == 4:
            self.tableview_edit_start(rowMid)
            return
        ''' THIS IS THE FUNCTION THAT PARSES THE SELECTED
            SUBARCHIVE AFTER CLICK ON THE MAIN TABLEVIEW '''
        selmod = self.current_tableView.selectionModel().selectedIndexes()
        '''Check Current Index'''
        if self.current_tableView_index == selmod[0].row():
            return
        arch_name = self.archiveTabs.tabText(self.archiveTabs.currentIndex())
        name = self.current_sortmodel.data(selmod[0], Qt.DisplayRole)
        off = self.current_sortmodel.data(selmod[1], Qt.DisplayRole)
        size = self.current_sortmodel.data(selmod[3], Qt.DisplayRole)

        if arch_name not in self._active_file:  # File not already opened
            try:
                if isinstance(self._active_file_handle, file):
                    self._active_file_handle.close()
                self._active_file = self.mainDirectory + os.sep +\
                    arch_name  # Get the New arhive file path
                self._active_file_handle = open(
                    self._active_file, 'rb')  # Opening File
            except:
                msgbox = QMessageBox()
                msgbox.setText(
                    "File Not Found\n Make sure you have selected the correct NBA 2K15 Installation Path")
                msgbox.exec_()
                return

        '''PARSING START'''
        self._active_file_handle.seek(off)
        t = StringIO()
        t.write(self._active_file_handle.read(size))
        t.seek(0)
        self._active_file_data = t

        print('Searching in : ', self._active_file)
        print('Handle Path : ', self._active_file_handle.name)

        gc.collect()

        '''Check for audio files'''
        if '.wav' in name:
            # Get to proper Offset
            self._active_file_data.seek(0x2C)
            t = open('temp.ogg', 'wb')
            t.write(self._active_file_data.read())
            t.close()
            self.sound_player.Stop()
            self.sound_player.OpenFile('temp.ogg')
            return

        ''' CALLING archive_parser TO PARSE THE SUBARCHIVE '''
        ''' LOC CONTAINS A FILE LIST WITH ALL THE SUBFILES DATA'''
        loc = archive_parser(self._active_file_data)
        if isinstance(loc, dataInitiate):
            # Answering Data Delivery Request
            # Getting the Data
            self._active_file_data.close()  # Closing the file
            self._active_file_handle.seek(off)  # Big archive already open
            t = StringIO()
            t.write(self._active_file_handle.read(loc.datalen))
            t.seek(0)
            self._active_file_data = t
            # Call archive parser again
            loc = archive_parser(self._active_file_data)

        '''self.file_list IS THE TREEMODEL THAT CONTAINS ALL THE
            FILES CONTAINED IN THE SUBARCHIVE'''
        self.file_list = SortModel()
        self.file_listModel = TreeModel(
            ("Name", "Offset", "Comp. Size", "Decomp. Size", "Type"))
        self.file_list.setSourceModel(self.file_listModel)

        # self.treeView_2.header().setResizeMode(QHeaderView.ResizeToContents)
        # self.treeView_2.header().setResizeMode(QHeaderView.Interactive)

        gc.collect()
        parent = self.file_listModel.rootItem
        for i in loc:
            # print(i)
            item = TreeItem(i, parent)
            parent.appendChild(item)

        self.treeView_2.setModel(self.file_list)  # Update the treeview
        self.treeView_2.setSortingEnabled(True)  # enable sorting
        self.treeView_2.sortByColumn(
            1, Qt.SortOrder.AscendingOrder)  # sort by offset
        self.current_tableView_index = selmod[0].row()
        # Open File into the iff editor
        print 'Opening File in Iff Editor'
        self._active_file_data.seek(0)
        self.iffEditorWindow._file = self._active_file_data
        self.iffEditorWindow._fileProps.name = name
        self.iffEditorWindow.openFileData()
        self.iffEditorWindow.show()

    def open_file_table(self):
        ''' FUNCTION THAT INITIATES THE FILE ARCHIVES LOADING
            ACTUAL PARSING IS DONE BY load_archive_database_tableview '''
        # Delete Current Tabs
        while self.archiveTabs.count():

            widg = self.archiveTabs.widget(self.archiveTabs.currentIndex())
            self.archiveTabs.removeTab(self.archiveTabs.currentIndex())
            try:
                widg.deleteLater()
            except:
                pass

        gc.collect()
        # update mainDirectory
        self.mainDirectory = self.pref_window.mainDirectory
        file_name = self.mainDirectory + os.sep + '0A'
        print(self.mainDirectory, file_name)

        self._active_file = file_name  # set active file to 0A file
        self._0Afile = file_name
        self._active_file_handle = open(self._active_file, 'rb')

        self.statusBar.showMessage('Getting archives...')
        self.fill_archive_names()  # Fill Archive Names
        self.fill_archive_list()  # Fill Archive List

        try:
            pass
            num = self.load_archive_database_tableview()
            # Store file offsets
            # for arch in self.list:
            #     arch_name=arch[0]
            #     f=open(str(arch_name)+'.txt','w')
            #     f.write(' '.join(['Name','Offset','Size'])+'\n')
            #     for entry in arch[3]:
            #         f.write(' '.join([str(entry[0]),str(entry[1]),str(entry[3])])+'\n')
            #     f.close()
        except:
            msgbox = QMessageBox()
            msgbox.setText(
                "File Not Found\n Make sure you have selected the correct NBA 2K15 Installation Path")
            msgbox.exec_()
            return

        # self.main_viewer_model=MyTableModel()

        '''SETUP SECONDARY BOTTOM-LEFT TABLEVIEW'''
        self.file_list = SortModel()
        self.file_listModel = TreeModel(
            ("Name", "Offset", "Comp. Size", "Decomp. Size", "Type"))
        self.file_list.setSourceModel(self.file_listModel)
        self.treeView_2.setModel(self.file_list)  # Update the treeview
        print "Swapping Columns"
        self.treeView_2.header().swapSections(3, 4)
        self.treeView_2.header().swapSections(2, 3)

        self.treeView_2.header().setResizeMode(QHeaderView.Interactive)
        self.statusBar.showMessage(str(num) + ' archives detected.')
        gc.collect()

    def close_app(self):
        sys.exit(0)

    def fill_archive_names(self):
        file_name = self.mainDirectory + os.sep + 'manifest'
        f = open(file_name, 'r')
        for line in f.readlines():
            archname = line.split('\t')[0]
            split = line.split('\t')[1].lstrip().split(' ')
            name = split[0]
            offset = int(split[1])
            if archname not in self.list_names.keys():
                self.list_names[archname] = {}
            self.list_names[archname][offset] = name
        f.close()

    def fill_archive_list(self):
        f = self._active_file_handle
        f.seek(16)
        count_0 = struct.unpack('<I', f.read(4))[0]
        f.seek(12, 1)
        count_1 = struct.unpack('<I', f.read(4))[0]
        f.seek(12, 1)
        s = 0
        print('Counts: ', count_0, count_1)
        self.list = []
        for i in range(count_0):
            size = struct.unpack('<Q', f.read(8))[0]
            f.read(8)
            name = read_string_1(f)
            f.read(13 + 16)
            # print(name,hex(size),f.tell())
            # self.main_list.append(None,(name,s))
            self.list.append((name, s, size, []))
            print(name, s, size)
            archiveOffsets_list.append(s)
            s += size

        archiveOffsets_list.append(s)

        print('Total Size: ', s)
        # Store archives data
        self.t = StringIO()
        self.t.write(f.read(0x18 * count_1))

        # Split worker jobs

        work_length = 50000
        work_last_length = count_1 % work_length
        work_count = count_1 // work_length

        # Call workers
        t0 = time.clock()
        threads = []
        subarch_id = 0  # keep the subarchive id
        for i in range(work_count):
            print('Starting Thread: ', i)
            self.t.seek(i * work_length * 0x18)
            data = StringIO()
            data.write(self.t.read(0x18 * work_length))
            # thread=threading.Thread(target=self.worker,args=(data,work_length,count_0,))
            thread = threading.Thread(
                target=self.worker, args=(data, work_length, count_0, subarch_id,))
            thread.start()
            threads.append(thread)
            subarch_id += work_length
        for i in range(work_count):
            threads[i].join()

        # last worker
        self.t.seek(work_count * work_length * 0x18)
        data = StringIO()
        data.write(self.t.read(0x18 * work_last_length))
        thread = threading.Thread(
            target=self.worker, args=(data, work_last_length, count_0, subarch_id,))
        thread.start()
        thread.join()

        print('Finished working. Total Time Elapsed: ', time.clock() - t0)

    def load_archive_database_tableview(self):
        ''' PARSING SETTINGS, IDENTIFYING WHICH ARCHIVE FILES TO READ
            AND SETUP THE MAIN TOP-LEFT TABLEVIEW '''
        # Create Tabs according to the Settings
        print('Parsing Settings')
        settings = self.pref_window.pref_window_buttonGroup
        selected_archives = []
        for child in settings.children():
            if isinstance(child, QCheckBox):
                if child.isChecked():
                    selected_archives.append(
                        archiveName_dict[child.text().split(' ')[0]])

        count = 0
        print('Creating ', len(selected_archives), ' Tabs')
        for i in selected_archives:
            # Create TableViewModel
            entry = self.list[i]
            sortmodel = MyTableModel(
                entry[3], ["Name", "Offset", "Type", "Size", "Comments"])
            # Create the TableView and Assign Options
            table_view = MyTableView()
            table_view.setModel(sortmodel)
            table_view.horizontalHeader().setResizeMode(QHeaderView.Interactive)
            lid = table_view.horizontalHeader().logicalIndex(0)
            table_view.horizontalHeader().resizeSection(lid, 900)
            lid = table_view.horizontalHeader().logicalIndex(1)
            table_view.horizontalHeader().resizeSection(lid, 75)
            lid = table_view.horizontalHeader().logicalIndex(3)
            table_view.horizontalHeader().resizeSection(lid, 60)
            table_view.horizontalHeader().setStretchLastSection(True)

            table_view.horizontalHeader().setMovable(True)

            table_view.setSortingEnabled(True)
            table_view.sortByColumn(1, Qt.AscendingOrder)
            table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_view.setSelectionMode(QAbstractItemView.SingleSelection)
            table_view.setEditTriggers(QAbstractItemView.SelectedClicked)
            table_view.hideColumn(2)  # Type

            # Functions
            table_view.clicked.connect(self.test)
            # table_view.doubleClicked.connect(self.tableview_edit_start)
            # table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            table_view.customContextMenuRequested.connect(self.main_ctx_menu)

            count += len(entry[3])
            tabId = self.archiveTabs.addTab(table_view, entry[0])
            # Store the sortmodel handles
            self.main_viewer_sortmodels.append(sortmodel)
            # Debugging Testing Archive size
            size = 0
            for subentry in entry[3]:
                size += subentry[3]
            print('Estimated Archive %s size: %d' % (entry[0], size))

        return count

    def save_comments(self):
        print('Saving Comments')

        f = open('NBA2K16_archiveComments.txt', 'w')
        f.write('//NBA2K16 ARCHIVE COMMENTS\n')
        f.write('//Created by NBA2K16 Explorer v' + version + '\n')
        for i in range(self.archiveTabs.count()):
            fname = str(self.archiveTabs.tabText(i))  # Write the archive name
            f.write('//' + fname + '\n')
            tmodel = self.archiveTabs.widget(i).model()  # Get tableview model
            for entry in tmodel.mylist:
                if entry[4]:
                    f.write(
                        entry[0] + '\t' + str(entry[4]) + '\n')
        f.close()

    def parse_comments(self):
        print('Parsing Comments')
        try:
            f = open('NBA2K16_archiveComments.txt')
            for line in f.readlines():
                if not line.startswith('//'):
                    split = line.rstrip().split('\t')
                    print(split[0], split[1])
                    self.comments[split[0]] = split[1]
            f.close()
        except:
            print('No Comments File Exists')

    def tableview_edit_start(self, index):
        if index.column() == 4:
            self.current_tableView.edit(index)

    def worker(self, data, length, count_0, subarch_id):
        data.seek(0)
        # f=open('C:\\worker.txt','w')
        for i in range(length):
            sa = struct.unpack('<Q', data.read(8))[0]
            id0 = struct.unpack('<I', data.read(4))[0]
            sb = struct.unpack('<I', data.read(4))[0]
            id1 = struct.unpack('<Q', data.read(8))[0]
            # f.write(id1)
            for j in range(count_0 - 1, -1, -1):
                val = self.list[j][1]  # full archive calculated offset
                archname = self.list[j][0]
                if id1 >= val:
                    # self.main_list.append(it,('unknown_'+str(i),id1-val))
                    comm = ''
                    name = self.list_names[archname][id1]
                    if name in self.comments.keys():
                        comm = self.comments[name]  # Try to load comment
                    self.list[j][3].append(
                        [name, id1 - val, sb, sa, comm])
                    subarch_id += 1
                    break

    def open_subfile(self):
        selmod = self.treeView_3.selectionModel().selectedIndexes()[0].row()
        print(self.subfile.files)
        name, off, size, type = self.subfile.files[selmod]
        print('Opening ', name)
        t = self.subfile._get_file(selmod)  # getting file

        typecheck = struct.unpack('>I', t.read(4))[0]
        t.seek(0)
        try:
            type = type_dict[typecheck]
        except:
            # print(type)
            type = 'UNKNOWN'

        print(type)
        # binary files checking

    def fill_info_panel(self, info_dict):  # Not used anymore
        # setup info panel
        print('Clearing Information Panel')
        for entry in self.groupBox_3.layout().children():
            self.clearLayout(entry)
        print('Setting Up Information Panel')
        sub_layout = QFormLayout()
        for entry in info_dict:
            lab = QLabel()
            if not info_dict[entry]:
                lab.setText(
                    "<P><b><FONT COLOR='#000000' FONT SIZE = 4>" + str(entry) + "</b></P></br>")
            else:
                lab.setText(str(entry) + info_dict[entry])

            sub_layout.addWidget(lab)

        self.groupBox_3.layout().addLayout(sub_layout)
        gc.collect()

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())


app = QApplication(sys.argv)
form = MainWindow()
form.show()
app.exec_()
