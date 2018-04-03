import yaml
import shlex
import logging
import subprocess


class LogicalToolManager(object):
    def __init__(self):
        self.handlers = []

    def set_handler(self, handler):
        self.handlers.append(handler)

    @staticmethod
    def from_file(filename):
        tool_manager = LogicalToolManager()
        with open(filename, u'rb') as fh:
            template = yaml.load(fh)
            handler_dict = template['Handlers']
            for handler_name, handler_dict in handler_dict.items():
                handler = LogicalToolHandler.from_dict(
                    handler_name, handler_dict
                )
                tool_manager.set_handler(
                    handler
                )

        return tool_manager

    def run(self, arango_handler, options):
        for handler in self.handlers:
            handler.run(arango_handler, options)


class LogicalToolHandler(object):
    def __init__(self, name, tool, parameters):
        self.name = name
        self.tool = tool
        self.parameters = parameters

    @staticmethod
    def from_dict(name, dictionary):
        return LogicalToolHandler(
            name,
            dictionary['tool'],
            dictionary['parameters']
        )

    def run(self, arango_handler, options):
        logging.info(u"[starting] Processing: {}".format(self.name))

        parameters = u"{} {}".format(self.tool, self.parameters)
        arguments = parameters.format(
            options
        )
        arguments = shlex.split(arguments, posix=False)

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

        logging.info(u"[finished] Processing: {}".format(self.name))
