#!/usr/bin/python
#
# Based on Per Olofsson Unarchiver
# Copyright 2016 Philippe Rochat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for Unarchiver class"""

import os
import subprocess
import shutil

from autopkglib import Processor, ProcessorError


__all__ = ["Unarchiver"]

EXTNS = {
    'zip': ['zip'],
    'tar_gzip': ['tar.gz', 'tgz'],
    'tar_bzip2': ['tar.bz2', 'tbz'],
    'tar': ['tar'],
    'gzip': ['gzip'],
}

class Archiver(Processor):
    """Archive decompressor for zip and common tar-compressed formats."""
    description = __doc__
    input_variables = {
        "archive_path": {
            "required": True,
            "description": "Path to an archive.",
        },
        "source_path": {
            "required": False,
            "description": ("Directory/Source File to be packed into archive. "
                            "Defaults to NAME.")
        },
      	"root_path": {
            "required": False,
            "description": ("Directory from where archive will be packed, created. "
                            "Defaults to RECIPE_CACHE_DIR.")
        },
        "archive_format": {
            "required": False,
            "description": ("The archive format. Currently supported: 'zip', "
                            "'tar_gzip', 'tar_bzip2', 'tar'. If omitted, the "
                            "file extension is used to guess the format.")
        }
    }
    output_variables = {
    }

    def get_archive_format(self, archive_path):
        """Guess archive format based on filename extension"""
        #pylint: disable=no-self-use
        for format_str, extns in EXTNS.items():
            for extn in extns:
                if archive_path.endswith(extn):
                    return format_str
        # We found no known archive file extension if we got this far
        return None

    def main(self):
        """Unarchive a file"""
        # handle some defaults for archive_path and source_path
        archive_path = self.env.get("archive_path")
        if not archive_path:
            raise ProcessorError(
                "Expected an 'archive_path' input variable but none is set!")
        source_path = self.env.get("source_path",self.env["NAME"])
        root_path = self.env.get("root_path",self.env["RECIPE_CACHE_DIR"])
        fmt = self.env.get("archive_format")
        if fmt is None:
            fmt = self.get_archive_format(archive_path)
            if not fmt:
                raise ProcessorError(
                    "Can't guess archive format for filename %s"
                    % os.path.basename(archive_path))
            self.output("Guessed archive format '%s' from filename %s"
                        % (fmt, os.path.basename(archive_path)))
        elif fmt not in EXTNS.keys():
            raise ProcessorError(
                "'%s' is not valid for the 'archive_format' variable. "
                "Must be one of %s." % (fmt, ", ".join(EXTNS.keys())))

        if fmt == "zip":
            cmd = ["/usr/bin/ditto",
                   "--noqtn",
                   "-c",
                   "-k",
                   source_path,
                   archive_path]
        elif fmt == "gzip":
           cmd = ["/usr/bin/ditto",
                  "--noqtn",
                  "-c",
                  source_path,
                  archive_path]
        elif fmt.startswith("tar"):
            cmd = ["/usr/bin/tar",
                   "-c",
                   "-f",
                   archive_path,
				   "-C",
				   root_path]
            if fmt.endswith("gzip"):
                cmd.append("-z")
            elif fmt.endswith("bzip2"):
                cmd.append("-j")
            cmd.append(source_path);
        # Call command.
        try:
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            (_, stderr) = proc.communicate()
        except OSError as err:
            raise ProcessorError(
                "%s execution failed with error code %d: %s"
                % (os.path.basename(cmd[0]), err.errno, err.strerror))
        if proc.returncode != 0:
            raise ProcessorError(
                "Archiving: %s failed: %s"
                % (cmd, stderr))

        self.output("Archived:  %s " % (cmd))

if __name__ == '__main__':
    PROCESSOR = Archiver()
    PROCESSOR.execute_shell()
