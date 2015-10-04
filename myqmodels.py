from PySide.QtCore import *
from PySide.QtGui import *


from pygl_widgets import GLWidgetQ

import operator
import sys
import os
import gc
from StringIO import StringIO
from nba2k15commonvars import *
from parsing_functions import *
from json_parser import *
from dds import *


class ModelPanel(QDialog):

    def __init__(self):
        super(ModelPanel, self).__init__()

        self.mode = 0
        self.status = True
        self.resize(300, 100)
        self.setWindowTitle('Model Panel')
        main_layout = QVBoxLayout()

        hor_layout = QHBoxLayout()

        lab = QLabel()
        lab.setText('Select Model Mode')
        hor_layout.addWidget(lab)
        main_layout.addLayout(hor_layout)

        but_group = QButtonGroup()
        hor_layout = QVBoxLayout()

        but = QRadioButton()
        but.setText('Stadium Models')
        self.stadium_but = but

        but_group.addButton(but)
        hor_layout.addWidget(but)

        but = QRadioButton()
        but.setText('Rest Models')
        self.rest_but = but

        but_group.addButton(but)
        hor_layout.addWidget(but)

        main_layout.addLayout(hor_layout)

        hor_layout = QHBoxLayout()
        but = QPushButton()
        but.setText('Import')
        but.clicked.connect(self.changeMode)
        hor_layout.addWidget(but)

        but = QPushButton()
        but.setText('Cancel')
        but.clicked.connect(self.quit)
        hor_layout.addWidget(but)

        main_layout.addLayout(hor_layout)
        self.setLayout(main_layout)

    def changeMode(self):
        if self.stadium_but.isChecked():
            self.mode = 0
        else:
            self.mode = 1
        self.close()

    def quit(self):
        self.status = False
        self.close()


class ImportPanel(QDialog):
    img_type = ['DXT1', 'DXT3', 'DXT5', 'RGBA', 'DXT5_NM']
    nvidia_opts = ['-dxt1a', '-dxt3', '-dxt5', '-u8888', '-n5x5']
    mipMaps = [str(i + 1) for i in range(13)]

    def __init__(self):
        super(ImportPanel, self).__init__()
        self.CurrentImageType = self.nvidia_opts[0]
        self.CurrentMipmap = self.mipMaps[11]
        self.swizzleFlag = True
        self.ImportStatus = False
        self.initUI()

    def initUI(self):

        self.resize(250, 150)
        self.setWindowTitle('Texture Import Panel')
        main_layout = QVBoxLayout()

        sub_layout = QHBoxLayout()
        lab = QLabel()
        lab.setText('Texture Type')
        but = QComboBox()
        but.addItems(self.img_type)
        but.currentIndexChanged.connect(self.setImageType)
        sub_layout.addWidget(lab)
        sub_layout.addWidget(but)

        main_layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()
        lab = QLabel()
        lab.setText('Mipmaps')
        but = QComboBox()
        but.addItems(self.mipMaps)
        but.currentIndexChanged.connect(self.setMipmap)
        sub_layout.addWidget(lab)
        sub_layout.addWidget(but)

        main_layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()
        but = QCheckBox()
        but.setText('Swizzle')
        but.setChecked(True)
        but.stateChanged.connect(self.setSwizzleFlag)

        sub_layout.addWidget(but)
        main_layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()
        but = QPushButton()
        but.setText('Import')
        but.clicked.connect(self.imported_image)

        sub_layout.addWidget(but)
        main_layout.addLayout(sub_layout)

        self.setLayout(main_layout)

    def imported_image(self):
        self.ImportStatus = True
        self.hide()

    def setImageType(self, index):
        self.CurrentImageType = self.nvidia_opts[index]

    def setMipmap(self, index):
        self.CurrentMipmap = self.mipMaps[index]

    def setSwizzleFlag(self):
        self.swizzleFlag = not self.swizzleFlag


class AboutDialog(QWidget):

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(500, 200)
        layout = QVBoxLayout()
        # main label
        lab = QLabel()
        lab.setAlignment(Qt.AlignCenter)
        lab.setText(
            "<P><b><FONT COLOR='#000000' FONT SIZE = 5>NBA 2K15 Explorer v0.28</b></P></br>")
        layout.addWidget(lab)
        lab = QLabel()
        lab.setAlignment(Qt.AlignCenter)
        lab.setText(
            "<P><b><FONT COLOR='#000000' FONT SIZE = 2>Coded by: gregkwaste</b></P></br>")
        layout.addWidget(lab)

        # textbox
        tex = QTextBrowser()
        f = open("about.html")
        tex.setHtml(f.read())
        f.close()
        tex.setOpenExternalLinks(True)
        tex.setReadOnly(True)
        layout.addWidget(tex)

        self.setLayout(layout)


class IffEditorWindow(QMainWindow):

    def __init__(self, parent=None):
        super(IffEditorWindow, self).__init__(parent)
        self.setWindowTitle("NBA 2K16 - Iff Editor")

        # Window private properties
        self.archiveContents = MyTableModel([[]], [])

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(sizePolicy)

        centerwidget = QWidget(self)  # Define CenterWidget
        centerwidget.setSizePolicy(sizePolicy)

        mainlayout = QSplitter()  # Define Splitter
        mainlayout.setOrientation(Qt.Horizontal)

        # mainlayout=QHBoxLayout()
        self.glwidget = GLWidgetQ(self)
        self.glwidget.renderText(0.5, 0.5, "3dgamedevblog")
        mainlayout.addWidget(self.glwidget)  # Add GLWidget to the splitter

        vertlist = QSplitter()
        vertlist.setOrientation(Qt.Vertical)

        gbox = QGroupBox()
        gbox.setTitle('Archive Contents')
        vlayout = QVBoxLayout()

        self.archiveTable = MyTableView(parent=gbox)
        self.archiveTable.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.archiveTable.horizontalHeader().setMovable(True)
        self.archiveTable.setSortingEnabled(True)
        self.archiveTable.sortByColumn(1, Qt.AscendingOrder)
        self.archiveTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.archiveTable.setModel(self.archiveContents)
        # Functions
        self.archiveTable.customContextMenuRequested.connect(
            self.archiveTableCtxMenu)
        self.archiveTable.clicked.connect(self.read_subfile)
        # self.archiveTable.doubleClicked.connect(read_subfile)

        vlayout.addWidget(self.archiveTable)
        gbox.setLayout(vlayout)

        vertlist.addWidget(gbox)

        # Text Editor
        self.text_editor = QPlainTextEdit()

        # File Explorer
        self.file_explorer_model = MyTableModel([[]], [])
        self.file_explorer_view = MyTableView()
        self.file_explorer_view.horizontalHeader().setResizeMode(
            QHeaderView.Stretch)
        self.file_explorer_view.setModel(self.file_explorer_model)

        # Tools Tab Widget
        gbox = QGroupBox()
        gbox.setTitle('Tools')
        tabwidget = QTabWidget()
        tabwidget.addTab(self.file_explorer_view, 'File Explorer')
        tabwidget.addTab(self.text_editor, 'Text Editor')

        vlayout = QVBoxLayout()
        vlayout.addWidget(tabwidget)
        gbox.setLayout(vlayout)

        vertlist.addWidget(gbox)

        mainlayout.addWidget(vertlist)
        self.setCentralWidget(mainlayout)
        self.resize(1276, 700)

        # Configure Menu Bar
        self.menubar = QMenuBar(self)
        self.fileMenu = QMenu('File', parent=self.menubar)

        self.fileOpenAction = QAction(self)
        self.fileOpenAction.setText('Open File')
        self.fileOpenAction.triggered.connect(self.openFile)

        self.closeWindowAction = QAction(self)
        self.closeWindowAction.setText('Close')
        self.closeWindowAction.triggered.connect(self.closeWindow)

        self.fileMenu.addAction(self.fileOpenAction)
        self.fileMenu.addAction(self.closeWindowAction)

        self.menubar.addAction(self.fileMenu.menuAction())

        self.setMenuBar(self.menubar)

        # StatusBar
        self.statusBar = QStatusBar(self)
        self.statusBar.setStatusTip("Coded by gregkwaste Copyright 2015 (c)")
        self.statusBar.setSizeGripEnabled(True)
        self.statusBar.setObjectName("statusBar")
        self.setStatusBar(self.statusBar)

        # File and Data Handles
        self._file = None

        # TESTING SECTION
        self.openFile('png2468.iff')

    def openFile(self, name=None):
        # Close previously open file handle
        if self._file:
            self._file.close()
        # Try Opening File
        if not name:
            location = QFileDialog.getOpenFileName(
                caption='Select .iff file', filter='*.iff')
            if location:
                self._file = open(location[0], 'rb')
            else:
                print('Canceled')
                return
        else:
            print('Opening File', name)
            self._file = open(name, 'rb')

        # Add data to the Archive Contents Table
        self.archiveContents = MyTableModel(
            archive_parser(self._file),
            ['Name', 'Offset', 'Comp. Size', 'Decomp. Size', 'Type'])
        self.archiveTable.setModel(self.archiveContents)
        gc.collect()
        # print archive_parser(self._file)

    def closeWindow(self):
        print('Closing Window')
        self.close()

    def archiveTableCtxMenu(self, pos):
        print('Ctx Menu Triggered')
        selmod = self.archiveTable.selectionModel().selectedIndexes()

        if len(selmod) == 0:  # exit if there is nothing selected
            return

        menu = QMenu()
        menu.addAction(self.tr("Export"))
        if not len(selmod) > len(self.archiveContents.header):
            menu.addAction(self.tr("Import"))

        res = menu.exec_(self.archiveTable.viewport().mapToGlobal(pos))

        if not res:
            return

        if res.text() == 'Export':
            self.export_items(selmod)
        elif res.text() == 'Import':
            self.import_item(selmod)

    def export_items(self, selection):
        print('Exporting Items')
        row_num = len(selection) // 5
        # Get archive name
        arch_name = '_' + self._file.name

        selmod = self.archiveTable.selectionModel().selectedIndexes()

        selected_dir = QFileDialog.getExistingDirectory(
            caption="Choose Export Directory")

        if not selected_dir:
            return
        # Sort Selection with row id
        selection = sorted(selection, key=lambda s: s.row())

        for i in range(row_num):  # loop to each row
            f_name = self.archiveContents.data(
                selection[5 * i], Qt.DisplayRole)  # get file name
            off = self.archiveContents.data(
                selection[5 * i + 1], Qt.DisplayRole)  # get file offset
            typ = self.archiveContents.data(
                selection[5 * i + 4], Qt.DisplayRole)  # get file type
            size = self.archiveContents.data(
                selection[5 * i + 2], Qt.DisplayRole)  # get file size

            print(f_name, off, typ, size)

            if size == 0:
                continue

            f_name = os.path.join(
                selected_dir, arch_name, str(f_name))
            # f_name=selected_dir+'\\'+arch_name + '\\'+str(f_name)

            t = StringIO()  # open temporary memory stream
            self._file.seek(off)
            # write data to temporary file
            t.write(self._file.read(size))

            if typ == 'LZMA':
                print('Decompressing LZMA')
                t.seek(0x4)
                data = pylzma.decompress_compat(t.read())
                # print(struct.unpack('>I',data[0:4])[0])
            elif typ == 'OGG':
                t.seek(0)
                f_name += '.ogg'
                data = t.read()
            elif typ == 'ZLIB':
                t.seek(0x10)
                data = zlib.decompress(t.read())
                if struct.unpack('>I', data[0:4])[0] == 0x504B0304:
                    f_name += '.zip'
                elif struct.unpack('>I', data[0:4])[0] == 0x44445320:
                    f_name += '.dds'
                else:
                    f_name += 'xml'

            else:
                t.seek(0)
                data = t.read()

            if not os.path.exists(os.path.dirname(f_name)):
                os.makedirs(os.path.dirname(f_name))

            # writing the file to the selected directory
            k = open(f_name, 'wb')
            k.write(data)
            k.close()
            t.close()

            self.statusBar.showMessage(
                'File Exported in: ' + str(f_name))  # notify the user

    def import_items(self, selection):
        # Check for one one row selection only
        row = selmod[0].row()
        for i in selmod:
            if i.row() != row:
                msgbox = QMessageBox(
                    QMessageBox.Warning, 'Error',
                    "Import one file at a time", QMessageBox.Ok)
                msgbox.exec_()
                return
        # Import routine
        location = QFileDialog.getOpenFileName(
            caption="Select file for Import",
            filter='*.zip ;; *.ogg ;; *.*')
        if not location[0]:
            return
        print(location)

        t = open(location[0], 'rb')
        k = t.read()  # store file temporarily
        t.close()
        ''' OGG IMPORT '''
        if str(location[0]).split('.')[-1] == 'ogg' and subfile_type == 'OGG':
            print('importing ogg')
            # Storing container temporarily
            tempiff = StringIO()
            self._active_file_handle.seek(subarch_off)
            tempiff.write(self._active_file_handle.read(subarch_size))

            tempiff.seek(0x18)
            fixSize = struct.unpack('<I', tempiff.read(4))[0]
            oldDataSize = struct.unpack('<I', tempiff.read(4))[0]
            tempiff.seek(0x1C)
            tempiff.write(struct.pack('<I', len(k) + 8 - fixSize))

            # oldCompSize=0x2C+fixSize+oldDataSize-8
            oldCompSize = subarch_size
            print(
                'Calculated oldCompSize: ',
                0x2C + fixSize + oldDataSize - 8)
            print('Old Iff Size: ', subarch_size)

            newCompSize = 0x2C + len(k)
            print(oldCompSize, newCompSize)
            tempiff.seek(0x2C)  # seek to audio file start
            tempiff.write(k)  # write new ogg file data
            tempiff.seek(0)
            k = tempiff.read()  # store the whole iff again

            # Scheduler Entry
            sched = SchedulerEntry()
            # Scheduler Props

            sched.name = subarch_name
            sched.selmod = 0
            sched.arch_name = self._active_file.split('\\')[-1]
            sched.subarch_name = subarch_name
            sched.subarch_offset = subarch_off
            sched.subarch_size = subarch_size
            sched.subfile_name = ''
            sched.subfile_off = 0
            sched.subfile_type = 'IFF'
            sched.subfile_index = 0
            sched.subfile_size = 0
            sched.local_off = 0
            sched.oldCompSize = oldCompSize
            sched.oldDecompSize = oldCompSize
            sched.newCompSize = newCompSize
            sched.newDataSize = newCompSize
            sched.chksm = zlib.crc32(k)
            sched.diff = sched.newCompSize - sched.oldCompSize

            self.addToScheduler(sched, k)  # Add to Scheduler
        elif str(location[0]).split('.')[-1] == 'zip' and subfile_type == 'ZIP' or \
                str(location[0]).split('.')[-1] == 'gziplzma' and subfile_type == 'GZIP LZMA':

            print('Importing File')
            # Scheduler Entry
            sched = SchedulerEntry()
            # Scheduler Props

            sched.name = subarch_name
            sched.selmod = selmod
            sched.arch_name = self._active_file.split('\\')[-1]
            sched.subarch_name = subarch_name
            sched.subarch_offset = subarch_off
            sched.subarch_size = subarch_size

            sched.subfile_name = subfile_name
            sched.subfile_off = subfile_off
            sched.subfile_type = 'REPLACE'
            sched.subfile_index = subfile_index
            sched.subfile_size = subfile_size

            sched.local_off = 0
            sched.oldCompSize = subfile_size
            sched.oldDecompSize = subfile_size

            sched.newCompSize = len(k)
            sched.newDataSize = len(k)
            sched.chksm = zlib.crc32(k)
            sched.diff = sched.newCompSize - sched.oldCompSize

            self.addToScheduler(sched, k)  # Add to Scheduler

    def read_subfile(self, data):
        print('read_subfile function')
        selmod = self.archiveTable.selectionModel().selectedIndexes()
        name = self.archiveContents.data(selmod[0], Qt.DisplayRole)
        off = self.archiveContents.data(selmod[1], Qt.DisplayRole)
        comp_size = self.archiveContents.data(selmod[2], Qt.DisplayRole)
        decomp_size = self.archiveContents.data(selmod[3], Qt.DisplayRole)
        typ = self.archiveContents.data(selmod[4], Qt.DisplayRole)
        print(off, typ, comp_size, decomp_size)

        self._file.seek(off)
        data = StringIO()

        if typ == 'OGG':
            print('Loading OGG File')
            data.write(self._file.read(decomp_size))
            data.seek(0)
            # self.sound_player.player.clear() # Clearing the player before
            # writing the new file
            t = open('temp.ogg', 'wb')
            t.write(data.read())
            t.close()
            data.close()
            self.sound_player.Stop()
            self.sound_player.OpenFile('temp.ogg')
            return
        elif typ == 'LZMA':
            print('Loading LZMA File')
            data.write(self._file.read(comp_size))
            data.seek(0x4)
            k = StringIO()
            k.write(pylzma.decompress_compat(data.read()))
            data.close()
            k.seek(0)
            data = k
        else:
            print('No Compression')
            data.write(self._file.read(decomp_size))
            data.seek(0)

        # Open file
        ext = name.split('.')[-1]
        if ext == 'dds':
            print('Reading DDS File')
            image = dds_file(True, data)
            self.glwidget.texture_setup(image)

        elif ext == 'SCNE':
            txtdata = str(data.read())
            self.text_editor.clear()
            self.text_editor.setPlainText(txtdata)
            # Parsing Json in order to find out the correct model filename
            jsondata = NbaJsonParser(txtdata)
            # get binary file
            binaryname = jsondata['Model']['player']['Binary']
            print binaryname
            t = StringIO()  # Prepare binary file
            # Get binaryfiledata
            for row in self.archiveContents.mylist:
                if row[0] == binaryname:
                    off = row[1]
                    size = row[2]
                    typ = row[4]
                    print 'Model File data', off, size, typ
                    # Most of the times it will be LZMA
                    # I'm checking just in case
                    if typ == 'LZMA':
                        self._file.seek(off + 4)
                        temp = self._file.read(size - 4)
                        t.write(pylzma.decompress_compat(temp))
                        t.seek(0)
                    break
            self.glwidget.customModel(parseModel(jsondata, t))
            # modeldata = parseModel(dial.mode, data)
            # vc, tc = len(modeldata[0]), len(modeldata[1])
            # self.glwidget.customModel(modeldata)
            # print vc, tc

        elif ext in ['TXTR', 'RDAT']:
            '''TEXT FILES, PROBABLY JSONS'''
            if ext == 'RDAT':
                '''RDAT FILES HAVE A 0x10 BYTE HEADER ON START
                    ITS USELESS FOR NOW'''
                data.seek(0x10)
            self.text_editor.clear()
            txtdata = str(data.read())
            self.text_editor.setPlainText(txtdata)

        # try to parse over the extension
        if typ == 'UNKNOWN':
            if name.split('.')[-1] in ['json'] or name == 'xml_file':
                self.text_editor.clear()
                self.text_editor.setPlainText(str(data.read()))

        data.close()
        gc.collect()


class IffPanel(QWidget):

    def __init__(self, parent=None):
        super(IffPanel, self).__init__(parent)
        self.setWindowTitle("Iff Panel")
        self.setFixedSize(800, 600)


class PreferencesWindow(QDialog):

    def __init__(self, parent=None):
        super(PreferencesWindow, self).__init__(parent)
        self.setWindowTitle("Preferences")
        try:
            key = r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 370240'
            reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
            key = OpenKey(reg, key)
            val, typ = QueryValueEx(key, 'InstallLocation')
            self.mainDirectory = os.path.abspath(val)
        except:
            self.mainDirectory = 'C:\\'
        self.preferences_checkFile()
        # self.pref_window.resize(500,300)

        horizontal_layout = QGridLayout(self)
        hpos = 0
        vpos = 0
        for i in range(len(archiveName_list)):
            op_name = archiveName_list[i]
            button = QCheckBox(self)
            button.setText(op_name + archiveName_discr[i])
            button.setChecked(bool_dict[settings_dict[op_name]])
            horizontal_layout.addWidget(button, hpos, vpos)
            vpos += 1
            if vpos > 8:
                hpos += 1
                vpos = 0

        horizontal_layout_2 = QHBoxLayout()
        button = QPushButton()
        button.setText("Select All")
        button.clicked.connect(self.preferences_selectAll)
        horizontal_layout_2.addWidget(button)

        button = QPushButton()
        button.setText("Select None")
        button.clicked.connect(self.preferences_selectNone)
        horizontal_layout_2.addWidget(button)

        button = QPushButton()
        button.setText("Save Settings")
        button.clicked.connect(self.preferences_saveSettings)
        horizontal_layout_2.addWidget(button)

        horizontal_layout_3 = QHBoxLayout()
        lab = QLabel()
        lab.setText("Select NBA 2K15 Directory: ")
        horizontal_layout_3.addWidget(lab)

        settingsLineEdit = QLineEdit()
        settingsLineEdit.setText(self.mainDirectory)
        settingsLineEdit.setReadOnly(True)
        horizontal_layout_3.addWidget(settingsLineEdit)

        settingsPathButton = QPushButton()
        settingsPathButton.setText("Select")
        settingsPathButton.clicked.connect(self.preferences_loadDirectory)
        horizontal_layout_3.addWidget(settingsPathButton)

        settingsLabel = QLabel()
        settingsLabel.setText("Select Archives to Load")

        settingsGroupBox = QGroupBox()
        settingsGroupBox.setLayout(horizontal_layout)
        settingsGroupBox.setTitle("Archives")

        layout = QVBoxLayout(self)
        layout.addLayout(horizontal_layout_3)

        layout.addWidget(settingsLabel)
        layout.addWidget(settingsGroupBox)
        layout.addLayout(horizontal_layout_2)

        self.setLayout(layout)
        self.pref_window_buttonGroup = settingsGroupBox
        self.pref_window_Directory = settingsLineEdit

        # Preferences Window Functions
    def preferences_checkFile(self):
        # Try parsing Settings File
        try:
            sf = open('settings.ini', 'r')
            sf.readline()
            sf.readline()
            self.mainDirectory = sf.readline().split(' : ')[-1][:-1]
            print(self.mainDirectory)
            set = sf.readlines()
            for setting in set:
                settings_dict[setting.split(' : ')[0]] = setting.split(
                    ' : ')[1][:-1]
        except:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("Warning")
            msgbox.setText(
                "Settings file not found. Please set your preferences")
            msgbox.exec_()

    def preferences_selectAll(self):
        for child in self.pref_window_buttonGroup.children():
            if isinstance(child, QCheckBox):
                child.setChecked(True)

    def preferences_selectNone(self):
        for child in self.pref_window_buttonGroup.children():
            if isinstance(child, QCheckBox):
                child.setChecked(False)

    def preferences_saveSettings(self):
        f = open('settings.ini', 'w')
        f.writelines(('NBA 2K Explorer Settings File \n', 'Version 0.1 \n'))
        f.write('NBA 2K15 Path : ' + self.mainDirectory + '\n')
        for child in self.pref_window_buttonGroup.children():
            if isinstance(child, QCheckBox):
                f.write(
                    child.text().split(' ')[0] + ' : ' + str(child.isChecked()) + '\n')
        f.close()
        print('Settings Saved')

    def preferences_loadDirectory(self):
        selected_dir = QFileDialog.getExistingDirectory(
            caption="Choose Export Directory")
        self.pref_window_Directory.setText(selected_dir)
        self.mainDirectory = selected_dir


class TreeItem(object):

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeModel(QAbstractItemModel):
    progressTrigger = Signal(int)

    def __init__(self, columns, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(columns)
        # self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    # load list to viewer
    def setupModelData(self, data, parent, settings):
        print('Parsing Settings')
        selected_archives = []
        for child in settings.children():
            if isinstance(child, QCheckBox):
                if child.isChecked():
                    selected_archives.append(
                        archiveName_dict[child.text().split(' ')[0]])

        print(selected_archives)
        print('Setting up data')
        step = 0
        for i in selected_archives:
            step += len(data[i][3])
        step = float(step / 100)
        prog = 0
        count = 0
        for i in selected_archives:
            entry = data[i]
            arch_parent = TreeItem((entry[0], entry[1], entry[2]), parent)
            parent.appendChild(arch_parent)
            for kid in entry[3]:
                arch_parent.appendChild(
                    TreeItem((kid[0], int(kid[1]), int(kid[2]), kid[3]), arch_parent))
                if count > step:
                    prog += 1
                    self.progressTrigger.emit(prog)
                    QCoreApplication.sendPostedEvents()
                    count = 0
                else:
                    count += 1
        self.progressTrigger.emit(100)


class MyTableView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent=None)
        self.buttonDown = False
        self.button = None

    def keyPressEvent(self, event):
        '''Use the default fallback'''
        QTableView.keyPressEvent(self, event)

    def editorDestroyed(self, editor):
        print(editor)
        self.dataChanged()

    def mousePressEvent(self, event):
        # Select Clicked Row
        self.selectionModel().clear()
        row_id = self.indexAt(event.pos()).row()
        self.selectRow(row_id)
        # Set the button flags
        self.buttonDown = True
        self.button = event.button()

    def mouseMoveEvent(self, event):
        # Select Rows if button is down
        if self.buttonDown and self.button == Qt.MouseButton.LeftButton:
            row_mid = self.indexAt(event.pos())
            topright = self.model().index(row_mid.row(),
                                          len(self.model().header) - 1, QModelIndex())
            self.selectionModel().select(QItemSelection(row_mid, topright),
                                         QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def mouseReleaseEvent(self, event):
        row_id = self.indexAt(event.pos()).row()
        # Release button
        self.down = False
        self.button = None
        if event.button() == Qt.MouseButton.LeftButton and \
                len(self.selectionModel().selectedIndexes()) == len(self.model().header):
            '''Emit Clicked Signal'''
            self.clicked.emit(row_id)
        else:
            '''Handle Left Click Should Emit Ctx Request Signal'''
            self.customContextMenuRequested.emit(event.pos())


class MyTableModel(QAbstractTableModel):

    def __init__(self, mylist, header, *args):
        QAbstractTableModel.__init__(self, parent=None, *args)
        self.mylist = mylist
        self.header = header

    def rowCount(self, parent=None):
        return len(self.mylist)

    def columnCount(self, parent=None):
        return len(self.mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == Qt.EditRole:
            return self.mylist[index.row()][index.column()]
        elif role != Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]

    def setData(self, index, value, role=Qt.EditRole):
        self.mylist[index.row()][index.column()] = str(value)
        return True

    def flags(self, index):
        if index.column() == 4:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mylist = sorted(self.mylist,
                             key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.mylist.reverse()
        self.emit(SIGNAL("layoutChanged()"))

    def findlayer(self, name):
        """
        Find a layer in the model by it's name
        """
        for colId in range(self.columnCount()):
            startindex = self.index(0, colId)
            items = self.match(startindex, Qt.DisplayRole, name,
                               1, Qt.MatchExactly | Qt.MatchWrap | Qt.MatchContains)
            try:
                return items[0]
            except:
                continue
        return QModelIndex()


class SortModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(SortModel, self).__init__(parent)
        self.model = self.sourceModel()

    def lessThan(self, left, right):
        # print(left,right)
        leftData = self.sourceModel().data(left, self.sortRole())
        rightData = self.sourceModel().data(right, self.sortRole())

        try:
            return int(leftData) < int(rightData)
        except ValueError:
            return leftData < rightData

    def filterAcceptsRow(self, row_num, source_parent):
        ''' Overriding the parent function '''
        model = self.sourceModel()
        source_index = model.index(row_num, 0, source_parent)
        offset_index = model.index(row_num, 1, source_parent)

        if self.filterRegExp().pattern() in model.data(source_index, Qt.DisplayRole) or \
           self.filterRegExp().pattern() in str(model.data(offset_index, Qt.DisplayRole)):
            return True
        return False


app = QApplication(sys.argv)
form = IffEditorWindow()
form.show()
app.exec_()
