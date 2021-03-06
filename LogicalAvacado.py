import pytsk3
import logging
import argparse
from libla import EnumHandlers as Eh
from libla import ArtifactHandler as Ah
from libla.ArangoHandler import ArangoHandler
from libla.LogicalToolHandler import LogicalToolManager

logging.basicConfig(
    level=logging.INFO
)


def get_arguments():
    usage = '''Process a logical volume.'''

    arguments = argparse.ArgumentParser(
        description=(usage)
    )
    arguments.add_argument(
        "-s", "--source",
        dest="source",
        action="store",
        required=True,
        help=u"Logical source [Example: \\\\.\\C:]"
    )
    arguments.add_argument(
        "-t", "--temp_dir",
        dest="temp_dir",
        action="store",
        required=True,
        help=u"TEMP_DIR (Make sure this is on a volume that can handle large files.)"
    )
    arguments.add_argument(
        "-d", "--database",
        dest="database",
        action="store",
        required=True,
        help=u"The name of the database you want to create inside of ArangoDB."
    )

    return arguments


def main():
    arguments = get_arguments()
    options = arguments.parse_args()

    tsk_img = pytsk3.Img_Info(
        options.source
    )

    arango_handler = ArangoHandler(
        options.database
    )

    tool_manager = LogicalToolManager.from_file(
        u"LogicalHandlers.yml"
    )
    tool_manager.run(
        arango_handler, options
    )

    handler_mapping = Ah.ArtifactMapping.from_file(
        u"ArtifactHandlers.yml"
    )

    le = Eh.LogicalEnumerator(
        tsk_img, handler_mapping,
        arango_handler, options.temp_dir,
        description=options.source
    )
    le.process_files()


if __name__ == "__main__":
    main()
