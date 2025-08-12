from django import template
import re

register = template.Library()

# -----------------------------
# Digits & date (unchanged)
# -----------------------------
URDU_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
EN_DIGITS = '0123456789'

def to_urdu_number(val):
    return ''.join(URDU_DIGITS[EN_DIGITS.index(ch)] if ch in EN_DIGITS else ch for ch in str(val))

@register.filter
def convert_urdu(val):
    """Convert English digits in string to Urdu digits."""
    return to_urdu_number(val)

URDU_MONTHS = {
    "January": "جنوری", "February": "فروری", "March": "مارچ", "April": "اپریل",
    "May": "مئی", "June": "جون", "July": "جولائی", "August": "اگست",
    "September": "ستمبر", "October": "اکتوبر", "November": "نومبر", "December": "دسمبر"
}

@register.filter
def convert_urdu_date(date):
    """Convert a date (datetime/date) to Urdu-formatted string."""
    day = to_urdu_number(date.day)
    month = URDU_MONTHS[date.strftime('%B')]
    year = to_urdu_number(date.year)
    return f"{year} {day}, {month}"

# -----------------------------
# Subject translation
# -----------------------------
# 1) Base subjects (parent level)
PARENT_MAP = {
    "mathematics": "ریاضی",
    "math": "ریاضی",
    "general mathematics": "جنرل ریاضی",
    "further mathematics": "اعلیٰ ریاضی",
    "english": "انگریزی",
    "science": "سائنس",
    "general science": "جنرل سائنس",
    "physics": "طبیعیات",
    "chemistry": "کیمسٹری",
    "biology": "حیاتیات",
    "botany": "علم نباتات",
    "zoology": "علم حیوانات",
    "computer science": "کمپیوٹر سائنس",
    "information technology": "انفارمیشن ٹیکنالوجی",
    "islamic studies": "اسلامیات",
    "pakistan studies": "مطالعہ پاکستان",
    "history": "تاریخ",
    "geography": "جغرافیہ",
    "civics": "شہریت",
    "economics": "معاشیات",
    "business studies": "کاروباری مطالعہ",
    "commerce": "کامرس",
    "accounting": "محاسبہ",
    "statistics": "شماریات",
    "environmental science": "ماحولیاتی سائنس",
    "social studies": "معاشرتی علوم",
    "education": "تعلیم",
    "philosophy": "فلسفہ",
    "psychology": "نفسیات",
    "sociology": "معاشرتیات",
    "law": "قانون",
    "library science": "لائبریری سائنس",
    "food and nutrition": "خوراک و غذائیت",
    "engineering drawing": "انجینئرنگ ڈرائنگ",
    "electronics": "الیکٹرانکس",
    "art": "فن",
    "drawing": "ڈرائنگ",
    "physical education": "جسمانی تعلیم",
    "health education": "صحت کی تعلیم",
    "moral education": "اخلاقی تعلیم",
    "music": "موسیقی",
    "arabic": "عربی",
    "persian": "فارسی",
    "punjabi": "پنجابی",
    "sindhi": "سندھی",
    "pashto": "پشتو",
    "balochi": "بلوچی",
    "french": "فرانسیسی",
    "german": "جرمن",
    "chinese": "چینی",
    "urdu": "اردو",
    "islamic history": "اسلامی تاریخ",
}

# 2) Sub-branches per parent (common school/board syllabi)
SUB_MAP = {
    # English
    "english": {
        "language": "انگریزی زبان",
        "literature": "انگریزی ادب",
        "grammar": "گرامر",
        "composition": "انشاء",
        "comprehension": "تفہیمِ مطلب",
        "reading": "مطالعہ",
        "writing": "تحریر",
        "speaking": "گفتگو",
        "listening": "سماعت",
        "phonics": "صوتیات",
        "spelling": "املا",
        "essay": "مضمون نویسی",
        "precis": "خلاصہ نویسی",
        "translation": "ترجمہ",
    },
    # Urdu
    "urdu": {
        "language": "اردو زبان",
        "literature": "اردو ادب",
        "grammar": "قواعد",
        "essay": "مضمون نویسی",
        "comprehension": "تفہیم",
        "translation": "ترجمہ",
    },
    # Mathematics
    "mathematics": {
        "arithmetic": "حساب",
        "algebra": "الجبرہ",
        "geometry": "ہندسہ",
        "trigonometry": "مثلثات",
        "calculus": "حسابِ اوّل/کلکیولس",
        "analytic geometry": "تجزیاتی ہندسہ",
        "number theory": "نظریہ اعداد",
        "set theory": "نظریہ مجموعہ",
        "probability": "امکان",
        "statistics": "شماریات",
        "vectors": "سمتیات",
        "matrices": "میٹرکس",
    },
    # Physics
    "physics": {
        "mechanics": "میکانیکیات",
        "electricity": "برقیات",
        "magnetism": "مقناطیسیت",
        "electromagnetism": "برقی مقناطیسیت",
        "optics": "نوریات",
        "waves": "امواج",
        "thermodynamics": "حرکیاتِ حرارت",
        "modern physics": "جدید طبیعیات",
        "atomic physics": "جوہری طبیعیات",
        "nuclear physics": "ایٹمی طبیعیات",
    },
    # Chemistry
    "chemistry": {
        "organic": "نامیاتی کیمسٹری",
        "inorganic": "غیر نامیاتی کیمسٹری",
        "physical": "طبعی کیمسٹری",
        "analytical": "تجزیاتی کیمسٹری",
        "biochemistry": "حیات کیمسٹری",
    },
    # Biology
    "biology": {
        "cell biology": "علم خلویات",
        "genetics": "وراثیات",
        "microbiology": "خرد حیاتیات",
        "human biology": "انسانی حیاتیات",
        "ecology": "ماحولیات",
        "botany": "علم نباتات",
        "zoology": "علم حیوانات",
    },
    # Computer Science / IT
    "computer science": {
        "programming": "برنامہ نویسی",
        "data structures": "ڈھانچےِ معلومات",
        "algorithms": "الگورتھمز",
        "databases": "ڈیٹابیس",
        "operating systems": "عملیاتی نظام",
        "networking": "نیٹ ورکنگ",
        "web development": "ویب ڈویلپمنٹ",
        "artificial intelligence": "مصنوعی ذہانت",
        "machine learning": "مشین لرننگ",
        "cyber security": "سائبر سکیورٹی",
    },
    # Islamic / Pakistan Studies
    "islamic studies": {
        "quran": "قرآن",
        "hadith": "حدیث",
        "fiqh": "فقہ",
        "seerah": "سیرت",
        "islamic history": "اسلامی تاریخ",
        "ethics": "اخلاقیات",
    },
    "pakistan studies": {
        "history": "پاکستان کی تاریخ",
        "geography": "پاکستان کا جغرافیہ",
        "civics": "شہریتِ پاکستان",
        "economy": "معیشتِ پاکستان",
    },
}

# Extra common aliases that appear in school data
ALIASES = {
    "english language": "انگریزی زبان",
    "english literature": "انگریزی ادب",
    "urdu language": "اردو زبان",
    "urdu literature": "اردو ادب",
    "islamiat": "اسلامیات",
    "islamiyat": "اسلامیات",
    "pak studies": "مطالعہ پاکستان",
    "pakistan affairs": "مطالعہ پاکستان",
    "computer": "کمپیوٹر سائنس",
    "i.t.": "انفارمیشن ٹیکنالوجی",
    "it": "انفارمیشن ٹیکنالوجی",
}

DELIMS = r"\s*[:/\-\u2013\u2014()]\s*"  # :, /, -, en/em dash, ( )

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def _split_parent_child(title: str):
    """
    Split subject into parent and (optional) sub-branch.
    Supports: 'Parent - Child', 'Parent: Child', 'Parent (Child)'
    """
    s = _norm(title)
    # Try direct alias first
    if s in ALIASES:
        return None, ALIASES[s]  # already fully translated

    parts = re.split(DELIMS, s)
    if len(parts) >= 2:
        parent = parts[0]
        child = " ".join(parts[1:]).strip()
        return parent, child
    return s, None

def _translate_parent(p: str) -> str:
    if not p:
        return None
    # try direct parent map
    if p in PARENT_MAP:
        return PARENT_MAP[p]
    # small heuristics
    if p.endswith(" studies") and p[:-8] in PARENT_MAP:
        return PARENT_MAP[p[:-8]] + " (" + "مطالعہ" + ")"
    return None

def _translate_child(parent_key: str, child: str) -> str:
    if not child:
        return None
    c = _norm(child)
    # direct alias like "english language"
    if c in ALIASES:
        return ALIASES[c]
    # per-parent sub-map
    pk = parent_key or ""
    if pk in SUB_MAP:
        # exact sub match
        if c in SUB_MAP[pk]:
            return SUB_MAP[pk][c]
        # loose matches: e.g., "modern" -> "modern physics"
        for key, ur in SUB_MAP[pk].items():
            if c.startswith(key):
                return ur
    # generic fallbacks
    generic = {
        "language": "زبان",
        "literature": "ادب",
        "grammar": "گرامر",
        "composition": "انشاء",
        "comprehension": "تفہیم",
        "theory": "نظریہ",
        "practical": "عملی",
    }
    if c in generic:
        return generic[c]
    return None

@register.filter
def subject_to_urdu(title):
    """
    Translate English subject names to Urdu, with sub-branch support.
    Examples:
      - "English Language" -> "انگریزی زبان"
      - "Mathematics - Algebra" -> "ریاضی (الجبرہ)"
      - "Physics: Optics" -> "طبیعیات (نوریات)"
      - "Computer Science (Programming)" -> "کمپیوٹر سائنس (برنامہ نویسی)"
      - "Pakistan Studies: History" -> "مطالعہ پاکستان (پاکستان کی تاریخ)"
    """
    if not title:
        return title

    # First try full-alias & simple exact map
    s = _norm(title)
    if s in ALIASES:
        return ALIASES[s]
    if s in PARENT_MAP:
        return PARENT_MAP[s]

    parent_key, child_raw = _split_parent_child(title)

    # If alias returned a direct Urdu phrase (parent_key None), just use that
    if parent_key is None and child_raw:
        return child_raw

    ur_parent = _translate_parent(parent_key) if parent_key else None
    ur_child = _translate_child(parent_key, child_raw) if child_raw else None

    # Compose results smartly
    if ur_parent and ur_child:
        return f"{ur_parent} ({ur_child})"
    if ur_child and not ur_parent:
        # we know child but not parent -> just child
        return ur_child
    if ur_parent and not ur_child and child_raw:
        # have parent translation, show raw child in Urdu digits if numeric
        return f"{ur_parent} ({child_raw})"
    # nothing matched -> return original
    return title
