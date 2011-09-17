import re
from pymongo.objectid import ObjectId

def convert_to_object_id(_id):
    if type(_id) == type(u'') or type(_id) == type(''):
        _id = ObjectId(_id)

    return _id

def normalize_text_for_url(text):
    
    text = decode_title(text)
    text = left_spaces(text, 400)
    
    #make works like don't can't or dominic's to dont cant dominics
    matches = re.findall(r"[a-z]'[a-z]", text)
    for match in matches:
        text = text.replace(match, match.replace("'", ""))
        
    #make terms like 1080 x 768 to 1080x768
    matches = re.findall(r"\b[0-9]+\sx\s[0-9]+\b", text)
    for match in matches:
        text = text.replace(match, match.replace(" ", ""))
    
    
    text = re.sub(r'[^a-zA-Z0-9\.\-_]', '-', text.lower().strip())
   
    doubleFind = text.find('--')
    while doubleFind <> -1:
        text = text.replace('--', '-')
        doubleFind = text.find('--')
    
    if text.startswith('-'): text= text[1:]
    if text.endswith('-'): text = text[0:-1]
    
    return text

def decode_title(title):
    import unidecode
    title = title.replace('&amp;', '&')
    return unidecode.unidecode(title)

def left_spaces(text, length):
    if length > 0 and len(text) > length:
        m = re.split(r'\s', text)

        if m[0] == text:
            return text[:length]
        
        str = ''
        for g in m:
            if len(str + g) > length:
                return str[1:]
            else:
                str = str + ' ' + g;
        
    return text

