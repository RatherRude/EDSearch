from typing import Literal
from pydantic import BaseModel

from ..Database import pg_connection


class AutocompleteArgs(BaseModel):
    input: str
    kinds: list[
        Literal[
            "station",
            "system",
            "body",
            "commodity",
            "module",
            "ship",
            "factions",
            "powers",
            "allegance",
        ]
    ] = [
        "station",
        "system",
        "body",
        "commodity",
        "module",
        "ship",
        "factions",
        "powers",
        "allegance",
    ]
    limit: int = 10

    model_config = {
        "json_schema_extra": {
            "example": {
                "input": "apha centrii",
                "lists": [
                    "station",
                    "system",
                    "body",
                    "commodity",
                    "module",
                    "ship",
                    "factions",
                    "powers",
                    "allegance",
                ],
            }
        }
    }


class AutocompleteMatch(BaseModel):
    name: str
    type: str | None
    systemname: str | None
    kind: str | None
    written_similarity: float


class AutocompleteResult(BaseModel):
    query: dict
    result: list[AutocompleteMatch]


# NOTE: maybe we should use the metaphone similarity in addition to the written similarity for STT queries
# but we should also consider the performance implications of this and how to index
#
# SELECT
#    id, name, systemname, SIMILARITY(
#    METAPHONE(name, 20),
#    METAPHONE(%s, 20)
# ) as phonetic_similarity, SIMILARITY(
#    name,
#    %s
# ) as written_similarity
# FROM stations
# ORDER BY SIMILARITY(
#    METAPHONE(name, 20),
#    METAPHONE(%s, 20)
# ) DESC, SIMILARITY(
#    name,
#    %s
# ) DESC
# Limit %s;


def api_autocomplete(args: AutocompleteArgs):
    with pg_connection() as (db, cur):
        cur.execute(
            f"""
                SELECT
                    id, name, type, systemname, SIMILARITY(
                    name,
                    %s
                ) as written_similarity
                FROM autocomplete
                WHERE %s % name 
                    and type = ANY(%s)
                ORDER BY written_similarity DESC
                Limit %s;
            """,
            (
                args.input,
                args.input,
                args.kinds,
                args.limit,
            ),
        )
        results = cur.fetchall()

    return AutocompleteResult.model_validate(
        {
            "query": {
                "input": args.input,
                "kinds": args.kinds,
            },
            "results": [
                AutocompleteMatch.model_validate({**result}) for result in results
            ],
        }
    )


def api_entity_recognition(args: AutocompleteArgs):
    with pg_connection() as (db, cur):
        # entity recognition is an inverse text search, where the document is the input and the query is the rows
        # we need to split the input into words
        # find the similarity between the words in the input and the rows using <<%
        # sum the similarities for each row
        # order by the sum of similarities
        cur.execute(
            f"""
                with words as (
                    select regexp_split_to_table(lower(%s), '[^[:alnum:]]+') as word
                ), entities as (
                    SELECT DISTINCT name, type, kind FROM autocomplete
                )
                select
                    name, word, type, kind, sum(strict_word_similarity(name, word)) as matches
                from entities, words
                where name <<% word
                group by name, word, type, kind
                order by matches desc
            """,
            (
                args.input,
                args.kinds,
                args.limit,
            ),
        )
        results = cur.fetchall()

    return AutocompleteResult.model_validate(
        {
            "query": {
                "input": args.input,
                "kinds": args.kinds,
            },
            "results": [
                AutocompleteMatch.model_validate({**result}) for result in results
            ],
        }
    )
