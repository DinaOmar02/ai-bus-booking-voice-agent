import re

async def normalize_location(origin: str, destination: str):
        origin = origin.strip().lower()
        destination = destination.strip().lower()

        return origin, destination

def validate_egyptian_phone(phone: str) -> tuple[bool, str]:

    clean = re.sub(r"[^\d+]", "", phone)
    
    if clean.startswith("+20"):
        clean = "0" + clean[3:]
    elif clean.startswith("20") and len(clean) == 12:
        clean = "0" + clean[2:]
        
    egypt_pattern = r"^01[0125]\d{8}$"
    
    if not re.match(egypt_pattern, clean):
        return False, clean
        
    return True, clean