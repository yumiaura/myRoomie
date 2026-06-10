extends Node
## Thin async wrapper around the myRoomie HTTP server.
## Registered as an autoload singleton named "Api".

var base_url := "http://127.0.0.1:8000"
var pet_id := ""


## Perform a request and return {ok, data} or {ok=false, error}.
## A fresh HTTPRequest is used per call so concurrent calls never collide.
func send(method: int, path: String, payload = null) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var body := ""
	if payload != null:
		body = JSON.stringify(payload)
	var started := http.request(base_url + path, headers, method, body)
	if started != OK:
		http.queue_free()
		return {"ok": false, "error": "could not reach server"}
	var result = await http.request_completed
	http.queue_free()

	var outcome: int = result[0]
	if outcome != HTTPRequest.RESULT_SUCCESS:
		return {"ok": false, "error": "server is offline"}

	var code: int = result[1]
	var raw: PackedByteArray = result[3]
	var text := raw.get_string_from_utf8()
	var data = null
	if text != "":
		data = JSON.parse_string(text)

	if code >= 200 and code < 300:
		return {"ok": true, "data": data}

	var detail := "request failed (%d)" % code
	if typeof(data) == TYPE_DICTIONARY and data.has("detail"):
		detail = str(data["detail"])
	return {"ok": false, "error": detail, "code": code}


func get_json(path: String) -> Dictionary:
	return await send(HTTPClient.METHOD_GET, path)


func post_json(path: String, payload = null) -> Dictionary:
	return await send(HTTPClient.METHOD_POST, path, payload)
