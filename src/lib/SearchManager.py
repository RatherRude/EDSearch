from difflib import get_close_matches
import json
from typing import Any, Callable, TypedDict, final
from openai import OpenAI
from .entities import find_entities, known_entities

class DataSource(TypedDict):
    name: str
    description: str
    method: Callable

@final
class SearchManager():
    def __init__(self, llm_client: OpenAI, llm_model_name: str, embed_client: OpenAI, embed_model_name: str) -> None:
        self.llm_client = llm_client
        self.llm_model_name = llm_model_name
        self.embed_client = embed_client
        self.embed_model_name = embed_model_name
        
        self.data_sources: list[DataSource] = []

    def register_source(self, name:str, description:str, method:Callable):
        self.data_sources.append({ "name": name, "description": description, "method": method })

    def route_sources(self, query: str, context: list[dict], entities: list[dict]) -> dict[str, bool]:
        search_categories_schema: dict = { "type": "object", "properties": {}, "required": [], "additionalProperties": False }
        for source in self.data_sources:
            search_categories_schema["properties"][source["name"]] = { "type": "boolean", "title": source["description"] }
            search_categories_schema["required"].append(source["name"])
     
        completion = self.llm_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": '\n'.join([
                     "You are a search engine for the Game Elite Dangerous. Your task is to categorize the user's query into a given set of categories.",
                     "You may choose multiple categories if the answer could benefit from more than one category.",
                     "The categories are:",
                     json.dumps(search_categories_schema)
                ])},
                {"role": "user", "content": '\n'.join([
                    "<context>",
                    '\n'.join([json.dumps(item) for item in context]),
                    "</context>",
                    "<entities>",
                    '\n'.join([json.dumps(item) for item in entities]),
                    "</entities>",
                    "<query>",
                    query,
                    "</query>"
                ])},
            ],
            response_format={ 
                "type": "json_schema", 
                "json_schema": {
                    "strict": True, 
                    "name": "search_categories",
                    "schema": search_categories_schema,
                }
            }
        )
        if not completion.choices[0].message.content:
            raise Exception("No completion content")
        return json.loads(completion.choices[0].message.content)
    
    
    def run(self, query: str, context: list[dict], state: dict[str, dict]):
        found_entities = find_entities(query)
        
        categories = self.route_sources(query, context, found_entities)
        results: dict[str, Any] = {
            "context": context,
            "possible_entities": found_entities,
            "query": query,
            "sources": categories,
            "results": {}
        }
        print(results)
        
        for source in self.data_sources:
            if categories.get(source["name"], False):
                results["results"][source["name"]] = source["method"](query, context, state, found_entities)
            #else:
            #    results[source["name"]] = 'skipped'
        
        return results

