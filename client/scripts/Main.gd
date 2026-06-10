extends Control
## The whole MVP UI, built in code so there is no fragile scene tree to maintain.
## Two screens: "move in" (create a roomie) and the apartment (live with them).

const STAT_KEYS := ["hunger", "hygiene", "energy", "mood", "health", "loneliness", "affection"]
const POLL_SECONDS := 5.0

var catalog: Dictionary = {}
var state: Dictionary = {}

var creation_root: Control
var room_root: Control
var name_edit: LineEdit
var gender_option: OptionButton
var preview_label: Label
var preview_seed: int = 0

var portrait: TextureRect
var header_label: Label
var traits_label: Label
var wallet_label: Label
var status_label: Label
var inbox_box: VBoxContainer
var bars: Dictionary = {}

var food_option: OptionButton
var activity_option: OptionButton
var gift_option: OptionButton
var chore_option: OptionButton
var job_option: OptionButton

var poll_timer: Timer


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	build_creation_screen()
	build_room_screen()
	room_root.visible = false

	poll_timer = Timer.new()
	poll_timer.wait_time = POLL_SECONDS
	poll_timer.timeout.connect(on_poll)
	add_child(poll_timer)

	var loaded = await Api.get_json("/catalog")
	if loaded["ok"]:
		catalog = loaded["data"]
		populate_catalogs()
	do_reroll()


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

	creation_root = wrap_in_scroll(box)
	add_child(creation_root)


func build_room_screen() -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)

	portrait = TextureRect.new()
	portrait.custom_minimum_size = Vector2(180, 180)
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	box.add_child(portrait)

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

	var inbox_title := Label.new()
	inbox_title.text = "Notes from them"
	inbox_title.add_theme_font_size_override("font_size", 18)
	box.add_child(inbox_title)

	inbox_box = VBoxContainer.new()
	inbox_box.add_theme_constant_override("separation", 6)
	box.add_child(inbox_box)

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


func fill_option(option: OptionButton, items: Dictionary) -> void:
	if option == null:
		return
	option.clear()
	for key in items.keys():
		option.add_item(str(key).replace("_", " "))


func selected(option: OptionButton) -> String:
	if option.selected < 0:
		return ""
	return option.get_item_text(option.selected).replace(" ", "_")


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
	Api.pet_id = result["data"]["id"]
	apply_state(result["data"])
	var visited = await Api.post_json("/pets/%s/visit" % Api.pet_id)
	if visited["ok"]:
		apply_state(visited["data"])
	creation_root.visible = false
	room_root.visible = true
	poll_timer.start()


func on_poll() -> void:
	if Api.pet_id == "":
		return
	var result = await Api.get_json("/pets/%s" % Api.pet_id)
	if result["ok"]:
		apply_state(result["data"])


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
	update_portrait()
	update_inbox()


func update_header() -> void:
	if state.is_empty():
		return
	header_label.text = "%s · %s · Lv %d" % [state["name"], str(state["relationship"]).replace("_", " "), int(state["level"])]


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
	var path := "res://assets/portraits/%s_%s.png" % [state["gender"], mood]
	if ResourceLoader.exists(path):
		portrait.texture = load(path)


func update_inbox() -> void:
	if state.is_empty():
		return
	for child in inbox_box.get_children():
		child.queue_free()
	var inbox: Array = state["inbox"]
	var count := inbox.size()
	var shown := 0
	for index in range(count - 1, -1, -1):
		if shown >= 8:
			break
		var event: Dictionary = inbox[index]
		var line := Label.new()
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		line.text = "• " + str(event["text"])
		inbox_box.add_child(line)
		shown += 1
