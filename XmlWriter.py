# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Michael J Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Base class for XMl-formatted file generators, like TCX and GPX files."""

class XmlWriter(object):
    """Base class for XMl-formatted file generators, like TCX and GPX files."""

    def __init__(self):
        super(XmlWriter, self).__init__()
        self.file = None
        self.strs = []
        self.tags = []

    def write(self, data):
        """Writes to either the file or the internal buffer, depending on whether or not a file was opened."""
        if self.file is None:
            self.strs.append(data)
        else:
            self.file.write(data)

    def create(self, file_name):
        """Opens the file or, if NULL is passed for the file_name, open a buffer in which to write."""
        if self.file is not None:
            self.file = open(file_name, 'wt')
            if self.file is None:
                raise Exception("Could not create the file.")
            self.file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>\n")

    def buffer(self):
        return ''.join(self.strs)

    def close(self):
        self.file = None
        self.strs = []
        self.tags = []

    def current_tag(self):
        if len(self.tags) is None:
            return None
        return self.tags[-1]

    def open_tag(self, tag_name):
        xml_str = self.format_indent() + "<" + tag_name + ">\n"
        self.tags.append(tag_name)
        self.write(xml_str)

    def open_tag_with_attributes(self, tag_name, key_values, values_on_individual_lines):
        indent = self.format_indent()
        xml_str = indent + "<" + tag_name + " "
        first = True
        for key in key_values:
            if values_on_individual_lines:
                xml_str += "\n"
                xml_str += indent
                xml_str += " "
            elif not first:
                xml_str += " "
            xml_str += key
            xml_str += "=\""
            xml_str += key_values[key]
            xml_str += "\""
            first = False
        xml_str += ">\n"

        self.tags.append(tag_name)
        self.write(xml_str)

    def write_tag_and_value(self, tag_name, value):
        xml_str = self.format_indent() + "<" + tag_name + ">" + str(value) + "</" + tag_name + ">\n"
        self.write(xml_str)

    def close_tag(self):
        tag = self.tags.pop()
        xml_str = self.format_indent() + "</" + tag + ">\n"
        self.write(xml_str)		

    def close_all_tags(self):
        while len(self.tags) > 0:
            self.close_tag()

    def format_indent(self):
        xml_str = "  " * len(self.tags)
        return xml_str
