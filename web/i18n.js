"use strict";

// Languages the switcher offers. Add a code here plus a block in I18N to extend.
const LANGS = ["en", "ru"];

const I18N = {
  en: {
    "app.title": "myRoomie",
    "auth.subtitle": "Sign in, or create an account to get started.",
    "auth.username": "Username", "auth.password": "Password",
    "btn.login": "Log in", "btn.register": "Register",
    "auth.created": "Account created — now log in.",
    "auth.expired": "Session expired — please sign in again.",
    "create.subtitle": "Someone is about to move in. Who is it?",
    "create.name": "Their name", "create.reroll": "🎲 Reroll personality",
    "create.movein": "Move in", "create.rolling": "Rolling a personality…",
    "create.needname": "Give them a name first.",
    "gender.girl": "girl", "gender.boy": "boy",
    "btn.logout": "Log out", "btn.switch": "Switch roomie", "btn.back": "Back", "btn.close": "Close",
    "loc.apartment": "Studio", "loc.street": "Outside", "loc.grocery": "Grocery", "loc.mall": "Mall", "loc.work": "Work",
    "hot.roomie": "Spend time", "hot.shower": "Freshen up", "hot.wardrobe": "Get dressed",
    "hot.kitchen": "Kitchen", "hot.mail": "Pay rent", "hot.notes": "Notes & diary", "hot.broom": "Tidy up",
    "hot.door": "Go outside", "hot.bed": "Rest spot", "hot.home": "Home",
    "panel.play": "What shall we do?", "panel.feed": "Pick something to eat", "panel.gift": "Choose a gift",
    "panel.buy": "Shop", "panel.chore": "Tidy up", "panel.wear": "Wardrobe", "panel.work": "Pick a shift",
    "panel.empty": "Nothing here yet.",
    "notes.title": "Notes", "diary.title": "Diary", "notes.markread": "Mark read", "notes.new": "new",
    "hud.coins": "coins", "hud.rent": "rent", "hud.overdue": "OVERDUE!",
    "hint.kitchen": "Groceries are bought at the store down the street.",
    "hint.bed": "They rest here — energy returns over time.",
    "stat.hunger": "Hunger", "stat.hygiene": "Hygiene", "stat.energy": "Energy", "stat.mood": "Mood",
    "stat.health": "Health", "stat.loneliness": "Loneliness", "stat.affection": "Affection",
    "rel.new_acquaintance": "new acquaintance", "rel.getting_to_know": "getting to know", "rel.friends": "friends",
    "rel.close": "close", "rel.sweethearts": "sweethearts", "rel.inseparable": "inseparable",
    "season.winter": "winter", "season.spring": "spring", "season.summer": "summer", "season.autumn": "autumn",
    "toast.offline": "Server is offline.", "toast.done": "Done.",
    "mg.title": "On shift", "mg.cancel": "Leave", "mg.score": "Orders", "mg.time": "Time",
    "mg.win": "Nice shift — you got paid!", "mg.lose": "The shift flopped — no pay.",
    "mg.tootired": "Too tired for this shift.",
    "instant_noodles": "Instant noodles", "home_cooked": "Home-cooked meal", "sushi": "Sushi",
    "pancakes": "Pancakes", "salad": "Salad", "cake": "Cake",
    "flowers": "Flowers", "plushie": "Plushie", "book": "Book", "jewelry": "Jewelry",
    "concert_tickets": "Concert tickets", "handwritten_letter": "Handwritten letter",
    "video_games": "Video games", "walk_in_park": "Walk in the park", "movie_night": "Movie night",
    "board_game": "Board game", "dance": "Dance",
    "dishes": "Dishes", "laundry": "Laundry", "vacuum": "Vacuum", "groceries": "Sort groceries",
    "freelance_art": "Freelance art", "barista_shift": "Barista shift", "tutoring": "Tutoring", "delivery": "Delivery",
    "cozy_sweater": "Cozy sweater", "summer_dress": "Summer dress", "denim_jacket": "Denim jacket",
    "pajamas": "Pajamas", "houseplant": "Houseplant", "string_lights": "String lights",
    "bookshelf": "Bookshelf", "rug": "Rug",
  },
  ru: {
    "app.title": "myRoomie",
    "auth.subtitle": "Войдите или создайте аккаунт, чтобы начать.",
    "auth.username": "Логин", "auth.password": "Пароль",
    "btn.login": "Войти", "btn.register": "Регистрация",
    "auth.created": "Аккаунт создан — теперь войдите.",
    "auth.expired": "Сессия истекла — войдите снова.",
    "create.subtitle": "Скоро кто-то заселится. Кто это?",
    "create.name": "Имя", "create.reroll": "🎲 Перебросить характер",
    "create.movein": "Заселить", "create.rolling": "Бросаем характер…",
    "create.needname": "Сначала дайте имя.",
    "gender.girl": "девушка", "gender.boy": "парень",
    "btn.logout": "Выйти", "btn.switch": "Сменить соседа", "btn.back": "Назад", "btn.close": "Закрыть",
    "loc.apartment": "Студия", "loc.street": "Улица", "loc.grocery": "Продукты", "loc.mall": "Молл", "loc.work": "Работа",
    "hot.roomie": "Провести время", "hot.shower": "Помыться", "hot.wardrobe": "Переодеться",
    "hot.kitchen": "Кухня", "hot.mail": "Оплатить аренду", "hot.notes": "Записки и дневник", "hot.broom": "Прибраться",
    "hot.door": "Выйти на улицу", "hot.bed": "Место отдыха", "hot.home": "Домой",
    "panel.play": "Чем займёмся?", "panel.feed": "Чем покормить", "panel.gift": "Выберите подарок",
    "panel.buy": "Магазин", "panel.chore": "Уборка", "panel.wear": "Гардероб", "panel.work": "Выберите смену",
    "panel.empty": "Здесь пока пусто.",
    "notes.title": "Записки", "diary.title": "Дневник", "notes.markread": "Прочитано", "notes.new": "новых",
    "hud.coins": "монет", "hud.rent": "аренда", "hud.overdue": "ПРОСРОЧЕНО!",
    "hint.kitchen": "Продукты покупаются в магазине дальше по улице.",
    "hint.bed": "Здесь отдыхают — энергия восстанавливается со временем.",
    "stat.hunger": "Голод", "stat.hygiene": "Чистота", "stat.energy": "Энергия", "stat.mood": "Настроение",
    "stat.health": "Здоровье", "stat.loneliness": "Одиночество", "stat.affection": "Привязанность",
    "rel.new_acquaintance": "новое знакомство", "rel.getting_to_know": "узнаёте друг друга", "rel.friends": "друзья",
    "rel.close": "близкие", "rel.sweethearts": "влюблённые", "rel.inseparable": "неразлучны",
    "season.winter": "зима", "season.spring": "весна", "season.summer": "лето", "season.autumn": "осень",
    "toast.offline": "Сервер недоступен.", "toast.done": "Готово.",
    "mg.title": "На смене", "mg.cancel": "Уйти", "mg.score": "Заказы", "mg.time": "Время",
    "mg.win": "Отличная смена — тебе заплатили!", "mg.lose": "Смена не задалась — без оплаты.",
    "mg.tootired": "Слишком устал(а) для смены.",
    "instant_noodles": "Доширак", "home_cooked": "Домашняя еда", "sushi": "Суши",
    "pancakes": "Блинчики", "salad": "Салат", "cake": "Торт",
    "flowers": "Цветы", "plushie": "Игрушка", "book": "Книга", "jewelry": "Украшение",
    "concert_tickets": "Билеты на концерт", "handwritten_letter": "Записка от руки",
    "video_games": "Видеоигры", "walk_in_park": "Прогулка в парке", "movie_night": "Киновечер",
    "board_game": "Настолка", "dance": "Танцы",
    "dishes": "Помыть посуду", "laundry": "Постирать", "vacuum": "Пропылесосить", "groceries": "Разобрать продукты",
    "freelance_art": "Фриланс-арт", "barista_shift": "Смена бариста", "tutoring": "Репетиторство", "delivery": "Доставка",
    "cozy_sweater": "Уютный свитер", "summer_dress": "Летнее платье", "denim_jacket": "Джинсовка",
    "pajamas": "Пижама", "houseplant": "Растение", "string_lights": "Гирлянда",
    "bookshelf": "Книжная полка", "rug": "Ковёр",
  },
};

function humanize(key) {
  return String(key).replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

let currentLang = (function () {
  const saved = localStorage.getItem("lang");
  if (saved && LANGS.includes(saved)) return saved;
  return (navigator.language || "en").toLowerCase().startsWith("ru") ? "ru" : "en";
})();

const changeListeners = [];

window.I18n = {
  LANGS,
  getLang: () => currentLang,
  setLang(lang) {
    if (!LANGS.includes(lang)) return;
    currentLang = lang;
    localStorage.setItem("lang", lang);
    for (const cb of changeListeners) cb(lang);
  },
  onChange(cb) { changeListeners.push(cb); },
  t(key) {
    const dict = I18N[currentLang] || I18N.en;
    return dict[key] || I18N.en[key] || humanize(key);
  },
};
