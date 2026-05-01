// Display labels and emoji icons for canonical menu items.

type ItemMeta = { en: string; si?: string; ta?: string; icon: string };

export const ITEM_LABELS: Record<string, ItemMeta> = {
  // Sri Lankan core
  rice:               { en: "Rice",                   si: "bath",                       icon: "rice" },
  dhal_curry:         { en: "Dhal Curry",             si: "parippu",                    icon: "dhal" },
  pol_sambol:         { en: "Pol Sambol",             si: "pol sambola",                icon: "coconut" },
  fish_ambul_thiyal:  { en: "Fish Ambul Thiyal",                                        icon: "fish" },
  chicken_curry:      { en: "Chicken Curry",          si: "kukulmas kariya",            icon: "chicken" },
  cashew_curry:       { en: "Cashew Curry",           si: "kaju kariya",                icon: "cashew" },
  brinjal_moju:       { en: "Brinjal Moju",           si: "wambatu moju",               icon: "brinjal" },
  seer_fish_curry:    { en: "Seer Fish Curry",                                          icon: "seer" },
  polos_curry:        { en: "Polos Curry",            si: "polos kariya",               icon: "jackfruit" },
  kandyan_beef_curry: { en: "Kandyan Beef Curry",                                       icon: "beef" },
  // Heritage / Burgher
  lamprais:           { en: "Lamprais",                                                 icon: "parcel" },
  milk_rice:          { en: "Milk Rice (Kiribath)",   si: "kiribath",                   icon: "kiribath" },
  watalappan:         { en: "Watalappan",                                               icon: "pudding" },
  love_cake:          { en: "Love Cake",                                                icon: "cake" },
  // Short eats / kottu
  string_hoppers:     { en: "String Hoppers",         si: "indi appa",                  icon: "noodle" },
  egg_hopper:         { en: "Egg Hopper",             si: "bittara appa",               icon: "egg" },
  devilled_chicken:   { en: "Devilled Chicken",                                         icon: "chili" },
  chicken_kottu:      { en: "Chicken Kottu",          si: "kottu roti",                 icon: "kottu" },
  cheese_kottu:       { en: "Cheese Kottu",                                             icon: "cheese" },
  egg_kottu:          { en: "Egg Kottu",                                                icon: "egg" },
  // Asian fusion
  nasi_goreng:        { en: "Nasi Goreng",                                              icon: "rice" },
  pad_thai:           { en: "Pad Thai",                                                 icon: "noodle" },
  thai_red_curry:     { en: "Thai Red Curry",                                           icon: "chili" },
  thai_green_curry:   { en: "Thai Green Curry",                                         icon: "leaf" },
  chinese_fried_rice: { en: "Chinese Fried Rice",                                       icon: "wok" },
  // Drinks
  king_coconut:       { en: "King Coconut",           si: "thambili",                   icon: "coconut" },
  ceylon_tea:         { en: "Ceylon Tea",             si: "te",                         icon: "tea" },
  lion_lager:         { en: "Lion Lager",                                               icon: "beer" },
  faluda:             { en: "Faluda",                                                   icon: "drink" },
};

export function itemLabel(key: string): string {
  return ITEM_LABELS[key]?.en ?? key.replace(/_/g, " ");
}

const EMOJI_BY_ICON: Record<string, string> = {
  rice: "rice", dhal: "dhal", coconut: "coconut", fish: "fish", chicken: "chicken",
  cashew: "cashew", brinjal: "brinjal", seer: "seer", jackfruit: "jackfruit",
  beef: "beef", parcel: "parcel", kiribath: "kiribath", pudding: "pudding", cake: "cake",
  noodle: "noodle", egg: "egg", chili: "chili", kottu: "kottu", cheese: "cheese",
  leaf: "leaf", wok: "wok", tea: "tea", beer: "beer", drink: "drink",
};

const EMOJI: Record<string, string> = {
  rice: "🍚",
  dhal: "🟡",
  coconut: "🥥",
  fish: "🐟",
  chicken: "🍗",
  cashew: "🥜",
  brinjal: "🍆",
  seer: "🐠",
  jackfruit: "🌳",
  beef: "🥩",
  parcel: "🍱",
  kiribath: "🍙",
  pudding: "🍮",
  cake: "🍰",
  noodle: "🍜",
  egg: "🍳",
  chili: "🌶",
  kottu: "🍲",
  cheese: "🧀",
  leaf: "🥬",
  wok: "🍡",
  tea: "🍵",
  beer: "🍺",
  drink: "🥤",
};

export function itemIcon(key: string): string {
  const meta = ITEM_LABELS[key];
  if (!meta) return "🍽️";
  return EMOJI[meta.icon] ?? "🍽️";
}
