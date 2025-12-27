import re
import unicodedata

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
from app.models.parrain import Parrain
from app.models.parrainage import Parrainage


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

FILLEULE_ALIAS_MAP = {
    "aziki khadija": "aziki khadija 2",
    "atouijir mariam": "atwijir meriam",
    "kajjid khadija": "hajjid khadija",
    "kardoune karima": "gardoune karima",
    "kharachi karima": "elkharachi karima",
}


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


def build_lookup(records, attr_order) -> dict[str, list]:
    lookup: dict[str, list] = {}
    for record in records:
        parts = [getattr(record, attr, "") or "" for attr in attr_order]
        name_a = normalize_text(" ".join(parts))
        name_b = normalize_text(" ".join(reversed(parts)))
        for key in {name_a, name_b}:
            if not key:
                continue
            lookup.setdefault(key, []).append(record)
    return lookup


def main(apply_changes: bool = True) -> None:
    db = SessionLocal()
    try:
        filleules = db.query(Filleule).all()
        parrains = db.query(Parrain).all()

        filleule_lookup = build_lookup(filleules, ["nom", "prenom"])
        parrain_lookup = build_lookup(parrains, ["nom", "prenom"])

        created = 0
        skipped_existing = 0
        unmatched = []
        ambiguous = []
        parse_errors = []

        for raw_line in RAW_LIST.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.lower().startswith("filleule"):
                continue

            parsed = split_line(line)
            if not parsed:
                parse_errors.append(line)
                continue
            raw_filleule, raw_parrain = parsed
            clean_filleule = clean_raw_name(raw_filleule)
            clean_parrain = clean_raw_name(raw_parrain)

            norm_filleule = normalize_text(clean_filleule)
            norm_parrain = normalize_text(clean_parrain)

            if norm_filleule in FILLEULE_ALIAS_MAP:
                norm_filleule = normalize_text(FILLEULE_ALIAS_MAP[norm_filleule])

            filleule_matches = filleule_lookup.get(norm_filleule, [])
            parrain_matches = parrain_lookup.get(norm_parrain, [])

            if len(filleule_matches) != 1 or len(parrain_matches) != 1:
                ambiguous.append(
                    {
                        "line": line,
                        "filleule": clean_filleule,
                        "parrain": clean_parrain,
                        "filleule_matches": len(filleule_matches),
                        "parrain_matches": len(parrain_matches),
                    }
                )
                continue

            filleule_obj = filleule_matches[0]
            parrain_obj = parrain_matches[0]

            existing = (
                db.query(Parrainage)
                .filter(Parrainage.id_filleule == filleule_obj.id_filleule)
                .filter(Parrainage.id_parrain == parrain_obj.id_parrain)
                .first()
            )
            if existing:
                skipped_existing += 1
                continue

            db.add(
                Parrainage(
                    id_filleule=filleule_obj.id_filleule,
                    id_parrain=parrain_obj.id_parrain,
                )
            )
            created += 1

        if apply_changes:
            db.commit()
        else:
            db.rollback()

        print(f"Parrainages crees: {created}")
        print(f"Parrainages deja existants: {skipped_existing}")
        if parse_errors:
            print("\nLignes non parsees:")
            for line in parse_errors:
                print(f"  - {line}")
        if ambiguous:
            print("\nLignes a verifier (matchs incomplets/ambigus):")
            for item in ambiguous:
                print(
                    f"  - {item['line']} | filleule:{item['filleule_matches']} parrain:{item['parrain_matches']}"
                )
    finally:
        db.close()


if __name__ == "__main__":
    main(apply_changes=True)
