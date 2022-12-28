import glob
import json
import os
import pathlib
from typing import List

import fire
import mdformat_frontmatter
from mdformat._util import build_mdit
from mdformat.renderer import MDRenderer
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

# Misc #################################################################################


def obsidianStar(noteTitle: str, vaultRelativePath: str) -> dict:
    return {"type": "file", "title": noteTitle, "path": vaultRelativePath}


def obsidianStarFile(stars: List[dict]) -> dict:
    return {"items": stars}


# Utilities ############################################################################


def extendedMdFormatText(md: str):
    mdit = build_mdit(MDRenderer)
    mdit.use(front_matter_plugin)
    mdit.options["parser_extension"] = [mdformat_frontmatter]
    rendering = mdit.render(md)

    return rendering


def recoverPhotoFromBackup(
    dayOneBackupDir: str, photoFName: str, journalName: str = ""
):
    if dayOneBackupDir[-1] != "/":
        dayOneBackupDir = dayOneBackupDir + "/"

    pFiles = [
        f for f in glob.iglob(dayOneBackupDir + "**/" + photoFName, recursive=True)
    ]

    for p in pFiles:
        try:
            with open(p, "rb") as f:
                return f.read()
        except:
            pass

    raise ValueError(
        "Unable to obtain image {} from backup directory '{}'.".format(
            photoFName, dayOneBackupDir
        )
    )


# Main #################################################################################
def main(
    dayOneFile: str = "/home/wgledbetter/pCloudSync/journal/3feb22/Export-Journal-3feb22/Export-Journal-3feb22/Journal.json",
    obsidianFolder: str = "test/obs",
    dayOneBackupDirs: List[str] = ["/home/wgledbetter/pCloudSync/journal/"],
):
    # Preliminary Path Setup -----------------------------------------------------------
    dayOneFile = os.path.abspath(dayOneFile)
    obsidianFolder = os.path.abspath(obsidianFolder)

    print("Converting '{}' into '{}'.".format(dayOneFile, obsidianFolder))

    dayOneRoot = os.path.dirname(dayOneFile)
    journalName = os.path.basename(dayOneFile).split(".")[0]

    obsPhotoDir = pathlib.Path(os.path.abspath(os.path.join(obsidianFolder, "photos")))
    obsPhotoDir.mkdir(exist_ok=True, parents=True)

    # Check if output is already an existing vault -------------------------------------
    # Find a folder called .obsidian in the root or above
    def getObsidianRoot(path: str):
        if os.path.exists(os.path.join(path, ".obsidian")):
            return path
        elif os.path.dirname(path) != path:
            return getObsidianRoot(os.path.dirname(path))
        else:
            return ""

    obsidianRoot = getObsidianRoot(obsidianFolder)
    if obsidianRoot == "":
        print("WARNING: The obsidianFolder is not a vault or within a vault.")
    else:
        obsidianRoot = os.path.abspath(obsidianRoot)

    # Read entries ---------------------------------------------------------------------

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
        if "photos" in e:
            nP = len(e["photos"])
        else:
            nP = 0

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
            try:
                with open(obsPicFPath, "wb") as outPic:
                    try:
                        with open(dayOnePicFPath, "rb") as inPic:
                            outPic.write(inPic.read())
                    except:
                        for bud in dayOneBackupDirs:
                            bud = os.path.abspath(bud)
                            try:
                                outPic.write(
                                    recoverPhotoFromBackup(bud, dayOnePicFName)
                                )
                                break
                            except:
                                pass
                        else:
                            print("Failed to recover image {}.".format(dayOnePicFName))

            except:
                # Output file open failed. Very strange
                print("Something is wrong with the output image file...")

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

        tags = ["#dayone", "#" + journalName.lower().replace(" ", "_")]
        if "tags" in e:
            for tg in e["tags"]:
                tags.append("#" + tg.replace(" ", "_"))

        tagsSection = TAGS_SECTION_FORMAT.format(" ".join(tags))

        # Create and Write File --------------------------------------------------------

        mdContents = extendedMdFormatText(frontMatter + t + "\n" + tagsSection)
        mdContents = mdContents.replace("\[", "[").replace("\]", "]")
        with open(os.path.join(obsOutPath, obsName), "w") as obsOut:
            obsOut.write(mdContents)

        # Handle stars -----------------------------------------------------------------
        if e["starred"] and obsidianRoot != "":
            star = obsidianStar(
                noteTitle=obsName.split(".")[0],
                vaultRelativePath=os.path.relpath(
                    os.path.join(obsOutPath, obsName), start=obsidianRoot
                ),
            )
            starFile = os.path.join(obsidianRoot, ".obsidian", "starred.json")
            if os.path.exists(starFile):
                with open(starFile, "r") as sf:
                    starDict = json.load(sf)
                if star not in starDict["items"]:
                    starDict["items"].append(star)

            else:
                starDict = obsidianStarFile(stars=[star])

            with open(starFile, "w") as sf:
                json.dump(starDict, sf, indent=2)


# Run ##################################################################################
if __name__ == "__main__":
    fire.Fire(main)
