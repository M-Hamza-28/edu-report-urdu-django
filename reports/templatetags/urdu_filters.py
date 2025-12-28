from django import template
import re

register = template.Library()

# -----------------------------
# Digits & date
# -----------------------------
URDU_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
EN_DIGITS = '0123456789'

def to_urdu_number(val):
    return ''.join(URDU_DIGITS[EN_DIGITS.index(ch)] if ch in EN_DIGITS else ch for ch in str(val))

@register.filter(name="report_label")
def report_label(value: str) -> str:
    """
    Translate 'Report' to Urdu for the PDF header.
    Use as: {{ "Report"|report_label }}
    """
    text = (str(value) or "").strip().lower()
    if text.startswith("report"):
        return "کارکردگی نامہ"
    return value

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
    """
    Convert a date (datetime/date) to Urdu-formatted string.
    Natural Urdu order: DAY MONTH YEAR, all in Urdu digits.
    Example: ۲۹ ستمبر ۲۰۲۵
    """
    day = to_urdu_number(date.day)
    month = URDU_MONTHS[date.strftime('%B')]
    year = to_urdu_number(date.year)
    return f"{day} {month} {year}"

# -----------------------------
# Simple arithmetic for templates
# -----------------------------
@register.filter
def percentage(obtained, total):
    """
    Compute (obtained / total) * 100 safely for templates.
    Usage:
      {{ obtained|percentage:total|floatformat:"2" }}
    Returns 0 if values are missing or total is 0.
    """
    try:
        mo = float(obtained)
        tm = float(total)
        if tm <= 0:
            return 0.0
        return (mo / tm) * 100.0
    except Exception:
        return 0.0

# -----------------------------
# Subject translation
# -----------------------------
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

SUB_MAP = {
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
    "urdu": {
        "language": "اردو زبان",
        "literature": "اردو ادب",
        "grammar": "قواعد",
        "essay": "مضمون نویسی",
        "comprehension": "تفہیم",
        "translation": "ترجمہ",
    },
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
    "chemistry": {
        "organic": "نامیاتی کیمسٹری",
        "inorganic": "غیر نامیاتی کیمسٹری",
        "physical": "طبعی کیمسٹری",
        "analytical": "تجزیاتی کیمسٹری",
        "biochemistry": "حیات کیمسٹری",
    },
    "biology": {
        "cell biology": "علم خلویات",
        "genetics": "وراثیات",
        "microbiology": "خرد حیاتیات",
        "human biology": "انسانی حیاتیات",
        "ecology": "ماحولیات",
        "botany": "علم نباتات",
        "zoology": "علم حیوانات",
    },
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

DELIMS = r"\s*[:/\-\u2013\u2014()]\s*"

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower().replace("—", "-").replace("–", "-"))

def _split_parent_child(title: str):
    s = _norm(title)
    if s in ALIASES:
        return None, ALIASES[s]
    parts = re.split(DELIMS, s)
    if len(parts) >= 2:
        parent = parts[0]
        child = " ".join(parts[1:]).strip()
        return parent, child
    return s, None

def _translate_parent(p: str) -> str:
    if not p:
        return None
    if p in PARENT_MAP:
        return PARENT_MAP[p]
    if p.endswith(" studies") and p[:-8] in PARENT_MAP:
        return PARENT_MAP[p[:-8]] + " (" + "مطالعہ" + ")"
    return None

def _translate_child(parent_key: str, child: str) -> str:
    if not child:
        return None
    c = _norm(child)
    if c in ALIASES:
        return ALIASES[c]
    pk = parent_key or ""
    if pk in SUB_MAP:
        if c in SUB_MAP[pk]:
            return SUB_MAP[pk][c]
        for key, ur in SUB_MAP[pk].items():
            if c.startswith(key):
                return ur
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
    if not title:
        return title
    s = _norm(title)
    if s in ALIASES:
        return ALIASES[s]
    if s in PARENT_MAP:
        return PARENT_MAP[s]
    parent_key, child_raw = _split_parent_child(title)
    if parent_key is None and child_raw:
        return child_raw
    ur_parent = _translate_parent(parent_key) if parent_key else None
    ur_child = _translate_child(parent_key, child_raw) if child_raw else None
    if ur_parent and ur_child:
        return f"{ur_parent} ({ur_child})"
    if ur_child and not ur_parent:
        return ur_child
    if ur_parent and not ur_child and child_raw:
        return f"{ur_parent} ({child_raw})"
    return title

# -----------------------------
# Term / Exam Type / Session labels (Urdu)
# -----------------------------
@register.filter
def term_to_urdu(term: str) -> str:
    s = _norm(term)
    mapping = {
        "1st term": "پہلی مدت", "first term": "پہلی مدت", "term 1": "پہلی مدت",
        "2nd term": "دوسری مدت", "second term": "دوسری مدت", "term 2": "دوسری مدت",
        "3rd term": "تیسری مدت", "third term": "تیسری مدت", "term 3": "تیسری مددت",
        "final term": "حتمی مدت", "final-term": "حتمی مدت",
    }
    return mapping.get(s, term)

@register.filter
def exam_type_to_urdu(exam_type: str) -> str:
    s = _norm(exam_type)
    mapping = {
        "mid-term": "نصف سالانہ", "mid term": "نصف سالانہ", "midterm": "نصف سالانہ",
        "final": "سالانہ", "annual": "سالانہ", "final term": "حتمی مدت",
        "monthly tests": "ماہانہ امتحانات", "monthly test": "ماہانہ امتحان",
        "weekly tests": "ہفتہ وار امتحانات", "weekly test": "ہفتہ وار امتحان",
        "tests week": "امتحانات کا ہفتہ", "quiz": "مختصر امتحان", "quizzes": "مختصر امتحانات",
        "unit test": "جزوی امتحان", "unit tests": "جزوی امتحانات",
        "class test": "جماعتی امتحان", "class tests": "جماعتی امتحانات",
        "assignment": "مشق تحریری", "assignments": "مشق تحریریں",
        "oral": "زبانی امتحان", "practical": "عملی امتحان",
    }
    return mapping.get(s, exam_type)

@register.filter
def session_to_urdu(session) -> str:
    prefix = "تعلیمی سال "
    year = getattr(session, "year", None)
    if isinstance(year, int):
        return f"{prefix}{to_urdu_number(year)}–{to_urdu_number(year + 1)}"
    name = getattr(session, "name", None)
    if isinstance(name, str) and name.strip():
        s = name.strip()
        low = s.lower()
        for lead in ("session", "academic year", "academic-year", "ay"):
            if low.startswith(lead):
                s = s[len(lead):].lstrip(" :ـ-–—-")
                break
        s = " ".join(to_urdu_number(tok) for tok in s.split())
        return prefix + s if s else prefix.strip()
    if isinstance(session, str):
        s = session.strip()
        low = s.lower()
        for lead in ("session", "academic year", "academic-year", "ay"):
            if low.startswith(lead):
                s = s[len(lead):].lstrip(" :ـ-–—-")
                break
        s = " ".join(to_urdu_number(tok) for tok in s.split())
        return prefix + s if s else prefix.strip()
    sid = getattr(session, "id", None)
    if sid is not None:
        return f"{prefix}{to_urdu_number(sid)}"
    return prefix.strip()
