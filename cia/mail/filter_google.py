#!/usr/bin/env python
from filterlib import CommitFilter
import re, time

PROJECT_TRANS = {
    'cia-vc': 'cia.vc',
}

class GoogleFilter(CommitFilter):
    project = 'unknown-google'

    def pullFiles(self, action):
        # Files are prefixed by four spaces.
        # Sometimes, they are followed by info like "      copied from ...",
        # which we don't really want.
        while True:
            line = self.pullLine()
            if len(line) <= 4 or line.lstrip() != line[4:]:
                self.pushLine(line)
                return
            self.addFile(line.strip(), action)

    def pullLog(self):
        # Log is somewhat ambiguous.
        # I guess the exact algorithm would be # "find the first line
        # of 78 '=' chars and cut message at the last empty line before.
        # Oh well, we cut at the first empty line, for now.
        lines = []
        while True:
            line = self.pullLine().strip()
            if not line:
                break
            lines.append(line)
        self.addLog("\n".join(lines))


    def addRevision(self, revision):
        self.xml.body.commit.addElement('revision', content=revision)

    def addTimestamp(self, timestamp):
        self.xml.addElement('timestamp', content=timestamp)

    def resetProject(self, project):
        # XXX - hack
        self.xml.source.project.children[0] = project

    def parse(self):
        self.xml.generator.addElement('version', content='Googlecode parser 0.3')
        match = re.match(r"\s*\[(?P<project>.*) commit\].*", self.message['subject'])
        if not match:
            return

        project = match.group('project')
        if project in PROJECT_TRANS:
            project = PROJECT_TRANS[project]
        self.resetProject(project)

        while True:
            line = self.pullLine()
            if not line:
                return
            line = line.strip()

            if line.startswith("Author: "):
                self.addAuthor(line.split(None, 1)[1])
            elif line.startswith("Date: "):
                timestr = line.split(None, 1)[1]
                timestamp = int(time.mktime(time.strptime(
                        timestr, "%a %b %d %H:%M:%S %Y")))
                self.addTimestamp("%d" % timestamp)
            elif line.startswith("New Revision: "):
                self.addRevision(line.split(None, 2)[2])
            elif line == "Added:":
                self.pullFiles("add")
            elif line == "Modified:":
                self.pullFiles("modify")
            elif line == "Removed:":
                self.pullFiles("remove")
            elif line == "Log:":
                self.pullLog()
                return
            else:
                print "Debug: Unhandled line '%s'" % line

if __name__ == '__main__':
    GoogleFilter().main()
