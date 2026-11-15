---
title: "Καταγραφείς τηλεμετρίας"
nav_order: 3
lang: "el"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Καταγραφείς τηλεμετρίας {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

Το `telemetry` καταγράφει κάθε κανάλι που στέλνει ένα παιχνίδι, χωρίζει τη ροή σε γύρους ή στάδια, και γράφει ένα
αρχείο [`heat3d-lap`](lap-format.md) JSON ανά γύρο σε έναν φάκελο. Η καρτέλα Race analysis του viewer διαβάζει αυτά
τα αρχεία. Η καταγραφή τρέχει μέχρι να πατήσετε **Ctrl+C**· ό,τι γύρος ή στάδιο είναι ανοιχτό εκείνη τη στιγμή γράφεται,
αν είναι αρκετά μακρύ ώστε να κρατηθεί (βλ. [Πώς χωρίζονται οι γύροι και τα στάδια](lap-splitting.md)).

Κώδικας: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
και τα modules στο [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Επιλογές {#options}

| Επιλογή | Προεπιλογή | Σημασία |
|---|---|---|
| `--game` | `forza` | Ένα από τα `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Ο φάκελος όπου γράφονται τα αρχεία γύρων. Δημιουργείται αν λείπει. Αγνοείται από το `trackmania`, του οποίου το plugin γράφει μόνο του τα αρχεία. |
| `--port` | `5300` | Η θύρα UDP που ακούει. **Για κάθε παιχνίδι εκτός του Forza, η τιμή 5300 σημαίνει "η δική του προεπιλεγμένη θύρα"**: 20777 για τα `wrc` και τα παιχνίδια DiRT, 6776 για το `rbr`, 4460 για το `beamng`. Δώστε οποιονδήποτε άλλον αριθμό για να την αλλάξετε. Δεν χρησιμοποιείται από τα παιχνίδια Assetto Corsa (κοινή μνήμη) ή το Trackmania (αρχεία). |
| `--forward` | κανένα | Μόνο Forza: `host:port` όπου προωθείται αμετάβλητο κάθε πακέτο που λαμβάνεται. `127.0.0.1:5301` για το FH Companion. Ένα απλό `:5301` σημαίνει `127.0.0.1:5301`. |
| `--install` | ανενεργό | `beamng`: αντιγράφει πρώτα το mod πρωτοκόλλου στα αποσυμπιεσμένα mods του BeamNG. `trackmania`: αντιγράφει το plugin Openplanet στον φάκελο plugins του Openplanet. Αγνοείται από τα άλλα παιχνίδια. |
| `--configure` | κανένα | Μόνο `wrc`: διαδρομή προς το `config.json` της τηλεμετρίας του EA SPORTS WRC· ενεργοποιεί το προεπιλεγμένο πακέτο `wrc` πριν από την καταγραφή (με αντίγραφο ασφαλείας πρώτα). |
| `--surface` | κανένα | Παιχνίδια ράλι (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ή `mixed`, που γράφεται στο `meta.surface` του αρχείου γύρου. Χωρίς αυτό δεν γράφεται επιφάνεια. |

## Τα παιχνίδια με μια ματιά {#the-games-at-a-glance}

| `--game` | Παιχνίδι | Πηγή | Προεπιλεγμένη θύρα | Διαχωρισμός | `game` στο αρχείο | Σελίδα |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (και 2023) | Data Out UDP | 5300 | ο μετρητής γύρων του παιχνιδιού (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, ή `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | κοινή μνήμη `acpmf_*` | - | μετρητής γύρων (`CounterSplitter`) | `assetto-corsa` | [Παιχνίδια Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | κοινή μνήμη `acpmf_*` | - | μετρητής γύρων (`CounterSplitter`) | `assetto-corsa-competizione` | [Παιχνίδια Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | κοινή μνήμη `acevo_pmf_*` | - | γραμμή εκκίνησης (`LineSplitter`) | `assetto-corsa-evo` | [Παιχνίδια Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | κοινή μνήμη `acpmf_*` | - | γραμμή εκκίνησης / στάση (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, δομή `wrc` | 20777 | ρολόι σταδίου (`StageSplitter`) | `ea-sports-wrc` | [Παιχνίδια ράλι](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | ρολόι σταδίου (`StageSplitter`) | `dirt-rally-2` | [Παιχνίδια ράλι](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | ρολόι σταδίου (`StageSplitter`) | `dirt-rally` | [Παιχνίδια ράλι](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | ρολόι σταδίου (`StageSplitter`) | `dirt-4` | [Παιχνίδια ράλι](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | ρολόι σταδίου (`StageSplitter`) | `richard-burns-rally` | [Παιχνίδια ράλι](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod πρωτοκόλλου `heat3d`, UDP | 4460 | γραμμή εκκίνησης (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanet, αρχεία CSV | - | ανά εκτέλεση, στο plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | τα δικά του αρχεία `.ibt`, διαβάζονται από τον viewer | - | ο μετρητής γύρων του προσομοιωτή | `iracing` | [iRacing](telemetry-iracing.md) |

## Κατάσταση {#status}

Ο καταγραφέας του Forza είναι αυτός που έχει δοκιμαστεί περισσότερο. Οι καταγραφείς Kunos, ράλι, BeamNG και Trackmania
είναι χτισμένοι με βάση τις δημοσιευμένες διατάξεις και δοκιμάζονται σε συνθετικά πακέτα και σελίδες χτισμένες από
αυτές τις διατάξεις (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`)· **κανένας τους δεν έχει ακόμη
τρέξει απέναντι στο ζωντανό παιχνίδι**. Οι καταγραφείς που μπορούν να ελέγξουν τα δεδομένα τους το κάνουν καθώς φτάνουν τα
πακέτα, και τυπώνουν μία φορά ένα `note:` όταν κάτι δεν ταιριάζει (το EA WRC και το DiRT συγκρίνουν την ταχύτητα κόσμου
με την ταχύτητα· το EA WRC αναφέρει επίσης ένα πακέτο μικρότερο από τα 237 bytes της προεπιλεγμένης δομής). Το
[Παιχνίδια](games.md) παραθέτει τις πηγές και ό,τι δεν έχει επιβεβαιωθεί ανά παιχνίδι.

## Ενώ τρέχει {#while-it-runs}

- Το **Forza** τυπώνει μία γραμμή κατάστασης κάθε δευτερόλεπτο: πακέτα που λήφθηκαν, και τον αριθμό, το πλήθος δειγμάτων
  και τα μέτρα του ανοιχτού γύρου, ή `waiting for a race`. Κάθε ολοκληρωμένος γύρος τυπώνει `wrote <file>`.
- Τα **παιχνίδια Assetto Corsa** τυπώνουν το όνομα κάθε αρχείου γύρου καθώς γράφεται.
- Τα **παιχνίδια ράλι** τυπώνουν `listening for <game> on port <port>`, και μετά `stage written: <file>`· με Ctrl+C
  ένα ανοιχτό στάδιο αρκετά μακρύ ώστε να κρατηθεί γράφεται ως `partial stage written: <file>`.
- Το **BeamNG** τυπώνει `lap written: <file>`, και με Ctrl+C `run written: <file>`.
- Το **Trackmania** δεν τυπώνει τίποτα ανά εκτέλεση: το plugin γράφει μόνο του τα αρχεία CSV.
- Στο τέλος κάθε καταγραφέας τυπώνει πόσα αρχεία έγραψε.

Μια εγγραφή Forza, εδώ τροφοδοτημένη με συνθετικά πακέτα Data Out ενός αυτοκινήτου που οδηγεί δύο γύρους μιας πίστας
150 m (τα αρχεία γύρων, το ακατέργαστο παράρτημα και το αρχείο αυτοελέγχου που αφήνει):

![εγγραφή τηλεμετρίας που καταγράφει δύο γύρους από συνθετική τροφοδοσία Forza](../assets/img/telemetry-run.svg)

## Ονόματα αρχείων {#file-names}

| Καταγραφέας | Μοτίβο |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Παιχνίδια Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Παιχνίδια ράλι, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, όπου το `<game>` είναι το μακρύ όνομα (`ea-sports-wrc`, `beamng`, ...), `stage` για ράλι και `lap` για BeamNG |
| Plugin Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

Το `lap` έναντι του `run` (Forza, Assetto Corsa) και η κατάληξη `_partial` (ράλι, BeamNG) δείχνουν αν ο γύρος ή το στάδιο
ολοκληρώθηκε. Η χρονοσφραγίδα είναι η στιγμή που γράφτηκε το αρχείο, όχι η στιγμή που ξεκίνησε ο γύρος.

Δίπλα στα αρχεία γύρων κάθε καταγραφέας γράφει `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - κάθε πακέτο ή σελίδα που
έφτασε, ολόκληρο, και στα μενού και ανάμεσα στους γύρους - και `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, τον
αυτοέλεγχο: ανά τύπο πακέτου πόσα ήρθαν, πόσα μπήκαν σε αρχεία γύρων, και το `lost`, που είναι 0. Ο viewer τα παραλείπει
όταν φορτώνεται ένας φάκελος. Βλ. [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) στο README.

## Θυγατρικές σελίδες αυτής της σελίδας {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Παιχνίδια Assetto Corsa](telemetry-assetto-corsa.md)
- [Παιχνίδια ράλι](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Πώς χωρίζονται οι γύροι και τα στάδια](lap-splitting.md)
- [Ολίσθηση, παρέκκλιση και παράγωγα κανάλια](slip-and-drift.md)
- [Το αρχείο heat3d-lap](lap-format.md)
