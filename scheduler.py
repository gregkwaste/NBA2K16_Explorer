class SchedulerEntry:

    def __init__(self):
        self.name = None
        self.selmod = None
        self.arch_name = None
        self.subarch_name = None
        self.subarch_offset = None
        self.subarch_size = None
        self.subfile_index = None
        self.subfile_name = None
        self.subfile_off = None
        self.subfile_type = None
        self.subfile_size = None
        self.local_off = None
        self.oldDecompSize = None
        self.newDataSize = None
        self.oldCompSize = None
        self.newCompSize = None
        self.chksm = None
        self.diff = None


def addToScheduler(self, sched, k):
    if not self.scheduler_model:
        self.scheduler_model = TreeModel(("Name", "ID", "Archive", "Subarchive Name", "Subarchive Offset", "Subarchive Size", "Subfile Index", "Subfile Name", "Subfile Offset", "Subfile Type",
                                          "Subfile Size", "Local File Offset", "Old Decompressed Size", "New Decompressed Size", "Old Compressed Size", "New Compressed Size", "CheckSum", "Diff"))
        gc.collect()
        self.scheduler.setModel(self.scheduler_model)

    parent = self.scheduler_model.rootItem
    item = TreeItem((sched.name, sched.selmod, sched.arch_name, sched.subarch_name, sched.subarch_offset,
                     sched.subarch_size, sched.subfile_index, sched.subfile_name, sched.subfile_off, sched.subfile_type,
                     sched.subfile_size, sched.local_off, sched.oldDecompSize, sched.newDataSize, sched.oldCompSize, sched.newCompSize,
                     sched.chksm, sched.diff), parent)
    parent.appendChild(item)

    self.schedulerFiles.append(k)


def scheduler_add_texture(self, im, fileName):
    # Get current selected file
    selmod = self.treeView_3.selectionModel().selectedIndexes()[0].row()
    name, off, oldCompSize, type = self.subfile.files[selmod]

    # Get archive Data
    parent_selmod = self.current_tableView.selectionModel(
    ).selectedIndexes()
    arch_name = self.archiveTabs.tabText(self.archiveTabs.currentIndex())
    subarch_name = self.current_sortmodel.data(
        parent_selmod[0], Qt.DisplayRole)
    subarch_offset = self.current_sortmodel.data(
        parent_selmod[1], Qt.DisplayRole)
    subarch_size = self.current_sortmodel.data(
        parent_selmod[3], Qt.DisplayRole)
    print(arch_name, subarch_offset, subarch_size)

    # Get Subfile Data
    parent_selmod = self.treeView_2.selectionModel().selectedIndexes()
    subfile_name = self.file_list.data(
        parent_selmod[0], Qt.DisplayRole)  # file name
    subfile_off = self.file_list.data(
        parent_selmod[1], Qt.DisplayRole)  # file offset
    subfile_type = self.file_list.data(
        parent_selmod[2], Qt.DisplayRole)  # file type
    subfile_size = self.file_list.data(
        parent_selmod[3], Qt.DisplayRole)  # file size
    # file index
    subfile_index = self.treeView_2.selectionModel().selectedIndexes()[
        0].row()
    chksm = 0

    if subfile_type == 'GZIP LZMA':  # override size for GZIP LZMA
        oldCompSize = subfile_size
        compOffset = 14

    print('Replacing File ', name, 'Size ', oldCompSize)
    t = self.subfile._get_file(selmod)

    if subfile_type == 'ZIP':
        local_off = off
        compOffset = 4
    else:
        local_off = 0

    compFlag = False  # flag for identifying dds files
    if not 'dds' in fileName:
        compFlag = True

    if 'dds' in name:
        # Getting Rest Image Data
        originalImage = dds_file(True, t)
        restDataLen = originalImage._get_rest_size()
        originalImage.data.seek(-restDataLen, 2)
        restData = originalImage.data.read()

        # Calculating Old Image Size
        oldDecompSize = originalImage._get_full_size() + restDataLen

    # Calculating New Image Size

    # Calling the Texture Importer panel
    # if not isinstance(im,dds_file):
    res = ImportPanel()
    res.exec_()

    if res.ImportStatus:  # User has pressed the Import Button
        # Compress the Texture
        comp = res.CurrentImageType
        nmips = res.CurrentMipmap

        # print(originalImage.header.dwMipMapCount,nmips)
        if compFlag:
            print('Converting Texture file')
            self.statusBar.showMessage('Compressing Image...')
            status = call(['./nvidia_tools/nvdxt.exe', '-file', str(fileName),
                           comp, '-nmips', nmips, '-quality_production', '-output', 'temp.dds'])
            f = open('temp.dds', 'rb')
        else:
            # working on an existing dds file
            f = open(fileName, "rb")

        # writing temp.dds to an IO buffer, and fixing the dds header
        t = StringIO()
        t.write(f.read(11))

        if res.swizzleFlag:
            t.write(struct.pack('B', 128))  # writing flag for swizzled dds
            f.read(1)
        else:
            t.write(f.read(1))

        t.write(f.read(16))

        # Overriding Mipmap count when compressing image
        if compFlag:
            t.write(struct.pack('B', int(nmips)))  # writing mipmaps
            f.read(1)
        else:
            t.write(f.read(1))

        t.write(f.read())
        f.close()
        t.seek(0)
        res.destroy()
    else:
        res.destroy()
        self.statusBar.showMessage('Import Canceled')
        return

    #f = open('testing.dds', 'wb')
    # f.write(t.read())
    # f.close()
    t.seek(0)

    f = dds_file(True, t)
    if res.swizzleFlag:
        print('Swizzling Texture')
        f.swizzle_2k()
    t = f.write_texture()

    newData = t.read()

    newData += restData
    newDataSize = len(newData)
    chksm = zlib.crc32(newData) & 0xFFFFFFFF  # calculate Checksum

    k = pylzma.compress(newData, 24)  # use 16777216 bits dictionary
    k = k + k[0:len(k) // 4]  # inflating file
    #comp_f = open('test.dat', 'wb')
    # comp_f.write(k)
    # comp_f.close()
    newCompSize = len(k)

    diff = newCompSize + compOffset - oldCompSize

    print('OldDecompSize: ', oldDecompSize, 'NewDecompSize: ', newDataSize)
    print('OldCompSize: ', oldCompSize,
          'NewCompSize: ', newCompSize, 'Diff: ', diff)

    # Calculate New Image Size

    # Add item to the scheduler
    if not self.scheduler_model:
        self.scheduler_model = TreeModel(("Name", "ID", "Archive", "Subarchive Name", "Subarchive Offset", "Subarchive Size", "Subfile Index", "Subfile Name", "Subfile Offset", "Subfile Type",
                                          "Subfile Size", "Local File Offset", "Old Decompressed Size", "New Decompressed Size", "Old Compressed Size", "New Compressed Size", "CheckSum", "Diff"))

    gc.collect()
    parent = self.scheduler_model.rootItem
    item = TreeItem((name, selmod, arch_name, subarch_name, subarch_offset, subarch_size, subfile_index, subfile_name, subfile_off,
                     subfile_type, subfile_size, local_off, oldDecompSize, newDataSize, oldCompSize, newCompSize, chksm, diff), parent)
    parent.appendChild(item)
    self.scheduler.setModel(self.scheduler_model)
    self.schedulerFiles.append(k)
    self.statusBar.showMessage('Texture Added to Import Schedule')


def scheduler_add_model(self, tfile):
    # Get current selected file
    selmod = self.treeView_3.selectionModel().selectedIndexes()[0].row()
    name, off, oldCompSize, type = self.subfile.files[selmod]

    # Get archive Data
    parent_selmod = self.current_tableView.selectionModel(
    ).selectedIndexes()
    arch_name = self.archiveTabs.tabText(self.archiveTabs.currentIndex())
    subarch_name = self.current_sortmodel.data(
        parent_selmod[0], Qt.DisplayRole)
    subarch_offset = self.current_sortmodel.data(
        parent_selmod[1], Qt.DisplayRole)
    subarch_size = self.current_sortmodel.data(
        parent_selmod[3], Qt.DisplayRole)
    print(arch_name, subarch_offset, subarch_size)

    # Get Subfile Data
    parent_selmod = self.treeView_2.selectionModel().selectedIndexes()
    subfile_name = self.file_list.data(
        parent_selmod[0], Qt.DisplayRole)  # file name
    subfile_off = self.file_list.data(
        parent_selmod[1], Qt.DisplayRole)  # file offset
    subfile_type = self.file_list.data(
        parent_selmod[2], Qt.DisplayRole)  # file type
    subfile_size = self.file_list.data(
        parent_selmod[3], Qt.DisplayRole)  # file size
    # file index
    subfile_index = self.treeView_2.selectionModel().selectedIndexes()[
        0].row()
    chksm = 0

    if subfile_type == 'GZIP LZMA':  # override size for GZIP LZMA
        oldCompSize = subfile_size
        compOffset = 14

    print('Replacing File ', name, 'Size ', oldCompSize)

    if subfile_type == 'ZIP':
        local_off = off
        compOffset = 4
    else:
        local_off = 0

    tfile.seek(0)
    newData = tfile.read()
    tfile.close()
    newDataSize = len(newData)
    chksm = zlib.crc32(newData) & 0xFFFFFFFF  # calculate Checksum

    # use 16777216 bits dictionary
    k = pylzma.compress(newData, dictionary=24, eos=0)
    k += b'\x00'
    # k=k+k[0:len(k)//4] #inflating file
    #comp_f = open('test.dat', 'wb')
    # comp_f.write(k)
    # comp_f.close()
    newCompSize = len(k)

    diff = newCompSize + compOffset - oldCompSize

    print('OldDecompSize: ', subfile_size, 'NewDecompSize: ', newDataSize)
    print('OldCompSize: ', oldCompSize,
          'NewCompSize: ', newCompSize, 'Diff: ', diff)

    # Add model to Scheduler
    sched = SchedulerEntry()

    sched.name = name
    sched.selmod = selmod
    sched.arch_name = arch_name

    sched.subarch_name = subarch_name
    sched.subarch_offset = subarch_offset
    sched.subarch_size = subarch_size

    sched.subfile_name = subfile_name
    sched.subfile_off = subfile_off
    sched.subfile_type = subfile_type
    sched.subfile_index = subfile_index
    sched.subfile_size = subfile_size

    sched.local_off = local_off
    sched.oldCompSize = oldCompSize
    sched.oldDecompSize = subfile_size
    sched.newCompSize = newCompSize
    sched.newDataSize = newDataSize
    sched.chksm = chksm
    sched.diff = diff

    self.addToScheduler(sched, k)  # Add to Scheduler
    self.statusBar.showMessage('Model Added to Import Scheduler')


def runScheduler(self):
    parent = self.scheduler_model.rootItem
    rowCount = parent.childCount()
    # print(rowCount)

    for i in range(rowCount):
        item = parent.child(i)
        name, selmod, arch_name, subarch_name, subarch_offset, subarch_size, subfile_index, subfile_name, subfile_off, subfile_type, subfile_size, local_off, oldDecompSize, newDataSize, oldCompSize, newCompSize, chksm, diff = item.data(0), item.data(
            1), item.data(2), item.data(3), item.data(4), item.data(5), item.data(6), item.data(7), item.data(8), item.data(9), item.data(10), item.data(11), item.data(12), item.data(13), item.data(14), item.data(15), item.data(16), item.data(17)

        self._active_file_handle.close()  # Close opened files
        if not arch_name in self._active_file:  # check archive name
            self._active_file = self.mainDirectory + '\\' + arch_name

        f = open(self._active_file, 'r+b')  # open big archive
        f.seek(subarch_offset)  # seek to iff offset
        t = StringIO()  # buffer for iff storage
        t.write(f.read(subarch_size))  # store iff file
        t.seek(0)

        # f.seek(subfile_off,1) #seek to subfile offset
        # f.seek(local_off,1) #seek to local zip offset

        t.seek(subfile_off + local_off)
        iffFlag = False
        compOffset = 0
        print(subfile_type)
        if subfile_type == 'ZIP':
            compOffset = 4
            # t.seek(4,1) #seek to the lzma offset
        elif subfile_type == 'GZIP LZMA':
            print('GZIP LZMA')
            compOffset = 14
            # t.seek(14,1) #seek to the raw gzip offset
        elif subfile_type == 'REPLACE':
            print('Replacing File')
            compOffset = 0
        elif subfile_type == 'IFF':
            print('Importing IFF')
            iffFlag = True
        t.seek(compOffset, 1)

        if diff <= 0:
            print('Enough Space for File')
            t.write(self.schedulerFiles[i])  # enough space for writing

            # t.seek(0)
            #k = open('temp.iff', 'wb')
            # k.write(t.read())
            # k.close()

            t.seek(0)
            # Writing iff back to full archive
            f.seek(subarch_offset)
            f.write(t.read())
            t.close()
            f.close()
        else:
            if not iffFlag:
                # writing File to archive
                # diff+=compOffset
                t.seek(oldCompSize - compOffset, 1)
                tail = StringIO()
                tail.write(t.read())  # bytes after the file
                tail.seek(0)
                print('tail size: ', len(tail.read()))
                tail.seek(0)

                if subfile_type == 'ZIP':
                    t.seek(subfile_off + local_off)
                    t.seek(-len(name) - 4 - 8 - 4, 1)
                    print(chksm)
                    t.write(struct.pack('<I', chksm))
                    t.write(struct.pack('<I', newCompSize + 0x4))
                    t.write(struct.pack('<I', newDataSize))

                    # seeking for appropriate info header
                    sub_file._get_zip_info_offset(selmod, tail)
                    print(tail.tell())
                    tail.write(struct.pack('<I', chksm))
                    tail.write(struct.pack('<I', newCompSize + 0x4))
                    tail.write(struct.pack('<I', newDataSize))
                    # seeking for end of central directory
                    tail.seek(0)
                    sub_file._get_zip_end_offset(tail)
                    print(tail.tell())
                    s = struct.unpack('<I', tail.read(4))[0]
                    tail.seek(-4, 1)
                    tail.write(struct.pack('<I', s + diff))

                    tail.seek(0)

                t.seek(subfile_off + local_off + compOffset)
                t.write(self.schedulerFiles[i])
                t.write(tail.read())
                tail.close()

                # Fix IFF Header
                t.seek(0)  # seek to iff start
                t.seek(8, 1)  # Skip magic and descr sec size
                s = struct.unpack('>I', t.read(4))[0]
                t.seek(-4, 1)
                t.write(struct.pack('>I', s + diff))

                t.seek(0)  # seek to iff start
                head = header(t)
                head.x38headers[0].size += diff
                head.x38headers[0].stop += diff
                t.seek(head.x38headersOffset)
                head.x38headers[0].write(t)

                # next headers
                t.seek(head.x38headersOffset + 0x38)
                for i in range(len(head.x38headers) - 1):
                    x38head = head.x38headers[i + 1]
                    x38head.start += diff
                    x38head.write(t)

                # Try automatically index calculation
                print('Old subfile index', subfile_index)
                subfile_index = int(
                    subfile_name.split('_')[1]) + int(subfile_name.split('_')[3])
                print('New calculated index', subfile_index)

                # i have to tweak all the next offsets
                for i in range(subfile_index + 1, len(head.sub_heads_data[0])):
                    print('Changing offset in file: ', i)
                    print('Seeking to: ', head.sub_heads_data[0][i])
                    t.seek(head.sub_heads_data[0][i])
                    fe = file_entry(t)
                    if not fe.type == 3:
                        t.seek(fe.off + 16)
                        s = struct.unpack('<Q', t.read(8))[0]
                        t.seek(-8, 1)
                        t.write(struct.pack('<Q', s + diff))

                t.seek(0)
                #k = open('temp.iff', 'wb')
                # k.write(t.read())
                # k.close()
            else:
                # writing full imported iff file
                t = StringIO()
                t.write(self.schedulerFiles[i])

            # Append iff into the big archive
            f.seek(subarch_offset + subarch_size)
            # tail=f.read()
            tailPath = self.mainDirectory + os.sep + 'tail'
            tail = open(tailPath, 'wb')
            # tailSize=os.fstat(tail.fileno()).st_size
            buf = 1
            while buf:
                buf = f.read(1024 * 1024 * 1024)
                print(len(buf))
                tail.write(buf)
            tail.close()
            print("Done Writing tail - TESTING")

            # Write actual data to archive
            f.seek(subarch_offset)
            t.seek(0)
            f.write(t.read())
            t.close()

            print("Writing back tail to big archive - TESTING")
            # Writing back the tail
            tail = open(tailPath, 'rb')
            buf = 1
            while buf:
                buf = tail.read(1024 * 1024 * 1024)
                f.write(buf)
            tail.close()
            os.remove(tailPath)  # Delete Tail File
            f.close()

            # diff-=compOffset #restore diff
            # Updating 0A database
            f = open(self.mainDirectory + '\\' + '0A', 'r+b')
            f.read(0x10)
            arch_num = struct.unpack('<I', f.read(4))[0]
            f.read(0xC)
            file_count = struct.unpack('<I', f.read(4))[0]
            f.read(0xC)
            # seeking to archive definition position
            f.seek(archiveName_dict[arch_name] * 0x30, 1)
            s = struct.unpack('<Q', f.read(8))[0]
            f.seek(-8, 1)
            print('Writing ' + str(arch_name) + ' size to ', str(f.tell()))
            f.write(struct.pack('<Q', s + diff))

            f.seek((arch_num + 1) * 0x30)  # seeking to archive definitions
            data_off = f.tell()  # store the data offset

            # get global file id
            subarch_id = int(subarch_name.split('_')[-1])
            f.seek(subarch_id * 0x18, 1)
            print('Found subarchive entry in ', f.tell())
            s = struct.unpack('<Q', f.read(8))[0]
            f.seek(-8, 1)
            f.write(struct.pack('<Q', s + diff))  # update its size
            f.seek(8, 1)
            sub_arch_full_offset = struct.unpack('<Q', f.read(8))[0]

            # Update next file offsets

            for arch in self.list:
                print('Seeking in: ', arch[0], arch[1], arch[2])
                for subarch in arch[3]:
                    # find all siblings with larger offset
                    test_val = subarch[1] + arch[1]
                    if test_val > sub_arch_full_offset:
                        subarch_name = subarch[0]
                        subarch_id = int(subarch_name.split('_')[-1])
                        f.seek(data_off + subarch_id * 0x18)
                        f.seek(8 + 4 + 4, 1)
                        s = struct.unpack('<Q', f.read(8))[0]
                        f.seek(-8, 1)
                        f.write(struct.pack('<Q', s + diff))

            f.close()

        self.schedulerFiles.pop()
        print('Scheduled Files left', len(self.schedulerFiles))
        # self.scheduler_model.removeRows(i,1)
        self.scheduler.setModel(None)
        self.scheduler_model.rootItem.childItems.pop()
        self.scheduler.setModel(self.scheduler_model)
        gc.collect()
        self.statusBar.showMessage('Import Completed')
        self.open_file_table()  # reload archives
