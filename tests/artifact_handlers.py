import sys
sys.path.append(u"..")
from lib import ArtifactHandler as Ah


def main():
    am = Ah.ArtifactMapping.from_file(u"ArtifactHandlers.yml")
    pass


if __name__ == u"__main__":
    main()