"""2025 BABBD draft, transcribed from the final league workbook."""

ROSTER_2025 = {
    "Ali": {
        "hitting": [("C", "Smith"), ("1B", "Harper"), ("2B", "Durbin"), ("3B", "Chisholm"),
                    ("SS", "Volpe"), ("OF", "Tucker"), ("OF", "Duran"), ("OF", "Grisham"),
                    ("Util", "Freeman"), ("Util", "Ohtani")],
        "pitching": [("SP", "Skubal"), ("SP", "Rodon"), ("RP", "Megill"), ("RP", "Bednar"),
                     ("P", "Imanaga"), ("P", "Cease"), ("W", "Nola")],
    },
    "Baker": {
        "hitting": [("C", "Kelly"), ("1B", "Bohm"), ("2B", "Stott"), ("3B", "Suarez"),
                    ("SS", "Turner"), ("OF", "Rodriguez"), ("OF", "Arozarena"), ("OF", "Suzuki"),
                    ("Util", "Castellanos"), ("Util", "Bader"), ("W", "Robles")],
        "pitching": [("SP", "Kirby"), ("SP", "Castillo"), ("RP", "Duran"), ("RP", "Munoz"),
                     ("P", "Smith"), ("P", "Buehler")],
    },
    "Brian": {
        "hitting": [("C", "Contreras"), ("1B", "Guerrero"), ("2B", "Polanco"), ("3B", "Muncy"),
                    ("SS", "Swanson"), ("OF", "Chourio"), ("OF", "Yelich"), ("OF", "T Hernandez"),
                    ("Util", "Bogaerts"), ("Util", "De La Cruz"), ("W", "Green")],
        "pitching": [("SP", "Gilbert"), ("SP", "Gausman"), ("RP", "Uribe"), ("RP", "Hoffman"),
                     ("P", "Bieber"), ("P", "Abbott")],
    },
    "Mitch": {
        "hitting": [("C", "Raleigh"), ("1B", "Arraez"), ("2B", "Betts"), ("3B", "Edman"),
                    ("SS", "Story"), ("OF", "O'Hearn"), ("OF", "Tatis"), ("OF", "Bellinger"),
                    ("Util", "Gimenez"), ("Util", "Varsho"), ("W", "Caballero")],
        "pitching": [("SP", "Yamamoto"), ("SP", "Fried"), ("RP", "Suarez"), ("RP", "Williams"),
                     ("P", "Glasnow"), ("P", "Sheehan")],
    },
    "Reed": {
        "hitting": [("C", "Wells"), ("1B", "Busch"), ("2B", "Hoerner"), ("3B", "Ramirez"),
                    ("SS", "Clement"), ("OF", "Crow-Armstrong"), ("OF", "Kwan"), ("OF", "Happ"),
                    ("Util", "Manzardo"), ("Util", "Shaw")],
        "pitching": [("SP", "Sanchez"), ("SP", "Williams"), ("RP", "Palencia"), ("RP", "Kittridge"),
                     ("P", "Boyd"), ("P", "Keller"), ("W", "Green")],
    },
    "Russ": {
        "hitting": [("C", "Realmuto"), ("1B", "Vaughn"), ("2B", "Turang"), ("3B", "Bregman"),
                    ("SS", "Bichette"), ("OF", "Schwarber"), ("OF", "Springer"), ("OF", "Pages"),
                    ("Util", "Kirk"), ("Util", "Rojas")],
        "pitching": [("SP", "Peralta"), ("SP", "Woo"), ("RP", "Scott"), ("RP", "Priester"),
                     ("P", "Luzardo"), ("P", "Kershaw"), ("W", "Vesia")],
    },
    "Tim": {
        "hitting": [("C", "Rice"), ("1B", "Naylor"), ("2B", "K Hernandez"), ("3B", "Machado"),
                    ("SS", "Rafaela"), ("OF", "Merrill"), ("OF", "Judge"), ("OF", "Stanton"),
                    ("Util", "Frelick"), ("Util", "Lowe")],
        "pitching": [("SP", "Snell"), ("SP", "Ohtani"), ("RP", "Chapman"), ("RP", "Miller"),
                     ("P", "Pivetta"), ("P", "Crochet"), ("W", "Schlittler")],
    },
}

# Used only where a surname/short label is not unique in the postseason player pool.
# Values are filled with MLB person IDs after the first discovery run.
PLAYER_ID_OVERRIDES_2025: dict[tuple[str, str, str], int] = {
    ("Ali", "hitting", "Chisholm"): 665862,       # Jazz Chisholm Jr.
    ("Baker", "hitting", "Turner"): 607208,       # Trea Turner
    ("Baker", "hitting", "Rodriguez"): 677594,    # Julio Rodriguez
    ("Baker", "pitching", "Buehler"): 621111,     # Walker Buehler (DNP)
    ("Brian", "hitting", "Guerrero"): 665489,     # Vladimir Guerrero Jr.
    ("Brian", "hitting", "Green"): 682985,        # Riley Greene
    ("Brian", "pitching", "Abbott"): 671096,      # Andrew Abbott (DNP)
    ("Mitch", "hitting", "Tatis"): 665487,        # Fernando Tatis Jr.
    ("Mitch", "pitching", "Suarez"): 663158,      # Robert Suarez
    ("Mitch", "pitching", "Williams"): 642207,    # Devin Williams
    ("Reed", "pitching", "Williams"): 668909,     # Gavin Williams
    ("Reed", "pitching", "Kittridge"): 552640,    # Andrew Kittredge
    ("Reed", "pitching", "Green"): 668881,        # Hunter Greene
    ("Russ", "pitching", "Peralta"): 642547,      # Freddy Peralta
    ("Russ", "pitching", "Scott"): 656945,        # Tanner Scott (DNP)
    ("Tim", "hitting", "Naylor"): 647304,         # Josh Naylor
    ("Tim", "hitting", "K Hernandez"): 571771,    # Enrique Hernandez
    ("Tim", "pitching", "Miller"): 695243,        # Mason Miller
}

# Final owner totals in the reference workbook. BB and L are retained solely to
# validate the historical import; 2026 scoring uses the standard 5x5 categories.
EXPECTED_TOTALS_2025 = {
    "Brian": {"R": 58, "HR": 24, "RBI": 56, "SB": 2, "BB": 50, "AVG": .2547169811, "W": 5, "L": 5, "SV": 3, "K": 82, "ERA": 3.157245334, "WHIP": 1.137092189},
    "Mitch": {"R": 47, "HR": 14, "RBI": 53, "SB": 4, "BB": 33, "AVG": .2323232323, "W": 6, "L": 2, "SV": 2, "K": 77, "ERA": 2.755158269, "WHIP": 1.224514786},
    "Ali": {"R": 47, "HR": 15, "RBI": 31, "SB": 6, "BB": 49, "AVG": .2294617564, "W": 1, "L": 1, "SV": 2, "K": 72, "ERA": 3.681770367, "WHIP": 1.012973857},
    "Tim": {"R": 31, "HR": 8, "RBI": 32, "SB": 3, "BB": 24, "AVG": .2580645161, "W": 7, "L": 5, "SV": 1, "K": 116, "ERA": 2.814682682, "WHIP": .9382275607},
    "Baker": {"R": 32, "HR": 12, "RBI": 32, "SB": 8, "BB": 32, "AVG": .1979166667, "W": 2, "L": 2, "SV": 2, "K": 42, "ERA": 3.240051841, "WHIP": 1.128018048},
    "Reed": {"R": 28, "HR": 8, "RBI": 27, "SB": 4, "BB": 18, "AVG": .2751937984, "W": 3, "L": 4, "SV": 3, "K": 45, "ERA": 3.306054978, "WHIP": 1.183649313},
    "Russ": {"R": 43, "HR": 17, "RBI": 46, "SB": 0, "BB": 29, "AVG": .2215568862, "W": 3, "L": 5, "SV": 0, "K": 35, "ERA": 5.307692308, "WHIP": 1.461538462},
}
