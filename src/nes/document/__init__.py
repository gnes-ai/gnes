import json


class BaseDocument:
    def __init__(self, doc_id: int, content: str):
        self.doc_id = doc_id
        self.content = content

    def __str__(self):
        return self.content


class JsonDocument(BaseDocument):
    def __init__(self, doc_id: int, content: str, str_field: str):
        super().__init__(doc_id, content)
        self.content = json.loads(content)
        self.str_field = str_field

    def __str__(self):
        return self.content[self.str_field]
