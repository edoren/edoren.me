#!/usr/bin/env python3

import os
import os.path
from collections import OrderedDict
from uuid import uuid4
from datetime import datetime, timezone

post_types = {
    "_default": [
        ("id", lambda: str(uuid4())),
        ("date", lambda: datetime.now(timezone.utc).astimezone()
                                 .replace(microsecond=0).isoformat()),
        ("title", "")
    ],
    "blog": [
        ("tags", []),
        ("categories", [])
    ]
}


def setup_yaml():
    import yaml
    """ https://stackoverflow.com/a/8661021 """
    def OrderedDictRepresenter(dumper, data):
        return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, OrderedDictRepresenter)
    return yaml


def create_post(post_type, post_path):
    page_template = "---\n{}---\n\n<!--description-->\n" \
                    "\n<!--more-->\n\n<!--content-->\n"

    contents = post_types["_default"]
    if post_type is not None:
        if post_type in post_types:
            contents += post_types[post_type]

    for i in range(len(contents)):
        key, value = contents[i]
        if callable(value):
            contents[i] = (key, value())

    contents.append(("type", post_type))
    contents = OrderedDict(contents)

    yaml = setup_yaml()

    content_dump = yaml.dump(contents, default_flow_style=False, indent=4)

    with open(post_path, "w") as f:
        f.write(page_template.format(content_dump))


def main(argv):
    if len(argv) == 1:
        print("Error: path needs to be provided")
        exit(255)

    name = argv[1].replace("\\", "/")
    content_folder = "content"

    post_path = os.path.abspath(os.path.join(content_folder, name))
    if os.path.exists(post_path):
        print("Error: {} already exists".format(post_path))
        exit(255)

    post_folder = os.path.dirname(post_path)
    if not os.path.exists(post_folder):
        os.makedirs(post_folder)

    tmp = name.split("/")
    if (len(tmp) == 1):
        post_type = None
    else:
        post_type = tmp[0]

    create_post(post_type, post_path)


if __name__ == "__main__":
    from sys import argv
    main(argv)
