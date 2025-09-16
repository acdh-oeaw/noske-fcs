from json import dump, load
from logging import INFO, StreamHandler, basicConfig, error, info, warning
from os import listdir
from os.path import join
from re import finditer

from yaml import safe_load

PATH_REGISTRY = "/var/lib/manatee/registry"
BASIC_SEARCH_ATTRIBUTES = ["word", "lemma"]
ATTR_TO_LAYER = {
    "word": "text",
    "lemma": "lemma",
    "pos": "pos",
    "orth": "orth",
    "norm": "norm",
    "phonetic": "phonetic",
}

basicConfig(level=INFO, handlers=[StreamHandler()])

with open("conf-docker.json", "r") as file:
    sruCfg = load(file)
sruCfg["corpora"]["resources"] = []

with open("corpora.yaml", "r") as file:
    corporaCfg = safe_load(file)

info("### Parsing registry files")
for corpCfgFilename in listdir(PATH_REGISTRY):
    if corpCfgFilename not in corporaCfg:
        warning(
            f"skipping {corpCfgFilename} because it is not defined in the corpora.yaml"
        )
        continue
    info(f"## Processing {corpCfgFilename}")
    with open(join(PATH_REGISTRY, corpCfgFilename), "rt") as corpCfgFile:
        corpCfgStr = corpCfgFile.read()
    corpCfgStr = [x.strip() for x in corpCfgStr.split("\n")]
    corpCfgStr = [
        x
        for x in corpCfgStr
        if x.startswith("ATTRIBUTE") or x.startswith("STRUCTURE") or x.startswith("}")
    ]
    corpCfgStr = "@" + "@".join(corpCfgStr).replace('"', "")

    structures = []
    attributes = []
    valid = True

    state = "none"
    bracketsCount = 0
    for i in finditer(
        r"}|@(STRUCTURE|ATTRIBUTE)\s+([-a-zA-Z0-9_]+)\s*({)?", corpCfgStr
    ):
        if i.group(0) == "}":
            bracketsCount -= 1
        else:
            if i.group(3) == "{":
                bracketsCount += 1
            if i.group(1) == "STRUCTURE":
                if state == "struct":
                    error("unexpected STRUCTURE definition encoutered")
                    valid = False
                    break
                state = "struct"
                structures.append(i.group(2))
            elif i.group(1) == "ATTRIBUTE":
                if state != "struct" and state != "none":
                    error("unexpected ATTRIBUTE definition encoutered")
                    valid = False
                    break
                if state != "struct":
                    state = "attr"
                    attributes.append(i.group(2))

        if bracketsCount == 0:
            state = "none"
        elif bracketsCount < 0:
            error("unexpected } encountered")
            valid = False
            continue

    info("# creating the config")
    cfg = corporaCfg[corpCfgFilename]
    cfg["id"] = corpCfgFilename
    # deal with SRU vs mquery-sru property name differences
    cfg["fullName"] = cfg["title"]
    cfg["uri"] = cfg["landingPageURI"]
    # reshape the config structure
    cfg["structureMapping"] = {
        "utteranceStruct": cfg["utterance"],
        "paragraphStruct": cfg["paragraph"],
        "turnStruct": cfg["turn"],
        "textStruct": cfg["text"],
        "sessionStruct": cfg["session"],
    }
    for k, v in cfg["structureMapping"].items():
        if v not in structures:
            error(
                f"erorr in mapping {v} as {k} - {v} is not among defined structures ({', '.join(structures)})"
            )
            valid = False
    for i in [
        "title",
        "landingPageURI",
        "utterance",
        "paragraph",
        "turn",
        "text",
        "session",
    ]:
        cfg.pop(i)
    # attributes
    cfg["posAttrs"] = []
    for x in attributes:
        if x in ATTR_TO_LAYER:
            cfg["posAttrs"].append(
                {
                    "name": x,
                    "id": x,
                    "layer": ATTR_TO_LAYER[x],
                    "isBasicSearchAttr": x in BASIC_SEARCH_ATTRIBUTES,
                    "isLayerDefault": True,
                }
            )
        else:
            warning(
                f"skipping attribute {x} as it lacks mapping to an FCS layer (text/lemma/pos/orth/norm/phonetic)"
            )

    if valid:
        sruCfg["corpora"]["resources"].append(cfg)

info("### Writing the config.json")
with open("conf-docker.json", "w") as file:
    dump(sruCfg, file)
