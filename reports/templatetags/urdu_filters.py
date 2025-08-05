from django import template

register = template.Library()

# Urdu digit mapping
URDU_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
EN_DIGITS = '0123456789'

def to_urdu_number(val):
    return ''.join(URDU_DIGITS[EN_DIGITS.index(ch)] if ch in EN_DIGITS else ch for ch in str(val))

@register.filter
def convert_urdu(val):
    """Convert English digits in string to Urdu digits."""
    return to_urdu_number(val)

# Optional: Urdu date conversion (you can expand this as needed)
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

# Subject translation map
SUBJECT_URDU_MAP = {
     "Mathematics": "ریاضی",
    "English": "انگریزی",
    "Science": "سائنس",
    "Physics": "طبیعیات",
    "Chemistry": "کیمسٹری",
    "Biology": "حیاتیات",
    "Computer Science": "کمپیوٹر سائنس",
    "Urdu": "اردو",
    "Islamic Studies": "اسلامیات",
    "Pakistan Studies": "مطالعہ پاکستان",
    "History": "تاریخ",
    "Geography": "جغرافیہ",
    "Civics": "شہریت",
    "Economics": "معاشیات",
    "Business Studies": "کاروباری مطالعہ",
    "Accounting": "محاسبہ",
    "Statistics": "شماریات",
    "Environmental Science": "ماحولیاتی سائنس",
    "Social Studies": "معاشرتی علوم",
    "Art": "فن",
    "Drawing": "ڈرائنگ",
    "Home Economics": "گھریلو معاشیات",
    "Physical Education": "جسمانی تعلیم",
    "Health Education": "صحت کی تعلیم",
    "Moral Education": "اخلاقی تعلیم",
    "Music": "موسیقی",
    "Arabic": "عربی",
    "Persian": "فارسی",
    "Punjabi": "پنجابی",
    "Sindhi": "سندھی",
    "Pashto": "پشتو",
    "Balochi": "بلوچی",
    "French": "فرانسیسی",
    "German": "جرمن",
    "Chinese": "چینی",
    "Information Technology": "انفارمیشن ٹیکنالوجی",
    "General Science": "جنرل سائنس",
    "Electronics": "الیکٹرانکس",
    "Education": "تعلیم",
    "Philosophy": "فلسفہ",
    "Psychology": "نفسیات",
    "Sociology": "معاشرتیات",
    "Law": "قانون",
    "Commerce": "کامرس",
    "Library Science": "لائبریری سائنس",
    "Food and Nutrition": "خوراک و غذائیت",
    "Engineering Drawing": "انجینئرنگ ڈرائنگ",
    "Zoology": "علم حیوانات",
    "Botany": "علم نباتات",
    "Geology": "ارضیات"
}
@register.filter
def subject_to_urdu(val):
    """Translate English subject names to Urdu."""
    return SUBJECT_URDU_MAP.get(val, val)
