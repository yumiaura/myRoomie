"use strict";

// Scene layout + click behaviour. Geometry (percent) mirrors
// client/assets/scenes/manifest.json — keep them in sync if either changes.
// action kinds:
//   goto   -> switch scene (to)
//   act    -> POST path with no body (e.g. /wash, /pay-rent)
//   panel  -> open a chooser; category = catalog key, or source:"wardrobe";
//             posts path with { [field]: key }
//   notes  -> open the notes + diary panel
//   hint   -> show a localized toast (key)
//   work   -> open the work mini-game (wired in a later phase; until then a
//             plain job panel is used)
window.SCENES = {
  apartment: {
    bg: "/scenes/scene_apartment.png",
    avatar: { x: 40, y: 36, w: 20, h: 42 },  // where the roomie portrait is drawn
    hotspots: [
      { id: "roomie", label: "hot.roomie", x: 40, y: 36, w: 20, h: 42, action: { kind: "panel", title: "panel.play", category: "activities", path: "/play", field: "activity" } },
      { id: "shower", label: "hot.shower", x: 80, y: 24, w: 16, h: 50, action: { kind: "act", path: "/wash" } },
      { id: "wardrobe", label: "hot.wardrobe", x: 61, y: 24, w: 14, h: 46, action: { kind: "panel", title: "panel.wear", source: "wardrobe", path: "/wear", field: "item" } },
      { id: "broom", label: "hot.broom", x: 52, y: 70, w: 10, h: 18, action: { kind: "panel", title: "panel.chore", category: "chores", path: "/chore", field: "task" } },
      { id: "mailbox", label: "hot.mail", x: 21, y: 60, w: 9, h: 18, action: { kind: "act", path: "/pay-rent" } },
      { id: "notebook", label: "hot.notes", x: 40, y: 64, w: 11, h: 13, action: { kind: "notes" } },
      { id: "kitchen", label: "hot.kitchen", x: 33, y: 15, w: 24, h: 25, action: { kind: "hint", key: "hint.kitchen" } },
      { id: "bed", label: "hot.bed", x: 4, y: 22, w: 26, h: 30, action: { kind: "hint", key: "hint.bed" } },
      { id: "door", label: "hot.door", x: 4, y: 56, w: 15, h: 40, action: { kind: "goto", to: "street" } },
    ],
  },
  street: {
    bg: "/scenes/scene_street.png",
    hotspots: [
      { id: "grocery", label: "loc.grocery", x: 5, y: 28, w: 26, h: 48, action: { kind: "goto", to: "grocery" } },
      { id: "mall", label: "loc.mall", x: 37, y: 22, w: 26, h: 54, action: { kind: "goto", to: "mall" } },
      { id: "work", label: "loc.work", x: 69, y: 18, w: 26, h: 60, action: { kind: "goto", to: "work" } },
      { id: "home", label: "hot.home", x: 3, y: 72, w: 15, h: 26, action: { kind: "goto", to: "apartment" } },
    ],
  },
  grocery: {
    bg: "/scenes/scene_grocery.png",
    hotspots: [
      { id: "shelf", label: "panel.feed", x: 14, y: 24, w: 72, h: 54, action: { kind: "panel", title: "panel.feed", category: "foods", path: "/feed", field: "food" } },
      { id: "back", label: "btn.back", x: 2, y: 4, w: 13, h: 13, action: { kind: "goto", to: "street" } },
    ],
  },
  mall: {
    bg: "/scenes/scene_mall.png",
    hotspots: [
      { id: "gifts", label: "panel.gift", x: 9, y: 26, w: 37, h: 52, action: { kind: "panel", title: "panel.gift", category: "gifts", path: "/gift", field: "item" } },
      { id: "clothes", label: "panel.buy", x: 54, y: 26, w: 37, h: 52, action: { kind: "panel", title: "panel.buy", category: "shop", path: "/buy", field: "item" } },
      { id: "back", label: "btn.back", x: 2, y: 4, w: 13, h: 13, action: { kind: "goto", to: "street" } },
    ],
  },
  work: {
    bg: "/scenes/scene_work.png",
    hotspots: [
      { id: "desk", label: "panel.work", x: 20, y: 30, w: 60, h: 46, action: { kind: "work" } },
      { id: "back", label: "btn.back", x: 2, y: 4, w: 13, h: 13, action: { kind: "goto", to: "street" } },
    ],
  },
};
