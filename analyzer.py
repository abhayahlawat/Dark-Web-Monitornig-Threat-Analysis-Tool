from textblob import TextBlob

def analyze_text(text, keywords):
    
    detected_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
    return detected_keywords

def sentiment_analysis(text):

    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity

    # Determine sentiment based on polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"
