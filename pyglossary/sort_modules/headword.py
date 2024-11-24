from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.icu_types import T_Collator
	from pyglossary.sort_keys_types import (
		SortKeyMakerType,
		SortKeyType,
		SQLiteSortKeyType,
	)


desc = "Headword"


def normal(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	return sortKey


def locale(
	collator: T_Collator,  # noqa: F821
) -> SortKeyMakerType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> bytes:
		return cSortKey(words[0])

	def warpper(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
		return sortKey

	return warpper


def sqlite(sortEncoding: str = "utf-8", **_options) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"headword",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def sqlite_locale(
	collator: T_Collator,  # noqa: F821
) -> Callable[..., SQLiteSortKeyType]:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> bytes:
		return cSortKey(words[0])

	return lambda **_options: [("sortkey", "BLOB", sortKey)]
