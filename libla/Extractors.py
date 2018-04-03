import os
import pytsk3
import logging
import tempfile

class UsnExtractor(object):
    def __init__(self, source_path, tsk_file, file_info, temp_dir):
        self.source_path = source_path
        self.tsk_file = tsk_file
        self.file_info = file_info

        self.temp_file_io = tempfile.NamedTemporaryFile(
            delete=False, dir=temp_dir
        )
        self.temp_file_name = self.temp_file_io.name
        self.cluster_size = tsk_file.info.fs_info.block_size

    def write_file(self):
        offset = 0
        size = self.file_info.size
        BUFF_SIZE = 1024 * 1024

        # for the journal, we need to skip the sparse data
        # iterate through the attributes till we get the correct one.
        for attr in self.tsk_file:
            if attr.info.id == self.file_info.id:
                for run in attr:
                    if run.flags == pytsk3.TSK_FS_ATTR_RUN_FLAG_SPARSE:
                        logging.debug(u"USN Extractor: Skipping {} sparse bytes.".format(run.len))
                        offset += run.len * self.cluster_size
                    else:
                        break

        while offset < size:
            available_to_read = min(BUFF_SIZE, size - offset)
            data = self.tsk_file.read_random(
                offset, available_to_read,
                self.file_info.type, self.file_info.id
            )
            if not data:
                break

            offset += len(data)
            self.temp_file_io.write(data)

        self.temp_file_io.close()
        logging.debug(u"{} -> {}".format(self.source_path, self.temp_file_io.name))

    def get_temp_name(self):
        return self.temp_file_name

    def __del__(self):
        os.remove(self.temp_file_name)
        logging.debug(u"File removed: {}".format(self.temp_file_name))


class RegularExtractor(object):
    def __init__(self, source_path, tsk_file, file_info, temp_dir):
        self.source_path = source_path
        self.tsk_file = tsk_file
        self.file_info = file_info

        _other, extension = os.path.splitext(self.source_path)

        self.temp_file_io = tempfile.NamedTemporaryFile(
            delete=False, dir=temp_dir, suffix=extension
        )
        self.temp_file_name = self.temp_file_io.name

    def write_file(self):
        offset = 0
        size = self.file_info.size
        BUFF_SIZE = 1024 * 1024

        while offset < size:
            available_to_read = min(BUFF_SIZE, size - offset)
            data = self.tsk_file.read_random(
                offset, available_to_read,
                self.file_info.type, self.file_info.id
            )
            if not data:
                break

            offset += len(data)
            self.temp_file_io.write(data)

        self.temp_file_io.close()
        logging.debug(u"{} -> {}".format(self.source_path, self.temp_file_io.name))

    def get_temp_name(self):
        return self.temp_file_name

    def __del__(self):
        os.remove(self.temp_file_name)
        logging.debug(u"File removed: {}".format(self.temp_file_name))
