import uuid

def make_request_id() -> str:
	return uuid.uuid4().hex
