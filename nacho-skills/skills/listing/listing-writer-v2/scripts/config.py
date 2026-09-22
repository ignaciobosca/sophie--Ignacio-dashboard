# config.py — agency / client house style for the xlsx output.
# Swap these values for any palette without touching skill logic.
# Default values are the agency house style; they are NOT tied to any one product brand.

STYLE = {
    "header_bg":   "0A2333",   # table header fill (navy default)
    "secondary_bg":"13835B",   # secondary header fill (green default)
    "flag_color":  "EA6C34",   # "must confirm" / warning text (orange default)
    "row_fill":    "F3F3F1",   # zebra row fill (off-white default)
    "body_color":  "2B2B2B",   # body text (charcoal default)
    "font":        "DM Sans",  # falls back to Calibri if unavailable
}

# Set per run from intake. Never hardcode a product brand here.
BRAND = ""          # e.g. "Acme Goods" — filled from Section 1
PRODUCT_SLUG = ""   # e.g. "learning-tablet" — filled from intake, used in filename
MODE = "renovation" # "renovation" or "new"
