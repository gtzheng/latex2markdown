import os
from typing import Union
import argparse
class Buffer:
    def __init__(self, size):
        self.count = 0
        self.size = size
        self.buffer = []
    def isempty(self):
        return self.count == 0
    def add(self, c):
        if self.count < self.size:
            self.buffer.append(c)
            self.count += 1
            return None
        else:
            val = self.buffer.pop(0)
            self.buffer.append(c)
            return val
    def empty(self, num=-1):
        if self.count == 0:
            return ""
        if num < 0 or num > self.count:
            val = ''.join(self.buffer[0:self.count])
            self.buffer = []
            self.count = 0
            return val
        else:
            val = self.buffer[0:num]
            del self.buffer[0:num]
            self.count = self.count - num
            return ''.join(val)
    def match(self, pattern):
        assert len(pattern) <= self.size, "buffer size is smaller than the pattern size"
        val = ''.join(self.buffer[0:len(pattern)])
        if val == pattern:
            return True
        else:
            return False


def filter_document(data: str) -> str:
    """Filters out comments and redundant blank lines.

    Args:
        data (str): input data string

    Returns:
        str: filtered data string
    """
    data = data.strip()
    document = []
    for line in data.split('\n'):
        line = line.strip()
        if len(line)==0:
            document.append('\n')
        elif line[0] == '%':
            continue
        else:
            document.append(line+'\n')
    prev = ""
    documents_filtered = []
    for line in document:
        if prev == '\n' and line == '\n':
            continue
        else:
            documents_filtered.append(line)
            prev = line
    document = ''.join(documents_filtered)
    return document

def filter_commands(document: str) -> str:
    """Keeps allowed environments and commands.

    Must run AFTER processing the document.

    Args:
        document (str): input string

    Returns:
        str: filtered output string
    """
    found_env = ""
    in_env = False
    keep_envs = ["abstract", "equation", "equation*", "figure", "figure*", "table", "table*", "align"]
    keep_commands = ["paragraph"]
    line_arr = []
    for line in document.split('\n'):
        if len(line) > 0 and line[0] == "\\":
            if not in_env: 
                for env in keep_envs: # check whether line contains \begin{env}
                    if f"\\begin{{{env}}}" == line[0:len(f"\\begin{{{env}}}")]:
                        found_env = env
                        break
                if len(found_env) == 0: # not an environment
                    found_command = ""
                    for command in keep_commands:
                        if f"\\{command}" == line[0:len(f"\\{command}")]:
                            found_command = command
                            break
                    if len(found_command) > 0:
                        line_arr.append(line+'\n')
                    continue # next line
                else: # found an env
                    in_env = True
                    line_arr.append(line+'\n')
            else: # in the environment
                if f"\\end{{{env}}}" == line[0:len(f"\\end{{{env}}}")]: # exit the environment
                    in_env = False
                    found_env = ""
                line_arr.append(line+'\n')
        else:
            line_arr.append(line+'\n')
    return ''.join(line_arr)
            
def get_figure(data):
    fig_buffer = Buffer(len(data))
    for c in data:
        fig_buffer.add(c) 
    path = []
    label = []
    caption = []
    while not fig_buffer.isempty():
        if fig_buffer.match("\\includegraphics"):
            fig_buffer.empty(len("\\includegraphics"))
            find_path = False
            while True:
                v = fig_buffer.empty(1)
                if find_path:
                    if v == '}':
                        break
                    path.append(v)
                if v == '{':
                    find_path = True
        elif fig_buffer.match("\\label"):
            fig_buffer.empty(len("\\label"))
            find_label = False
            while True:
                v = fig_buffer.empty(1)
                if find_label:
                    if v == '}':
                        break
                    label.append(v)
                if v == '{':
                    find_label = True
            
        elif fig_buffer.match("\\caption"):
            fig_buffer.empty(len("\\caption"))
            find_caption = False
            bracket_count = 0
            while True:
                v = fig_buffer.empty(1)
                if find_caption:
                    if v == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            break
                    caption.append(v)
                if v == '{':
                    bracket_count += 1
                    find_caption = True
        fig_buffer.empty(1)
            
    return ''.join(path), ''.join(caption), ''.join(label)




def format_font(data: Union[str, list[str]]) -> str:
    """Converts latext font types to the markdown formats.

    Args:
        data (str): An input string

    Returns:
        str: The output font.
    """
    target = []
    buffer = Buffer(40)
    store_bold = False
    for c in data:
        v = buffer.add(c)
        if buffer.match("  "): # if there are two spaces
            buffer.empty(1)

        if store_bold:
            if v is None:
                continue
            elif v == "}":
                store_bold = False
                target.append("**")
                for s in bold_text:
                    if s == '\n':
                        s = ' '
                    target.append(s)
                target.append("**")
            else:
                bold_text.append(v)
            continue

        if buffer.match(r"\textbf{"):
            bold_text = []
            buffer.empty(len(r"\textbf{"))
            store_bold = True


        if v is not None:
            if v == '~':
                v = ' '
            target.append(v)
    target.append(buffer.empty())
    document = ''.join(target)
    return document

def main_latext2markdown(document: str) -> str:
    """Converts latext commands to the markdown commands.

    Processes section, section*, subsection, subsection*, cite, figure, figure*
      abstract

    Args:
        document (str): An input string.

    Returns:
        str: The output string.
    """
    target = []
    buffer = Buffer(40)
    store_abstract = False
    store_cite = False
    store_section = False
    store_section_star = False
    store_subsection = False
    store_subsection_star = False
    start_record = False
    store_figure = False
    store_figure_star = False
    bracket_count = 0
    figure_count = 1
    for c in document:
        v = buffer.add(c)
        if buffer.match("  "): # if there are two spaces
            buffer.empty(1)

        if store_cite: # process cite
            if v is None:
                continue
            elif v == "}":
                store_cite = False
                eles = ''.join(cite_arr).split(',')
                strs = "; ".join(['@'+e.strip() for e in eles])
                strs = '[' + strs + ']'
                target.append(strs)
            else:
                cite_arr.append(v)
            continue
        
        if store_abstract:
            if buffer.match("\\end{abstract}"):
                buffer.empty(len("\\end{abstract}"))
                store_abstract = False
                target.append("---\nabstract: >\n")
                for s in abstract_text:
                    target.append(s)
                if v is not None:
                    target.append(v)
                    if v != '\n':
                        target.append('\n')
                target.append("---\n")
                if buffer.buffer[1] != "\n":
                    target.append('\n')
            else:
                if v is not None:
                    abstract_text.append(v)
            continue


        if store_figure:
            if buffer.match("\\end{figure}"):
                buffer.empty(len("\\end{figure}"))
                store_figure = False
                path, caption, label = get_figure(figure_text)
                target.append(f"![\label{{{label}}}**Figure {figure_count}:** {caption}]({path}){{fullwidth=t}}\n")
                figure_count += 1
            else:
                if v is not None:
                    figure_text.append(v)
            continue

        if store_figure_star:
            if buffer.match("\\end{figure*}"):
                buffer.empty(len("\\end{figure*}"))
                store_figure_star = False
                path, caption, label = get_figure(figure_text)
                target.append(f"![\label{{{label}}}**Figure {figure_count}:** {caption}]({path}){{fullwidth=t}}\n")
                figure_count += 1
            else:
                if v is not None:
                    figure_text.append(v)
            continue


        if store_section: # process section
            if v is None:
                continue
            elif v == '{':
                bracket_count += 1
                section_title.append(v)
            elif v == "}":
                if bracket_count > 0:
                    bracket_count -= 1
                    section_title.append(v)
                else:
                    store_section = False
                    if target[-2] != "\n":
                        target.append('\n')
                    target.append("# ")
                    for s in section_title:
                        if s == '\n':
                            s = ' '
                        target.append(s)
                    if buffer.buffer[1] != "\n":
                        target.append('\n')
            else:
                section_title.append(v)
            continue

        if store_section_star:
            if v is None:
                continue
            elif v == '{':
                bracket_count += 1
                section_title.append(v)
            elif v == "}":
                if bracket_count > 0:
                    bracket_count -= 1
                    section_title.append(v)
                else:
                    store_section_star = False
                    if target[-2] != "\n":
                        target.append('\n')
                    target.append("# ")
                    for s in section_title:
                        if s == '\n':
                            s = ' '
                        target.append(s)
                    if buffer.buffer[1] != "\n":
                        target.append('\n')
            else:
                section_title.append(v)
            continue

        if store_subsection:
            if v is None:
                continue
            elif v == '{':
                bracket_count += 1
                subsection_title.append(v)
            elif v == "}":
                if bracket_count > 0:
                    bracket_count -= 1
                    subsection_title.append(v)
                else:
                    store_subsection = False
                    if target[-2] != "\n":
                        target.append('\n')
                    target.append("## ")
                    for s in subsection_title:
                        if s == '\n':
                            s = ' '
                        target.append(s)
                    if buffer.buffer[1] != "\n":
                        target.append('\n')
            else:
                subsection_title.append(v)
            continue

        if store_subsection_star:
            if v is None:
                continue
            elif v == '{':
                bracket_count += 1
                subsection_title.append(v)
            elif v == "}":
                if bracket_count > 0:
                    bracket_count -= 1
                    subsection_title.append(v)
                else:
                    store_subsection_star = False
                    if target[-2] != "\n":
                        target.append('\n')
                    target.append("## ")
                    for s in subsection_title:
                        if s == '\n':
                            s = ' '
                        target.append(s)
                    if buffer.buffer[1] != "\n":
                        target.append('\n')
            else:
                subsection_title.append(v)
            continue

        


        if buffer.match(r"\cite{"):
            cite_arr = []
            buffer.empty(6)
            store_cite = True

        if buffer.match(r"\section{"):
            section_title = []
            buffer.empty(len(r"\section{"))
            store_section = True


        if buffer.match(r"\section*{"):
            section_title = []
            buffer.empty(len(r"\section*{"))
            store_section_star = True

        if buffer.match(r"\subsection{"):
            subsection_title = []
            buffer.empty(len(r"\subsection{"))
            store_subsection = True

        if buffer.match(r"\subsection*{"):
            subsection_title = []
            buffer.empty(len(r"\subsection*{"))
            store_subsection_star = True

        if buffer.match("\\begin{abstract}"):
            abstract_text = []
            buffer.empty(len("\\begin{abstract}"))
            store_abstract = True
            start_record = True

        if buffer.match("\\begin{figure}"):
            figure_text = []
            buffer.empty(len("\\begin{figure}"))
            store_figure = True

        if buffer.match("\\begin{figure*}"):
            figure_text = []
            buffer.empty(len("\\begin{figure*}"))
            store_figure_star = True

        if v is not None and start_record:
            if v == '~':
                v = ' '
            target.append(v)
    target.append(buffer.empty())
    document = ''.join(target)
    return document

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latex2Markdown")
    parser.add_argument(
        "--fin", type=str,
        help="Input file")
    parser.add_argument(
        "--fout", type=str,
        help="Output file")
    args = parser.parse_args()
    file_path  = args.fin
    with open(file_path, "r") as f:
        data = f.read()

document = filter_document(data) # Filters out comments and redundant blank lines.
document = main_latext2markdown(document)
document = filter_commands(document) # filter out unnecessary environments and commands
document = format_font(document)
document = filter_document(document) # filter out additional comments and redundant blank lines
with open(args.fout,"w") as f:
    f.write(document)
