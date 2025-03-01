# -*- coding: utf-8 -*-
# http://www.octopus-studio.com/download.en.htm

import os
from os.path import isdir

from pyglossary.compression import compressionOpen as c_open
from pyglossary.compression import stdCompressions
from pyglossary.core import log
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	FileSizeOption,
)

enable = True
lname = "octopus_mdict_source"
format = "OctopusMdictSource"
description = "Octopus MDict Source"
extensions = (".mtxt",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	# "links": BoolOption(),
	"resources": BoolOption(comment="Enable resources / data files"),
	"file_size_approx": FileSizeOption(
		comment="split up by given approximate file size\nexamples: 100m, 1g",
	),
	"word_title": BoolOption(
		comment="add headwords title to begining of definition",
	),
}
depends = {}

tools = [
	{
		"name": "MDXBuilder",
		"web": "https://www.mdict.cn/",
		"platforms": ["Windows"],
		"license": "Proprietary",
	},
]

file_size_check_every = 100


def replaceStringTable(
	rplList: "list[tuple[str, str]]",
):
	def replace(st: str) -> str:
		for rpl in rplList:
			st = st.replace(rpl[0], rpl[1])
		return st

	return replace


class Reader:
	_encoding = "utf-8"

	def __init__(self, glos):
		self._glos = glos
		self._filename = ""
		self._file = None
		self._wordCount = 0

		# dict of mainWord -> newline-separated altenatives
		self._linksDict = {}  # type: Dict[str, str]

	def __len__(self):
		return self._wordCount

	def close(self):
		if self._file:
			self._file.close()
		self._file = None

	def open(
		self,
		filename,
		encoding="utf-8",
	):
		self._filename = filename
		self._encoding = encoding
		self._file = open(filename, encoding=encoding)
		self.loadLinks()

	def loadLinks(self):
		linksDict = {}
		word = ""
		defi = ""
		wordCount = 0
		for line in self._file:
			line = line.strip()
			if line.startswith("#"):
				continue
			if line == "</>":
				if word and defi:
					wordCount += 1
				word, defi = "", ""
				continue
			if line.startswith("@@@LINK="):
				if not word:
					log.warn(f"unexpected line: {line}")
					continue
				mainWord = line[8:]
				if mainWord in linksDict:
					linksDict[mainWord] += "\n" + word
				else:
					linksDict[mainWord] = word
				continue
			if not word:
				word = line
				continue
			defi += line

		if word and defi:
			wordCount += 1
		log.info(f"wordCount = {wordCount}")
		self._linksDict = linksDict
		self._wordCount = wordCount
		self._file = open(self._filename, encoding=self._encoding)

	def __iter__(self):
		linksDict = self._linksDict
		word, defi = "", ""
		glos = self._glos

		def newEntry():
			words = word
			altsStr = linksDict.get(word, "")
			if altsStr:
				words = [word] + altsStr.split("\n")
			return glos.newEntry(words, defi)

		for line in self._file:
			line = line.strip()
			if line == "</>":
				if defi:
					yield newEntry()
				word, defi = "", ""
				continue
			if line.startswith("@@@LINK="):
				continue
			if word:
				line = line.replace("entry://", "bword://")
				defi += "\n" + line
			else:
				word = line

		if word:
			yield newEntry()


class Writer:
	_resources = True
	_file_size_approx: int = 0
	_word_title: bool = False
	_encoding = "utf-8"

	compressions = stdCompressions

	def __init__(self, glos):
		self._glos = glos
		self._filename = None
		self._file = None

	def finish(self):
		self._filename = None

	def open(self, filename):
		if self._file_size_approx > 0:
			self._glos.setInfo("file_count", "-1")
		self._open(filename)
		self._filename = filename
		self._resDir = f"{filename}_res"
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

	def _open(self, filename: str):
		if not filename:
			filename = self._glos.filename + self._ext

		_file = self._file = c_open(
			filename,
			mode="wt",
			encoding=self._encoding,
		)
		# TODO: write info
		_file.flush()
		return _file

	def write(self):
		encoding = "utf-8"
		_file = self._file
		filename = self._filename
		glos = self._glos
		file_size_approx = self._file_size_approx
		word_title = self._word_title

		entryFmt = "{word}\n{defi}\n</>\n"
		defiEscapeFunc = replaceStringTable(
			[
				("bword://", "entry://"),
			]
		)

		myResDir = self._resDir
		fileIndex = 0
		entryCount = 0

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if self._resources:
					entry.save(myResDir)
				continue

			words = entry.l_word
			defi = entry.defi
			defi = defiEscapeFunc(defi)

			if word_title:
				defi = glos.wordTitleStr(words[0]) + defi

			_file.write(entryFmt.format(word=words[0], defi=defi))

			for alt in words[1:]:
				_file.write(
					entryFmt.format(
						word=alt,
						defi="@@@LINK=" + words[0],
					)
				)

			if file_size_approx > 0:
				entryCount += 1
				if entryCount % file_size_check_every == 0:
					if _file.tell() >= file_size_approx:
						fileIndex += 1
						_file = self._open(f"{self._filename}.{fileIndex}")

		_file.close()
		if not os.listdir(myResDir):
			os.rmdir(myResDir)
