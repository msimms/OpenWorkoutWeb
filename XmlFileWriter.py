# Copyright 2018 Michael J Simms

class XmlFileWriter(object):
    """Base class for XMl-formatted file type writers, like TCX and GPX files."""

    def __init__(self):
        super(XmlFileWriter, self).__init__()
        self.file = None

    def create_file(file_name):
        self.file = open(file_name, 'wt')
        if self.file is not None:
            xml_str = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>\n"
            return self.file.write(xml_str)
        return False

    def open_tag(self, tag_name):
        xml_str  = self.format_indent()
        xml_str += "<"
        xml_str += tag_name
        xml_str += ">\n"

        self.tags.append(tag_name)
        return self.file.write(xml_str)

    def open_tag(self, tag_name, key_values, values_on_individual_lines):
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

        self.tags.push(tag_name)
        return self.file.write(xml_str)

    def write_tag_and_value(self, tag_name, value):
        xml_str  = self.format_indent()
        xml_str += "<"
        xml_str += tag_name
        xml_str += ">"
        xml_str += str(value)
        xml_str += "</"
        xml_str += tag_name
        xml_str += ">\n"
        return self.file.write(xml_str)

    def close_tag(self):
        tag_name = self.tags.top()
        self.tags.pop()

        xml_str = self.format_indent()
        xml_str += "</"
        xml_str += tag_name
        xml_str += ">\n"
        return self.file.write(xml_str)		

    def close_all_tags(self):
        result = True
        while len(self.tags) > 0 and result:
            result = self.close_tag()
        return True

    def format_indent(self):
        xml_str = ""
        for i in range(0, len(self.tags)):
            xml_str += "  "
        return xml_str
