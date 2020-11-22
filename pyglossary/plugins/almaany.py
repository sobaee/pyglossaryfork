# -*- coding: utf-8 -*-

from formats_common import *
import html

enable = True
format = 'Almaany'
description = 'Almaany.com Arabic Dictionary (SQLite3)'
extensions = ()
readOptions = []
writeOptions = []

tools = [
	{
		"name": "Almaany.com Arabic Dictionary",
		"web": "https://ply.gl/com.almaany.arar",
		"platforms": ["Android"],
		# "license": "",
	},
]


class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._clear()

	def _clear(self):
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self, filename):
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("h")

	def __len__(self):
		self._cur.execute("select count(*) from WordsTable")
		return self._cur.fetchone()[0]

	def __iter__(self):
		self._cur.execute(
			"select word, searchword, root, meaning from WordsTable"
			" order by id"
		)
		# FIXME: iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# for row in self._cur:
		for row in self._cur.fetchall():
			word = row[0]
			searchword = row[1]
			root = row[2]
			meaning = row[3]
			definition = meaning
			definition = definition.replace("|", "<br>")
			if root:
				definition += f'<br>Root: <a href="bword://{html.escape(root)}">{root}</a>'
			yield self._glos.newEntry(
				[word, searchword],
				definition,
				defiFormat="h",
			)

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
