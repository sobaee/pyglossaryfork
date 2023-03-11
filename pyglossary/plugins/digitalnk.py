# -*- coding: utf-8 -*-

import html
import typing
from typing import Iterator

from pyglossary.glossary_type import EntryType, GlossaryType

enable = True
lname = "digitalnk"
format = 'DigitalNK'
description = 'DigitalNK (SQLite3, N-Korean)'
extensions = ()
extensionCreate = ".db"
kind = "binary"
wiki = ""
website = (
	"https://github.com/digitalprk/dicrs",
	"@digitalprk/dicrs",
)


class Reader(object):
	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self: "typing.Self", filename: str) -> None:
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("m")

	def __len__(self) -> int:
		self._cur.execute("select count(*) from dictionary")
		return self._cur.fetchone()[0]

	def __iter__(self) -> "Iterator[EntryType]":
		self._cur.execute(
			"select word, definition from dictionary"
			" order by word",
		)
		# iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# no idea why!
		# https://github.com/ilius/pyglossary/issues/282
		# for row in self._cur:
		for row in self._cur.fetchall():
			word = html.unescape(row[0])
			definition = row[1]
			yield self._glos.newEntry(word, definition, defiFormat="m")

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
