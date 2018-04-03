import re
import yaml
import shlex
import logging
import subprocess
from libla.Extractors import RegularExtractor, UsnExtractor


class ArtifactMapping(object):
    def __init__(self):
        self._mapping = {}

    def set_handler(self, name, handler):
        self._mapping[name] = handler

    @staticmethod
    def from_file(filename):
        artifact_mapping = ArtifactMapping()
        with open(filename, u'rb') as fh:
            template = yaml.load(fh)
            handler_dict = template['Handlers']
            for handler_name, handler_dict in handler_dict.items():
                handler = ArtifactHandler.from_dict(
                    handler_name, handler_dict
                )
                artifact_mapping.set_handler(
                    handler_name, handler
                )

        return artifact_mapping

    def iter_handlers(self, file_info):
        for name, handler in self._mapping.items():
            if handler.matches(file_info):
                yield handler


class MatchFilter(object):
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value
        self.regexp = re.compile(self.value, flags=re.I)

    @staticmethod
    def from_dict(dictionary):
        return MatchFilter(**dictionary)

    def matches(self, file_info):
        attribute_value = getattr(file_info, self.attribute, None)
        if attribute_value is not None:
            if self.regexp.search(attribute_value):
                return True
        return False


class ArtifactHandler(object):
    def __init__(self, name, match, extractor, tool_cmd):
        self.name = name
        self.match = match
        self.extractor = extractor
        self.tool_cmd = tool_cmd

        if self.extractor == 'regular':
            self._extractor_class = RegularExtractor
        elif self.extractor == 'usn':
            self._extractor_class = UsnExtractor
        else:
            raise Exception(u"Unknown extractor type: {}".format(self.extractor))

    @staticmethod
    def from_dict(name, dictionary):
        match = MatchFilter.from_dict(
            dictionary['match']
        )
        return ArtifactHandler(
            name,
            match,
            dictionary['extractor'],
            dictionary['tool_cmd']
        )

    def matches(self, file_info):
        return self.match.matches(file_info)

    def run(self, source_path, tsk_file, file_info, arango_handler, temp_dir):
        logging.info(u"[starting] Processing: {}".format(source_path))

        extractor = self._extractor_class(
            source_path,
            tsk_file,
            file_info,
            temp_dir
        )
        extractor.write_file()

        temp_filename = extractor.get_temp_name()
        temp_filename = temp_filename.replace(u"\\", u"\\\\")

        arguments = self.tool_cmd.format(
            temp_filename
        )
        arguments = shlex.split(arguments)

        logging.debug(u"Command: {}".format(u" ".join(arguments)))

        output, error = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()

        if output:
            arango_handler.insert_jsonl(
                self.name,
                output
            )

        if error:
            logging.error(error)

        logging.info(u"[finished] Processing: {}".format(source_path))
