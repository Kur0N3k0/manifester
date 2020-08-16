import os, sys, zipfile, uuid
import json
from pathlib import Path
from glob import glob
from xml.etree import ElementTree as ET
from apkutils import APK

if len(sys.argv) != 2:
    print("[Usage] python manifester.py {target_path}")
    exit(-1)

if not os.path.exists("./result"):
    os.mkdir("./result")

target_path = sys.argv[1]

ns = "{http://schemas.android.com/apk/res/android}"

safeAttr = lambda x, y: x.attrib[y] if y in x.attrib else ""

for item in glob(f"{target_path}/*.apk"):
    filename = Path(item).stem
    manifest_uuid = str(uuid.uuid4())

    apk = APK(item)
    root = ET.fromstring(apk.get_org_manifest())
    app = root.find("application")
    result = {}
    for child in list(app):
        if child.tag not in result:
            result[child.tag] = []
        
        name = safeAttr(child, f"{ns}name")
        enabled = safeAttr(child, f"{ns}enabled") != "false"
        exported = safeAttr(child, f"{ns}exported") == "true"
        permission = safeAttr(child, f"{ns}permission")
        read_permission = safeAttr(child, f"{ns}readpermission")
        write_permission = safeAttr(child, f"{ns}writepermission")

        intents = []
        for intent_filter in list(child):
            intent = {}
            for intent_item in list(intent_filter):
                if intent_item.tag == "action":
                    intent["action"] = safeAttr(intent_item, f"{ns}name")
                elif intent_item.tag == "category":
                    intent["category"] = safeAttr(intent_item, f"{ns}name")
                elif intent_item.tag == "data":
                    intent["data"] = {
                        "scheme": safeAttr(intent_item, f"{ns}scheme"),
                        "host": safeAttr(intent_item, f"{ns}host"),
                        "port": safeAttr(intent_item, f"{ns}port"),
                        "path": safeAttr(intent_item, f"{ns}path"),
                        "pathPattern": safeAttr(intent_item, f"{ns}pathPattern"),
                        "pathPrefix": safeAttr(intent_item, f"{ns}pathPrefix"),
                        "mimeType": safeAttr(intent_item, f"{ns}mimeType")
                    }
                
            if len(intent):
                intents += [ intent ]

        if enabled and exported and not (permission or read_permission or write_permission):
            result[child.tag] += [ {
                "class": name,
                "intent": intents
            } ]

    open(f"result/{filename}.txt", "w").write(json.dumps(result, indent=4))