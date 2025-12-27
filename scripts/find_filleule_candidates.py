import re
import unicodedata
from difflib import SequenceMatcher

from app.database import SessionLocal
from app.models import (  # noqa: F401
    annee_scolaire,
    correspondant,
    document,
    etablissement,
    filleule,
    localite,
    parrain,
    parrainage,
    role,
    scolarite,
    suivisocial,
    typedocument,
    user,
)
from app.models.filleule import Filleule


RAW_LIST = """
Filleule	Parrain
ABATAYE Sana	BARBE JACKY ET NICOLE
ABELLOUCH Asmaa ( VC)	COTE COLISSON Christine
ABELLOUCH Oumayma	BABACI Louisa
ABELLOUCH Ikram	BANTMAN Beatrice ( amie CG)
ABELLOUCH Mariam 	GUYOT Claude
ABERBOUR Nouhaila	JULIENNE Patrick
ABU ADEL Fadma	DUFAURE Laurence
AHRAICH  Ilham	GAUTHIER MANON + TREMBLAY LUC
AHRAICH Hiba 	TERKI Mustapha ( VC)
AIT BOUTAADILT Fatiha	PESANDO Brigitte
AJAMOUR Khadija	BESSE COLETTE
AKHNIOUCH Asma 	CROISILE Anne Sophie (VC)
AMHIRKI Fatima	PICQ Muriel
AMMEDDAH Khadija 	DELCEY Ghislaine
AMRIJIN Maryam	DESTEBANES Jean Michel  (AV)
ANEJAR Naima	GRANDJANIN ANNIE
ANJIMI Fatimzahra 	GRAFF Elodie
ANJIMI  Imane	SANJUAN Jacques (VC)
ANJIMI Fadma	VANDEWELDE Nathalie
ANJIMI Hajar 	LAINEAU Regis
ANTOUS Fatiha	QUERAUD Christiane
ATOUIJIR Mariam	BARAT Laurenna
AZGOUNE Fatimzahra 	CIROT Clothilde (amis KB)
AZGOUNE Rim	CARLES Serge
AZIKI Khadija 	PORRAL Martine
BELKASS Mariem	IDRISSI Mohamed
BELMAHJOUBI Hanane	PASTUREAU Jean-Claude
BENMANSOUR Asmae	BOIDRON Caroline
BENTALEB Salma 	WOLFF Brigitte (VC)
BIAZ Fatimzahra	PAPOT Herve (VC)
BIZBIZ Chaima 	FOUGERAT Celine
BOUBRIK Assma 	LETOURNEAU Myriam (VC)
BOUTZARZIT Amina 	JEUNE Estelle ( AM ROBINEAU)
CHAFAI Hiba	BOUVET GERBETTAL Eric(MCL)
CHRIJI Asmae	THENIERE Isabelle et Richard
CHRIJI Saadia 	BENADI Hind ( VC )
EDDARI Yasmine 	ELKHOU Fouzia
EDDIBA Donia	TRABELSI Mohammed
EL HOUSSANI Nora	REIGNIER Margaux (Soeur Anais)
ELAAMRAOUI Dounia	LE CAR Daniele
ELAAMRAOUI Yasmine	KORCZENIUK Christophe
ELAMRAOUI Karima	LE CAR  Daniele (3 EME FIL)
ELGAROUAZE Khadija	HAMMERER Veronique
ELHABRI Hasna	MAYEUR Emmanuelle
ELHADJI Sara	CAMILLERI Michel
ELKAID Leila	BENIDA DANA
ELMAALOUJ Hiba	CATINAT Beatrice
ESSAKI Khadija 	PACQUOLA Chiara MALIN Federico
ETTAOURIRI Chayma 	LE CAR Daniele
ETTAOURIRI Fatimzahra 	CURSOL Christian
ETTAOURIRI Khadija	BECKER Catherine
ETTAOURIRI Majda 	GAREL  Deborah
ETTAOURIRI Noura 	CLAVERIE Patrice
ETTAOURIRI Safaa ( Amina)	PORRAL Martine
HABIBALLAH Hiba	HERRAN Jean-Philippe
HABOUDE Fatiha	BIKEROUANE Khadija
HANKRIR Malak	HOSTEIN Xavier ( yonnet)
HARNISS Zarha	SANCHEZ Jorge
HATEM Meryem	LAURENT Pierre et Dominique ( JL)
HERWIZ Siham	MEYNARDI  Pascale (  CG)
HRID Bouchra 	FOSSAT Mathilde
HRID Fadma	FOSSAT Sylvie
HRID Saafa	FOSSAT Thibaut
HRID Khadija	BONNAUD Sonia
HRID Laila	POULENAT Patricia
HRID Siham	SOARES Nathalie
IDDOBA Kawtar	MARCILLAT Lison
IHADDAJ Assmae 	SEGUIN Kathleen
IKHRICHI Hajar	El AMRI Yasmine
IMSOUR Hiba	VANNIER Sarah
JAIDI Chaima	CHAVELET Elisabeth
JAIDI Noura	LITALIEN Dominique
KAJJID Khadija 	LEENDERS CHLOE ET VICK
KARDOUNE Karima	DEFONTENAY Anne Laure
KHARACHI Karima	KIELH Josy
KOSMATE Khadija	NANA et ROGER
LAAOUINA Ahlam 	CROISILLE Veronique Marie
LAAOUINA Hasnae 	KHELIFA Siham
LABSIR Meriem 	AEBI Michele
LAGSIR Hiba	LECAUDEY Marina
LAGSIR Salma 	LAILHEUGUE Valerie
LAHSSIOUI Nouha	LECOEUR Maryvonne
LAKLIDA Hiba	HERIT GILLES
LAKLIDA Ibtissam	GIRARD Jean Paul et Lysiane
LAKRA Aya 	KERKVLIET Lise (ami CG)
LAKRA Sanaa (VC)	MEYNARDI  Pascale (  CG) x2
LAKRATI Ibtissam	GUYOT Annaelle
LAMKHANTAR Khadija	LAINEAU SOPHIE
LBAZE Khadija 	DESPOUY Isabelle (amie VC)
LIKAMT Meriem	PALIX Ghislaine
MAHROUS Ghizlaine 	PAUVIF Laurent et Faty
MANSOURI Hajar 	ROBINEAU Anne Marie
MARWANE Ilham 	LARIVIERE Annie
MAZIZI Zineb	VERCHERE  Agnes
MOSLIH Kawtar	LOULOUM Marie Claude
NAJI Malek	LIDOU Maurice
N'SSISE Fatiha	HADDOUCH Zohra
OUABDOU Assmae	ZARABA Fatima
OUHSSINE Khadija	YETIS SERDAL (  SL)
OULEHLOU Fadna	BOUDAREL Christelle
OURACHI Rachida	NANA et ROGER
OUTSSILA Hajar 	HAOUAS Cristina
RAMI Fatimzahra 	KLEIN Martin
RAMI Hajar 	KLEIN Martin
SAMOU Fatima	MALLET Martine (CA)
SOUKRAT Najoua	YONNET Marie Cyrille
TAHIRI KAWTAR 	HEJL Michel et Christine ( VC)
WDJAA CHAIMAE 	ZORIO Gaelle
WIDADE Elaidy	MATHIS MEYNARD Anne Charlotte
YOUB Rokaya  	ROHDAIN FLORENCE (VC)
ZAKANI Samira 	STRICKER Solange (VC)
ZARROUK Yousra	RODHAIN Florence (2 EME FILL )
""".strip()


def normalize_text(value: str) -> str:
    value = value.strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def clean_raw_name(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\bx\s*2\b", "", value, flags=re.IGNORECASE)
    value = value.replace("+", " ")
    value = value.replace("&", " ")
    return " ".join(value.split())


def split_line(line: str) -> tuple[str, str] | None:
    if "\t" in line:
        parts = [part for part in line.split("\t") if part.strip()]
        if len(parts) >= 2:
            return parts[0], parts[1]
    parts = re.split(r"\s{2,}", line.strip())
    if len(parts) >= 2:
        left = " ".join(parts[:-1])
        right = parts[-1]
        return left, right
    return None


def ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def best_candidates(name_norm: str, alt_norm: str, pool: list[dict], limit: int = 5) -> list[dict]:
    scored = []
    for item in pool:
        score = max(ratio(name_norm, item["norm"]), ratio(alt_norm, item["norm"]))
        if score >= 0.6:
            scored.append({**item, "score": score})
    scored.sort(key=lambda x: (-x["score"], x["nom"].lower(), x["prenom"].lower()))
    return scored[:limit]


def main():
    db = SessionLocal()
    try:
        filleules = db.query(Filleule).all()
    finally:
        db.close()

    pool = []
    for f in filleules:
        full = f"{f.nom} {f.prenom}".strip()
        norm = normalize_text(full)
        pool.append(
            {
                "id": f.id_filleule,
                "nom": f.nom or "",
                "prenom": f.prenom or "",
                "norm": norm,
            }
        )

    exact_lookup = {}
    for item in pool:
        exact_lookup.setdefault(item["norm"], []).append(item)

    missing = []
    for raw_line in RAW_LIST.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("filleule"):
            continue
        parsed = split_line(line)
        if not parsed:
            continue
        raw_filleule, _ = parsed
        clean_filleule = clean_raw_name(raw_filleule)
        norm = normalize_text(clean_filleule)

        if norm in exact_lookup:
            continue
        missing.append(clean_filleule)

    seen = set()
    for name in missing:
        if name in seen:
            continue
        seen.add(name)
        parts = name.split()
        if len(parts) >= 2:
            nom = parts[0]
            prenom = " ".join(parts[1:])
        else:
            nom = name
            prenom = ""
        norm = normalize_text(f"{nom} {prenom}")
        alt_norm = normalize_text(f"{prenom} {nom}")
        candidates = best_candidates(norm, alt_norm, pool)
        print(f"\n{name}")
        if not candidates:
            print("  - aucun candidat proche")
            continue
        for cand in candidates:
            full_name = f"{cand['prenom']} {cand['nom']}".strip()
            print(f"  - {full_name} (id {cand['id']}) score {cand['score']:.2f}")


if __name__ == "__main__":
    main()
