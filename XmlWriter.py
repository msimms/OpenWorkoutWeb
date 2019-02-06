# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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

class XmlWriter(object):
    """Base class for XMl-formatted file generators, like TCX and GPX files."""

    def __init__(self):
        super(XmlWriter, self).__init__()
        self.file = None
        self.tags = []

    def create_file(self, file_name):
        self.file = open(file_name, 'wt')
        if self.file is None:
            raise Exception("Could not create the file.")
        self.file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>\n")

    def close_file(self):
        self.file = None

    def current_tag(self):
        if len(self.tags) is None:
            return None
        return self.tags[-1]

    def open_tag(self, tag_name):
        xml_str  = self.format_indent()
        xml_str += "<"
        xml_str += tag_name
        xml_str += ">\n"

        self.tags.append(tag_name)
        self.file.write(xml_str)

    def open_tag_with_attributes(self, tag_name, key_values, values_on_individual_lines):
        indent = self.format_indent()

        xml_str = indent
        xml_str += "<"
        xml_str += tag_name
        xml_str += " "

        first = True
        for key_value in key_values:
            if values_on_individual_lines:
                xml_str += "\n"
                xml_str += indent
                xml_str += " "
            elif not first:
                xml_str += " "
            key = key_value.keys()[0]
            xml_str += key
            xml_str += "=\""
            xml_str += key_value[key]
            xml_str += "\""
            first = False
        xml_str += ">\n"

        self.tags.append(tag_name)
        self.file.write(xml_str)

    def write_tag_and_value(self, tag_name, value):
        xml_str  = self.format_indent()
        xml_str += "<"
        xml_str += tag_name
        xml_str += ">"
        xml_str += str(value)
        xml_str += "</"
        xml_str += tag_name
        xml_str += ">\n"
        self.file.write(xml_str)

    def close_tag(self):
        tag = self.tags.pop()
        xml_str = self.format_indent()
        xml_str += "</"
        xml_str += tag
        xml_str += ">\n"
        self.file.write(xml_str)		

    def close_all_tags(self):
        while len(self.tags) > 0:
            self.close_tag()

    def format_indent(self):
        xml_str = ""
        for i in range(0, len(self.tags)):
            xml_str += "  "
        return xml_str
