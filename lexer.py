KEYWORDS = {
    "auto","break","case","char","const","continue","default","do",
    "double","else","enum","extern","float","for","goto","if",
    "int","long","register","return","short","signed","sizeof",
    "static","struct","switch","typedef","union","unsigned",
    "void","volatile","while"
}

OPERATORS = set("+-*/><=")
DELIMITERS = set(" +-*/><=(),;{}[]")

def is_delimiter(ch):
    return ch in DELIMITERS

def is_operator(ch):
    return ch in OPERATORS

def is_keyword(word):
    return word in KEYWORDS

def is_integer(word):
    return word.isdigit()

def is_valid_identifier(word):
    return word and not word[0].isdigit() and not is_delimiter(word[0])


# =========================
# MAIN LEXER
# =========================
def lexical_analyzer(text):
    left = 0
    right = 0
    n = len(text)

    tokens = []

    while right <= n:

        if right < n and not is_delimiter(text[right]):
            right += 1
            continue

        # single char operator
        if right < n and is_operator(text[right]) and left == right:
            tokens.append(("OPERATOR", text[right]))
            right += 1
            left = right
            continue

        # extract word
        if left != right:
            sub = text[left:right]

            if is_keyword(sub):
                tokens.append(("KEYWORD", sub))

            elif is_integer(sub):
                tokens.append(("INTEGER", sub))

            elif is_valid_identifier(sub):
                tokens.append(("IDENTIFIER", sub))

            else:
                tokens.append(("UNKNOWN", sub))

        right += 1
        left = right

    return tokens