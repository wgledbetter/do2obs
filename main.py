import collections.abc
import json
import os
import pathlib
from typing import Any

import fire
import mdformat
import mdformat_frontmatter
from markdown_it.utils import OptionsDict
from mdformat._util import NULL_CTX
from mdformat._util import build_mdit
from mdformat.renderer import MDRenderer
from mdformat_frontmatter.plugin import _render_frontmatter
from mdit_py_plugins.front_matter import front_matter_plugin

# Format String Snippets ###############################################################

FRONT_MATTER_FORMAT = """---
{yaml}
---
"""

LOCATION_FRONT_MATTER_FORMAT = "location: [{latitude}, {longitude}]"

DAYONE_MOMENT_FORMAT = "![](dayone-moment://{photoIdentifier})"

OBSIDIAN_PICTURE_LINK_FORMAT = "![[{photoFile}]]"

TAGS_SECTION_FORMAT = "## Tags\n{}"

# Utilities ############################################################################


def extendedMdFormatText(md: str):
    mdit = build_mdit(MDRenderer)
    mdit.use(front_matter_plugin)
    mdit.options["parser_extension"] = [mdformat_frontmatter]
    rendering = mdit.render(md)

    return rendering


# Main #################################################################################
def main(dayOneFile: str = "test/do/Journal.json", obsidianFolder: str = "test/obs"):
    dayOneFile = os.path.abspath(dayOneFile)
    obsidianFolder = os.path.abspath(obsidianFolder)

    dayOneRoot = os.path.dirname(dayOneFile)
    journalName = os.path.basename(dayOneFile).split(".")[0]

    obsPhotoDir = pathlib.Path(os.path.abspath(os.path.join(obsidianFolder, "photos")))
    obsPhotoDir.mkdir(exist_ok=True, parents=True)

    dayOneEntries = []
    with open(dayOneFile, "r") as f:
        dayOneEntries = json.load(f)["entries"]

    for e in dayOneEntries:
        # Create output file -----------------------------------------------------------
        obsName = e["creationDate"] + ".md"
        cYear = obsName[0:4]
        cMonth = obsName[5:7]
        obsOutPath = pathlib.Path(
            os.path.abspath(os.path.join(obsidianFolder, cYear, cMonth))
        )
        obsOutPath.mkdir(exist_ok=True, parents=True)

        # Read entry text --------------------------------------------------------------
        t = e["text"]

        # Handle Photos ----------------------------------------------------------------
        nP = len(e["photos"])
        for i in range(nP):
            p = e["photos"][i]
            dayOnePhotoLink = DAYONE_MOMENT_FORMAT.format(
                photoIdentifier=p["identifier"].upper()
            )
            dayOnePicFName = p["md5"] + "." + p["type"]
            dayOnePicRelPath = os.path.join("photos", dayOnePicFName)
            dayOnePicFPath = os.path.abspath(os.path.join(dayOneRoot, dayOnePicRelPath))
            obsPicFName = e["creationDate"] + "-{}.".format(i) + p["type"]
            obsPicRelPath = os.path.join("photos", obsPicFName)
            obsPicFPath = os.path.abspath(os.path.join(obsidianFolder, obsPicRelPath))
            # Rename and copy to destination
            with open(dayOnePicFPath, "rb") as inPic:
                with open(obsPicFPath, "wb") as outPic:
                    outPic.write(inPic.read())
            # Replace entry text with markdown link to new file
            obsidianPhotoLink = OBSIDIAN_PICTURE_LINK_FORMAT.format(
                photoFile=obsPicRelPath
            )
            t = t.replace(dayOnePhotoLink, obsidianPhotoLink)

        # Handle Audios ----------------------------------------------------------------
        # None, because I'm on Android.
        # I imagine it'd have a similar pattern to the photos, though.

        # Handle Metadata --------------------------------------------------------------
        journalFrontMatter = "journal: {}".format(
            "main" if journalName.lower() == "journal" else journalName.lower()
        )
        if "location" in e:
            lat = e["location"]["latitude"]
            lon = e["location"]["longitude"]
            # Create a frontmatter section in the output file
            locationFrontMatter = LOCATION_FRONT_MATTER_FORMAT.format(
                latitude=lat, longitude=lon
            )
            if "address" in e["location"]:
                addressFrontMatter = 'address: "{}"'.format(e["location"]["address"])
            else:
                addressFrontMatter = ""

            frontMatter = FRONT_MATTER_FORMAT.format(
                yaml=locationFrontMatter
                + "\n"
                + addressFrontMatter
                + "\n"
                + journalFrontMatter
            )

        else:
            frontMatter = FRONT_MATTER_FORMAT.format(yaml=journalFrontMatter)

        # Handle Tags ------------------------------------------------------------------

        jTag = "#" + journalName.lower()
        tags = []
        for tg in e["tags"]:
            tags.append("#" + tg.replace(" ", "_"))

        tagsSection = TAGS_SECTION_FORMAT.format(jTag + " " + " ".join(tags))

        # Create and Write File --------------------------------------------------------

        mdContents = extendedMdFormatText(frontMatter + t + "\n" + tagsSection)
        mdContents = mdContents.replace("\[", "[").replace("\]", "]")
        with open(os.path.join(obsOutPath, obsName), "w") as obsOut:
            obsOut.write(mdContents)


# Run ##################################################################################
if __name__ == "__main__":
    fire.Fire(main)
