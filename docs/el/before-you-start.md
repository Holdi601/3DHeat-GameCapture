---
title: Πριν ξεκινήσετε
nav_order: 1.5
lang: el
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Πριν ξεκινήσετε {#before-you-start}

Δεν έχετε ξαναδουλέψει με τη γραμμή εντολών; Αυτή η σελίδα σας πηγαίνει από το μηδέν σε μια πρώτη
λειτουργική εντολή. Χρειάζεται περίπου δέκα λεπτά, μία φορά.

## 1. Εγκαταστήστε την Python {#install-python}

Το GameCapture είναι πρόγραμμα Python. Χρειάζεστε **Python 3.10 ή νεότερη**.

1. Πηγαίνετε στο [python.org/downloads](https://www.python.org/downloads/) και κατεβάστε τη νεότερη
   Python για Windows.
2. Τρέξτε το πρόγραμμα εγκατάστασης. Στην πρώτη οθόνη, **επιλέξτε «Add python.exe to PATH»**. Αν δεν την επιλέξετε,
   το τερματικό δεν θα βρει την Python.
3. Κάντε κλικ στο *Install Now*.

Ή, σε ένα τερματικό: `winget install Python.Python.3.12`.

## 2. Εγκαταστήστε το Git {#install-git}

Το Git κατεβάζει το εργαλείο. Πάρτε το από το [git-scm.com](https://git-scm.com/download/win), ή τρέξτε
`winget install Git.Git`. Αν δεν θέλετε Git, χρησιμοποιήστε *Code > Download ZIP* στη
[σελίδα του GitHub](https://github.com/Holdi601/3DHeat-GameCapture) και αποσυμπιέστε το.

## 3. Ανοίξτε τερματικό σε έναν φάκελο {#open-a-terminal-in-a-folder}

Το τερματικό είναι ένα παράθυρο όπου πληκτρολογείτε εντολές. Αυτές οι σελίδες χρησιμοποιούν το **PowerShell**,
που έχει κάθε υπολογιστής με Windows.

- Ανοίξτε τον φάκελο στην Εξερεύνηση αρχείων, κάντε κλικ στη γραμμή διεύθυνσης, πληκτρολογήστε `powershell`
  και πατήστε Enter. Το PowerShell ανοίγει **μέσα σε αυτόν τον φάκελο**.
- Ή ανοίξτε το PowerShell από το μενού Έναρξη και πηγαίνετε σε έναν φάκελο με `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Διαβάστε τις εντολές αυτών των σελίδων {#read-the-commands-on-these-pages}

- Πληκτρολογήστε κάθε γραμμή εντολής και πατήστε Enter.
- Το κείμενο μέσα σε γωνιώδεις αγκύλες είναι **σημείο κράτησης θέσης**: βάλτε εκεί τη δική σας τιμή, χωρίς τις αγκύλες.
  Το `<recording>.mp4` σημαίνει ένα όνομα αρχείου, όπως `match1.mp4`.
- Το κείμενο μέσα σε τετράγωνες αγκύλες, όπως το `[--fps 5]`, είναι **προαιρετικό**.
- Μια διαδρομή με κενά θέλει εισαγωγικά: `"C:\My Videos\match1.mp4"`.
- Γραμμές που αρχίζουν με `#` είναι σχόλια. Δεν τα πληκτρολογείτε.

## 5. Πάρτε το εργαλείο και τα πακέτα του {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Το `python -m venv .venv` φτιάχνει έναν ιδιωτικό φάκελο για τα πακέτα του εργαλείου, ώστε να μην μπλέκονται
με τίποτα άλλο στον υπολογιστή σας. Κάθε εντολή μετά αρχίζει με `.venv\Scripts\python`.

**Θα δείτε** στο τέλος της τελευταίας γραμμής `Successfully installed ...`. Ελέγξτε ότι το εργαλείο δουλεύει:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Θα δείτε** μια λίστα εντολών, που αρχίζει με `usage: heat3d_capture`.

![Η λίστα εντολών που τυπώνει το --help](../assets/img/cli-help.svg)

Μπορείτε επίσης να *ενεργοποιήσετε* τον φάκελο μία φορά, και μετά να πληκτρολογείτε μόνο `python`:

| Τερματικό | Ενεργοποίηση | Μετά |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Αν το PowerShell πει *running scripts is disabled*, τρέξτε μία φορά
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ή παραλείψτε την ενεργοποίηση.

## 6. Επιπλέον προγράμματα που χρειάζονται ορισμένες εντολές {#extra-programs-some-commands-need}

| Εντολή | Χρειάζεται | Εγκατάσταση |
|---|---|---|
| `hud` | **ffmpeg** και **ffprobe** (για ανάγνωση βίντεο) | `winget install Gyan.FFmpeg`, και μετά νέο τερματικό. Ελέγξτε με `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, εγκατεστημένο πριν από τα άλλα πακέτα | η εντολή από το [pytorch.org](https://pytorch.org/get-started/locally/) για την κάρτα γραφικών σας |

## Όταν κάτι πάει στραβά {#when-something-goes-wrong}

| Βλέπετε | Σημαίνει | Τι να κάνετε |
|---|---|---|
| `'python' is not recognized` | Η Python δεν είναι στο PATH | Εγκαταστήστε ξανά την Python με το PATH επιλεγμένο, και μετά ανοίξτε νέο τερματικό. |
| `No module named heat3d_capture` | το τερματικό δεν είναι στον φάκελο του εργαλείου | Κάντε `cd` στον φάκελο `3DHeat-GameCapture`. |
| `No module named numpy` (ή άλλο πακέτο) | τα πακέτα δεν είναι εγκατεστημένα, ή χρησιμοποιήσατε άλλη Python | Τρέξτε ξανά τη γραμμή `pip install -r requirements.txt`, με `.venv\Scripts\python`. |
| `'.venv' is not recognized` | γράψατε `/` στο cmd | Χρησιμοποιήστε κάθετες ανάποδες: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | λείπει το ffmpeg | Δείτε το βήμα 6, και μετά ανοίξτε νέο τερματικό. |

Επόμενο: η [Αρχική](index.md) έχει ένα πρώτο παράδειγμα για κάθε εργασία.
