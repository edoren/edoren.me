#!/usr/bin/env python3

import argparse
import os
import os.path
from collections import OrderedDict
from datetime import datetime, timezone
from uuid import uuid4

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def create_post(post_path, post_type):
    post_vars = {
        "id": str(uuid4()),
        "date": datetime.now(timezone.utc).astimezone().isoformat(),
        "type": post_type
    }
    with open(os.path.join(SCRIPT_DIR, "templates", "new_post.md")) as f:
        data = f.read()
        with open(post_path, "w") as fpost:
            fpost.write(data.format(**post_vars))


def main(args):
    post_name = args.name.replace("\\", "/")
    post_type = args.type
    content_folder = os.path.join(SCRIPT_DIR, "content")

    post_path = os.path.join(content_folder, post_name)
    if not os.path.splitext(post_path)[1]:
        post_path += ".md"

    if os.path.exists(post_path):
        print("Error: {} already exists".format(post_path))
        exit(-1)

    post_folder = os.path.dirname(post_path)
    if not os.path.exists(post_folder):
        os.makedirs(post_folder)

    create_post(post_path, post_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name",
                        help="New post file name, this can be a path.\n"
                        "Eg. blog/tutorials/my_post.md",
                        type=str)
    parser.add_argument("-t, --type",
                        dest="type",
                        help="The type of the new post. Defaults to 'blog'",
                        default="blog",
                        type=str)
    main(parser.parse_args())
