import os
import pytsk3
import logging


class FileInfo(object):
    def __init__(self, fullname, attribute):
        self.fullname = fullname
        self.filename = attribute.info.fs_file.name.name.decode('utf-8')
        self.id = attribute.info.id
        self.type = attribute.info.type
        self.size = attribute.info.size

        self.attribute_name = None
        if attribute.info.name:
            self.attribute_name = attribute.info.name.decode('utf-8')


class LogicalEnumerator(object):
    """A class to process the logical volume."""
    def __init__(self, file_io, handler_mapping, arango_handler, temp_dir, description=u""):
        """Create LogicalEnumerator

        Params:
            file_io (FileIO): I file like object representing a volume.
            handler_mapping (ArtifactMapping): The artifact mapping that determines file operations
            arango_handler (ArangoHandler): The handler for inserting documents into ArangoDB
            temp_dir (unicode): The location to extract files to
            description (unicode): The label for this LogicalEnumerator
        """
        self.file_io = file_io
        self.handler_mapping = handler_mapping
        self.arango_handler = arango_handler
        self.temp_dir = temp_dir
        self.description = description
        self.tsk_fs = pytsk3.FS_Info(
            self.file_io
        )
        self._insure_temp_dir()

    def _insure_temp_dir(self):
        """Make sure the temp dir exists."""
        if not os.path.isdir(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _iter_directory(self, tsk_dir, stack=[]):
        """Iterate a directory looking for file entries.

        Params:
            tsk_dir: TSK File as a directory
            stack: A list of path names that gives the full path
        """
        for tsk_file in tsk_dir:
            filename = tsk_file.info.name.name.decode('utf-8')

            if filename in [u".", u".."]:
                continue

            if hasattr(tsk_file.info, 'meta'):
                if hasattr(tsk_file.info.meta, 'type'):
                    is_dir = tsk_file.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR
                else:
                    logging.debug(u"not sure how to handle here...")
                    continue
            else:
                logging.debug(u"not sure how to handle here...")
                continue

            if is_dir:
                stack.append(filename)
                self._iter_directory(
                    tsk_file.as_directory(), stack=stack
                )
                stack.pop()
            else:
                self._process_entry(
                    tsk_file, u"/".join(stack)
                )

    def _process_entry(self, tsk_file, full_path):
        """Process a TSK File.

        Params:
            tsk_file (TSK File): A TSK File object
            full_path (unicode): The fullpath of this file object
        """
        filename = tsk_file.info.name.name.decode('utf-8')
        fullname = u"/".join([full_path, filename])

        for attr in tsk_file:
            if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
                if attr.info.name:
                    attr_name = attr.info.name.decode('utf-8')
                    source_path = u":".join([fullname, attr_name])
                else:
                    source_path = fullname

                file_info = FileInfo(
                    source_path, attr
                )

                for handler in self.handler_mapping.iter_handlers(file_info):
                    handler.run(
                        source_path,
                        tsk_file,
                        file_info,
                        self.arango_handler,
                        self.temp_dir
                    )

    def process_files(self, directory=u"/"):
        """Entry into processing all files for this LogicalEnumerator.

        Params:
            directory (unicode): The starting directory to recurse. (default is root)
        """
        tsk_dir = self.tsk_fs.open_dir(directory)
        self._iter_directory(
            tsk_dir, stack=[u"."]
        )
