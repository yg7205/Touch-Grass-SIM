def check_active_window(title):
    keywords = ["tiktok", "instagram", "youtube", "twitter", "reddit", "facebook"]
    title_lower = title.lower()
    for kw in keywords:
        if kw in title_lower:
            return True
    return False