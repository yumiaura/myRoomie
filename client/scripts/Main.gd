extends Control
## The whole MVP UI, built in code so there is no fragile scene tree to maintain.
## Two screens: "move in" (create a roomie) and the apartment (live with them).

const STAT_KEYS := ["hunger", "hygiene", "energy", "mood", "health", "loneliness", "affection"]
const POLL_SECONDS := 5.0
const SAVE_PATH := "user://myroomie.cfg"

var catalog: Dictionary = {}
var state: Dictionary = {}

var auth_root: Control
var username_edit: LineEdit
var password_edit: LineEdit
var auth_status: Label

var creation_root: Control
var room_root: Control
var name_edit: LineEdit
var gender_option: OptionButton
var preview_label: Label
var preview_seed: int = 0

var portrait: TextureRect
var outfit_overlay: TextureRect
var decor_box: HBoxContainer
var current_mood: String = ""
var header_label: Label
var traits_label: Label
var wallet_label: Label
var status_label: Label
var inbox_title: Label
var inbox_box: VBoxContainer
var diary_box: VBoxContainer
var bars: Dictionary = {}

var food_option: OptionButton
var activity_option: OptionButton
var gift_option: OptionButton
var chore_option: OptionButton
var job_option: OptionButton
var shop_option: OptionButton
var wear_option: OptionButton
var outfit_label: Label

var poll_timer: Timer
var socket: WebSocketPeer = null


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	build_auth_screen()
	build_creation_screen()
	build_room_screen()
	auth_root.visible = false
	creation_root.visible = false
	room_root.visible = false
	Api.unauthorized.connect(on_session_expired)

	poll_timer = Timer.new()
	poll_timer.wait_time = POLL_SECONDS
	poll_timer.timeout.connect(on_poll)
	add_child(poll_timer)

	var loaded = await Api.get_json("/catalog")
	if loaded["ok"]:
		catalog = loaded["data"]
		populate_catalogs()

	# Reuse a saved session token if it still works; otherwise ask to sign in.
	var saved_token := config_get("token")
	if saved_token != "":
		Api.token = saved_token
		var check = await Api.get_json("/pets")
		if check["ok"]:
			await after_login()
			return
		Api.token = ""
		config_set("token", "")
	show_auth()


# --- Screen construction --------------------------------------------------
func wrap_in_scroll(inner: Control) -> ScrollContainer:
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(margin)
	margin.add_child(inner)
	inner.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return scroll


func build_auth_screen() -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)

	var title := Label.new()
	title.text = "myRoomie"
	title.add_theme_font_size_override("font_size", 40)
	box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Sign in, or create an account to get started."
	box.add_child(subtitle)

	username_edit = LineEdit.new()
	username_edit.placeholder_text = "Username"
	box.add_child(username_edit)

	password_edit = LineEdit.new()
	password_edit.placeholder_text = "Password"
	password_edit.secret = true
	box.add_child(password_edit)

	var buttons := HBoxContainer.new()
	var login_button := Button.new()
	login_button.text = "Log in"
	login_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	login_button.pressed.connect(on_login)
	buttons.add_child(login_button)
	var register_button := Button.new()
	register_button.text = "Register"
	register_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	register_button.pressed.connect(on_register)
	buttons.add_child(register_button)
	box.add_child(buttons)

	auth_status = Label.new()
	auth_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(auth_status)

	auth_root = wrap_in_scroll(box)
	add_child(auth_root)


func build_creation_screen() -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 14)

	var title := Label.new()
	title.text = "myRoomie"
	title.add_theme_font_size_override("font_size", 40)
	box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Someone is about to move in. Who is it?"
	box.add_child(subtitle)

	name_edit = LineEdit.new()
	name_edit.placeholder_text = "Their name"
	box.add_child(name_edit)

	gender_option = OptionButton.new()
	gender_option.add_item("girl")
	gender_option.add_item("boy")
	box.add_child(gender_option)

	var reroll := Button.new()
	reroll.text = "🎲 Reroll personality"
	reroll.pressed.connect(do_reroll)
	box.add_child(reroll)

	preview_label = Label.new()
	preview_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	preview_label.text = "Rolling a personality…"
	box.add_child(preview_label)

	var move_in := Button.new()
	move_in.text = "Move in"
	move_in.pressed.connect(on_move_in)
	box.add_child(move_in)

	status_label = Label.new()
	status_label.modulate = Color(1, 0.5, 0.5)
	box.add_child(status_label)

	box.add_child(make_simple_action("Log out", on_logout))

	creation_root = wrap_in_scroll(box)
	add_child(creation_root)


func build_room_screen() -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)

	var portrait_stack := Control.new()
	portrait_stack.custom_minimum_size = Vector2(180, 180)
	portrait = TextureRect.new()
	portrait.set_anchors_preset(Control.PRESET_FULL_RECT)
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	portrait_stack.add_child(portrait)
	outfit_overlay = TextureRect.new()
	outfit_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	outfit_overlay.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	outfit_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	portrait_stack.add_child(outfit_overlay)
	box.add_child(portrait_stack)

	header_label = Label.new()
	header_label.add_theme_font_size_override("font_size", 22)
	box.add_child(header_label)

	traits_label = Label.new()
	traits_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(traits_label)

	wallet_label = Label.new()
	box.add_child(wallet_label)

	for key in STAT_KEYS:
		box.add_child(make_stat_row(key))

	box.add_child(HSeparator.new())

	food_option = make_action_row(box, "Feed", func(): on_action("/feed", {"food": selected(food_option)}))
	box.add_child(make_simple_action("Wash", func(): on_action("/wash")))
	activity_option = make_action_row(box, "Play", func(): on_action("/play", {"activity": selected(activity_option)}))
	gift_option = make_action_row(box, "Gift", func(): on_action("/gift", {"item": selected(gift_option)}))
	chore_option = make_action_row(box, "Chore", func(): on_action("/chore", {"task": selected(chore_option)}))
	job_option = make_action_row(box, "Work", func(): on_action("/work", {"job": selected(job_option)}))
	box.add_child(make_simple_action("Pay rent", func(): on_action("/pay-rent")))

	box.add_child(HSeparator.new())

	var shop_title := Label.new()
	shop_title.text = "Shop & wardrobe"
	shop_title.add_theme_font_size_override("font_size", 18)
	box.add_child(shop_title)
	shop_option = make_action_row(box, "Buy", func(): on_action("/buy", {"item": selected(shop_option)}))
	wear_option = make_action_row(box, "Wear", func(): on_action("/wear", {"item": selected(wear_option)}))
	outfit_label = Label.new()
	outfit_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(outfit_label)
	decor_box = HBoxContainer.new()
	box.add_child(decor_box)

	box.add_child(HSeparator.new())

	var inbox_header := HBoxContainer.new()
	inbox_title = Label.new()
	inbox_title.text = "Notes from them"
	inbox_title.add_theme_font_size_override("font_size", 18)
	inbox_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inbox_header.add_child(inbox_title)
	var mark_read := Button.new()
	mark_read.text = "Mark read"
	mark_read.pressed.connect(on_mark_read)
	inbox_header.add_child(mark_read)
	box.add_child(inbox_header)

	inbox_box = VBoxContainer.new()
	inbox_box.add_theme_constant_override("separation", 6)
	box.add_child(inbox_box)

	box.add_child(HSeparator.new())
	var diary_title := Label.new()
	diary_title.text = "Diary"
	diary_title.add_theme_font_size_override("font_size", 18)
	box.add_child(diary_title)
	diary_box = VBoxContainer.new()
	diary_box.add_theme_constant_override("separation", 6)
	box.add_child(diary_box)

	box.add_child(HSeparator.new())
	var session_row := HBoxContainer.new()
	var switch_button := make_simple_action("Switch roomie", on_move_out)
	switch_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	session_row.add_child(switch_button)
	var logout_button := make_simple_action("Log out", on_logout)
	logout_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	session_row.add_child(logout_button)
	box.add_child(session_row)

	room_root = wrap_in_scroll(box)
	add_child(room_root)


func make_stat_row(key: String) -> Control:
	var row := HBoxContainer.new()
	var label := Label.new()
	label.text = key.capitalize()
	label.custom_minimum_size = Vector2(110, 0)
	row.add_child(label)
	var bar := ProgressBar.new()
	bar.max_value = 100
	bar.value = 0
	bar.custom_minimum_size = Vector2(220, 0)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(bar)
	bars[key] = bar
	return row


func make_action_row(parent: VBoxContainer, label_text: String, callback: Callable) -> OptionButton:
	var row := HBoxContainer.new()
	var option := OptionButton.new()
	option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(option)
	var button := Button.new()
	button.text = label_text
	button.custom_minimum_size = Vector2(90, 0)
	button.pressed.connect(callback)
	row.add_child(button)
	parent.add_child(row)
	return option


func make_simple_action(label_text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = label_text
	button.pressed.connect(callback)
	return button


# --- Catalog --------------------------------------------------------------
func populate_catalogs() -> void:
	fill_option(food_option, catalog.get("foods", {}))
	fill_option(activity_option, catalog.get("activities", {}))
	fill_option(gift_option, catalog.get("gifts", {}))
	fill_option(chore_option, catalog.get("chores", {}))
	fill_option(job_option, catalog.get("jobs", {}))
	fill_option(shop_option, catalog.get("shop", {}))


func fill_option(option: OptionButton, items: Dictionary) -> void:
	if option == null:
		return
	option.clear()
	for key in items.keys():
		option.add_item(str(key).replace("_", " "))


func fill_option_list(option: OptionButton, items: Array) -> void:
	if option == null:
		return
	option.clear()
	for item in items:
		option.add_item(str(item).replace("_", " "))


func selected(option: OptionButton) -> String:
	if option.selected < 0:
		return ""
	return option.get_item_text(option.selected).replace(" ", "_")


# --- Auth flow ------------------------------------------------------------
func show_auth() -> void:
	auth_root.visible = true
	creation_root.visible = false
	room_root.visible = false


func show_creation() -> void:
	auth_root.visible = false
	creation_root.visible = true
	room_root.visible = false
	name_edit.text = ""
	do_reroll()


func on_register() -> void:
	var result = await Api.post_json("/auth/register", {
		"username": username_edit.text.strip_edges(),
		"password": password_edit.text,
	})
	if result["ok"]:
		auth_status.text = "Account created — now log in."
	else:
		auth_status.text = str(result["error"])


func on_login() -> void:
	var result = await Api.post_json("/auth/login", {
		"username": username_edit.text.strip_edges(),
		"password": password_edit.text,
	})
	if not result["ok"]:
		auth_status.text = str(result["error"])
		return
	Api.token = str(result["data"]["token"])
	await after_login()


func after_login() -> void:
	config_set("token", Api.token)
	# If we lived with someone last time and they still exist, walk right in.
	var saved := load_saved_pet_id()
	if saved != "":
		var existing = await Api.get_json("/pets/%s" % saved)
		if existing["ok"]:
			await enter_room(existing["data"], true)
			return
		clear_saved_pet_id()
	show_creation()


func on_logout() -> void:
	stop_live_updates()
	if Api.token != "":
		await Api.post_json("/auth/logout")  # revoke the token server-side
	Api.token = ""
	Api.pet_id = ""
	state = {}
	config_set("token", "")
	clear_saved_pet_id()
	show_auth()


func on_session_expired() -> void:
	# Fired by Api when an authenticated request comes back 401 (token expired
	# or revoked). Drop the dead session and send the player back to sign-in.
	if auth_root.visible:
		return
	stop_live_updates()
	Api.token = ""
	Api.pet_id = ""
	state = {}
	config_set("token", "")
	show_auth()
	auth_status.text = "Session expired — please sign in again."


# --- Flow -----------------------------------------------------------------
func do_reroll() -> void:
	var result = await Api.post_json("/preview", {})
	if not result["ok"]:
		preview_label.text = "(start the server to roll a personality)"
		return
	preview_seed = int(result["data"]["seed"])
	var traits: Dictionary = result["data"]["traits"]
	preview_label.text = "%s · loves %s · into %s · favourite food: %s" % [
		traits["personality"],
		str(traits["love_language"]).replace("_", " "),
		traits["hobby"],
		str(traits["favorite_food"]).replace("_", " "),
	]


func on_move_in() -> void:
	var chosen_name := name_edit.text.strip_edges()
	if chosen_name == "":
		status_label.text = "Give them a name first."
		return
	var gender := gender_option.get_item_text(gender_option.selected)
	var payload := {"name": chosen_name, "gender": gender}
	if preview_seed != 0:
		payload["seed"] = preview_seed
	var result = await Api.post_json("/pets", payload)
	if not result["ok"]:
		status_label.text = str(result["error"])
		return
	await enter_room(result["data"], true)


func enter_room(data: Dictionary, comfort_on_entry: bool) -> void:
	Api.pet_id = data["id"]
	save_pet_id(Api.pet_id)
	current_mood = ""
	apply_state(data)
	if comfort_on_entry:
		var visited = await Api.post_json("/pets/%s/visit" % Api.pet_id)
		if visited["ok"]:
			apply_state(visited["data"])
	auth_root.visible = false
	creation_root.visible = false
	room_root.visible = true
	start_live_updates()


func on_move_out() -> void:
	stop_live_updates()
	clear_saved_pet_id()
	Api.pet_id = ""
	state = {}
	current_mood = ""
	show_creation()


func config_set(key: String, value: String) -> void:
	var cfg := ConfigFile.new()
	cfg.load(SAVE_PATH)  # keep any existing keys; a missing file is fine
	cfg.set_value("session", key, value)
	cfg.save(SAVE_PATH)


func config_get(key: String) -> String:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return ""
	return str(cfg.get_value("session", key, ""))


func save_pet_id(pet_id: String) -> void:
	config_set("pet_id", pet_id)


func load_saved_pet_id() -> String:
	return config_get("pet_id")


func clear_saved_pet_id() -> void:
	config_set("pet_id", "")


func on_poll() -> void:
	if Api.pet_id == "":
		return
	var result = await Api.get_json("/pets/%s" % Api.pet_id)
	if result["ok"]:
		apply_state(result["data"])


# --- Live updates: prefer a WebSocket, fall back to polling ---------------
func start_live_updates() -> void:
	var ws_url := Api.base_url.replace("https://", "wss://").replace("http://", "ws://")
	ws_url += "/pets/%s/ws?token=%s" % [Api.pet_id, Api.token]
	socket = WebSocketPeer.new()
	if socket.connect_to_url(ws_url) != OK:
		socket = null
		poll_timer.start()  # couldn't open a socket; poll instead


func stop_live_updates() -> void:
	if socket != null:
		socket.close()
		socket = null
	poll_timer.stop()


func _process(delta: float) -> void:
	if socket == null:
		return
	socket.poll()
	var ready_state := socket.get_ready_state()
	if ready_state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count() > 0:
			var text := socket.get_packet().get_string_from_utf8()
			var data = JSON.parse_string(text)
			if typeof(data) == TYPE_DICTIONARY:
				apply_state(data)
	elif ready_state == WebSocketPeer.STATE_CLOSED:
		socket = null
		poll_timer.start()  # connection dropped; fall back to polling


func on_action(action_path: String, payload = null) -> void:
	if Api.pet_id == "":
		return
	var result = await Api.post_json("/pets/%s%s" % [Api.pet_id, action_path], payload)
	if result["ok"]:
		apply_state(result["data"])
	else:
		flash_status(str(result["error"]))


func flash_status(message: String) -> void:
	header_label.text = "⚠ " + message
	await get_tree().create_timer(2.0).timeout
	update_header()


# --- Rendering ------------------------------------------------------------
func apply_state(data: Dictionary) -> void:
	state = data
	update_header()
	update_traits()
	update_wallet()
	update_bars()
	update_wardrobe()
	update_portrait()
	update_inbox()
	update_diary()


func update_header() -> void:
	if state.is_empty():
		return
	header_label.text = "%s · %s · Lv %d" % [state["name"], str(state["relationship"]).replace("_", " "), int(state["level"])]
	var season := str(state.get("season", ""))
	if season != "":
		header_label.text += " · " + season


func update_traits() -> void:
	if state.is_empty():
		return
	var traits: Dictionary = state["traits"]
	traits_label.text = "%s · loves %s · into %s · favourite food: %s" % [
		traits["personality"],
		str(traits["love_language"]).replace("_", " "),
		traits["hobby"],
		str(traits["favorite_food"]).replace("_", " "),
	]


func update_wallet() -> void:
	if state.is_empty():
		return
	var wallet: Dictionary = state["wallet"]
	var rent_line := "rent %d" % int(wallet["rent_amount"])
	if wallet["rent_overdue"]:
		rent_line += " (OVERDUE!)"
	wallet_label.text = "💰 %d coins   ·   🏠 %s" % [int(wallet["money"]), rent_line]


func update_bars() -> void:
	if state.is_empty():
		return
	var stats: Dictionary = state["stats"]
	for key in STAT_KEYS:
		if bars.has(key) and stats.has(key):
			bars[key].value = float(stats[key])


func update_wardrobe() -> void:
	if state.is_empty():
		return
	var wardrobe: Array = state.get("wardrobe", [])
	fill_option_list(wear_option, wardrobe)
	var outfit = state.get("outfit", null)
	var worn := "nothing in particular"
	if outfit != null:
		worn = str(outfit).replace("_", " ")
	var decor: Array = state.get("decor", [])
	var decor_text := "none"
	if decor.size() > 0:
		var names := []
		for item in decor:
			names.append(str(item).replace("_", " "))
		decor_text = ", ".join(names)
	outfit_label.text = "Wearing: %s · Decor: %s" % [worn, decor_text]

	# Layer the worn outfit over the portrait, preferring per-gender art.
	var per_gender := "res://assets/portraits/outfit_%s_%s.png" % [str(outfit), str(state["gender"])]
	var generic := "res://assets/portraits/outfit_%s.png" % str(outfit)
	if outfit != null and ResourceLoader.exists(per_gender):
		outfit_overlay.texture = load(per_gender)
	elif outfit != null and ResourceLoader.exists(generic):
		outfit_overlay.texture = load(generic)
	else:
		outfit_overlay.texture = null

	# Show placed decor as little icons.
	for child in decor_box.get_children():
		child.queue_free()
	for item in decor:
		var decor_path := "res://assets/portraits/decor_%s.png" % str(item)
		if ResourceLoader.exists(decor_path):
			var icon := TextureRect.new()
			icon.texture = load(decor_path)
			icon.custom_minimum_size = Vector2(48, 48)
			icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			decor_box.add_child(icon)


func update_portrait() -> void:
	if state.is_empty():
		return
	var stats: Dictionary = state["stats"]
	var mood := "neutral"
	if float(stats["health"]) < 30.0:
		mood = "sick"
	elif float(stats["mood"]) < 35.0:
		mood = "sad"
	elif float(stats["mood"]) > 70.0:
		mood = "happy"
	if mood == current_mood:
		return
	current_mood = mood
	var path := "res://assets/portraits/%s_%s.png" % [state["gender"], mood]
	if ResourceLoader.exists(path):
		portrait.texture = load(path)
		animate_portrait()


func animate_portrait() -> void:
	# A small fade-and-pop whenever the mood (and therefore the picture) changes.
	portrait.pivot_offset = portrait.custom_minimum_size / 2.0
	portrait.modulate.a = 0.0
	portrait.scale = Vector2(0.85, 0.85)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(portrait, "modulate:a", 1.0, 0.25)
	tween.tween_property(portrait, "scale", Vector2.ONE, 0.3) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func update_inbox() -> void:
	if state.is_empty():
		return
	for child in inbox_box.get_children():
		child.queue_free()
	var inbox: Array = state["inbox"]
	var count := inbox.size()

	var unread := 0
	for event in inbox:
		if not event["seen"]:
			unread += 1
	if unread > 0:
		inbox_title.text = "Notes from them (%d new)" % unread
	else:
		inbox_title.text = "Notes from them"

	var shown := 0
	for index in range(count - 1, -1, -1):
		if shown >= 8:
			break
		var event: Dictionary = inbox[index]
		var line := Label.new()
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		if event["seen"]:
			line.text = "• " + str(event["text"])
			line.modulate = Color(0.7, 0.7, 0.7)
		else:
			line.text = "● " + str(event["text"])
		inbox_box.add_child(line)
		shown += 1


func on_mark_read() -> void:
	if Api.pet_id == "":
		return
	var result = await Api.post_json("/pets/%s/inbox/seen" % Api.pet_id)
	if result["ok"]:
		apply_state(result["data"])


func update_diary() -> void:
	if state.is_empty():
		return
	for child in diary_box.get_children():
		child.queue_free()
	var diary: Array = state.get("diary", [])
	var shown := 0
	for index in range(diary.size() - 1, -1, -1):
		if shown >= 8:
			break
		var entry: Dictionary = diary[index]
		var line := Label.new()
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		line.text = "✦ " + str(entry["text"])
		diary_box.add_child(line)
		shown += 1
