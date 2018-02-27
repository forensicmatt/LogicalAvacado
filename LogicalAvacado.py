import pytsk3
import logging
import argparse
from lib import EnumHandlers as Eh
from lib import ArtifactHandler as Ah
from lib.ArangoHandler import ArangoHandler

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
        type=unicode,
        help=u"Logical source [Example: \\\\.\\C:]"
    )
    arguments.add_argument(
        "-t", "--temp_dir",
        dest="temp_dir",
        action="store",
        required=True,
        type=unicode,
        help=u"TEMP_DIR (Make sure this is a on a volume that can handle large files.)"
    )
    arguments.add_argument(
        "-d", "--database",
        dest="database",
        action="store",
        required=True,
        type=unicode,
        help=u"The name of the database you want to create inside in ArangoDB."
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
