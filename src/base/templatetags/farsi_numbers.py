from django import template

register = template.Library()

def intcomma(value):
    try:
        value = int(value)
        return "{:,}".format(value)
    except:
        return value

def to_farsi_number(number):
    en_to_fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(number).translate(en_to_fa)

@register.filter
def farsi_comma(value):
    return to_farsi_number(intcomma(value))




units = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
tens = ["", "ده", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
hundreds = ["", "یکصد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
specials = {
    10: "ده", 11: "یازده", 12: "دوازده", 13: "سیزده", 14: "چهارده",
    15: "پانزده", 16: "شانزده", 17: "هفده", 18: "هجده", 19: "نوزده"
}
thousands = ["", "هزار", "میلیون", "میلیارد", "تریلیون"]

def group_to_word(n):
    n = int(n)
    if n == 0:
        return ""
    parts = []

    h = n // 100
    t = (n % 100) // 10
    u = n % 10

    if h:
        parts.append(hundreds[h])

    if 10 < n % 100 < 20:
        parts.append(specials[n % 100])
    else:
        if t:
            parts.append(tens[t])
        if u:
            parts.append(units[u])

    return " و ".join(parts)

def number_to_persian_words(number):
    number = int(number)
    if number == 0:
        return "صفر"

    number_str = str(number)
    groups = []
    while number_str:
        groups.insert(0, number_str[-3:])
        number_str = number_str[:-3]

    parts = []
    for i, group in enumerate(reversed(groups)):
        num = int(group)
        if num == 0:
            continue
        part = group_to_word(num)
        if thousands[i]:
            part += f" {thousands[i]}"
        parts.insert(0, part.strip())

    return " و ".join(parts)


@register.filter
def farsi_comma_with_words(value):
    try:
        num = int(value)
        farsi_number = to_farsi_number("{:,}".format(num))
        words = number_to_persian_words(num)
        return f"{farsi_number} ریال ({words} ریال)"
    except:
        return value
