---
title: "Trackmania (2020)"
nav_order: 5
lang: "el"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Κώδικας: το plugin του Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Το plugin δεν έχει τρέξει ακόμη μέσα στο παιχνίδι**· ο αναγνώστης του προβολέα
για το CSV του δοκιμάζεται.

## Γιατί ένα plugin που γράφει αρχεία {#why-a-plugin-that-writes-files}

Το Trackmania δεν έχει δική του έξοδο τηλεμετρίας. Το Openplanet, η πλατφόρμα plugin του παιχνιδιού,
εκθέτει στα plugin την κατάσταση του οχήματος που βλέπει ο παίκτης, αλλά τα plugin του Openplanet δεν
μπορούν να στέλνουν UDP. Έτσι το plugin γράφει ένα αρχείο CSV ανά διαδρομή στον δικό του φάκελο
αποθήκευσης, και ο προβολέας διαβάζει τα αρχεία όπως είναι. Δεν υπάρχει διεργασία εγγραφής:
το `telemetry --game trackmania` μόνο εγκαθιστά το plugin (με `--install`) και τυπώνει πού θα εμφανιστούν
τα αρχεία.

## Εγκατάσταση και φόρτωση {#installing-and-loading}

- Το `--install` αντιγράφει το `mods/trackmania/Heat3dRecorder` στο
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, αντικαθιστώντας παλαιότερο αντίγραφο. Χωρίς το
  `--install` δεν αντιγράφεται τίποτα.
- Μέσα στο παιχνίδι: **Openplanet > Developer > Load plugin**, και επιλέξτε `3DHeat recorder`.
- Το plugin εξαρτάται από το plugin **VehicleState** του Openplanet (`dependencies = ["VehicleState"]`
  στο `info.toml`).
- Τα μη υπογεγραμμένα plugin φορτώνουν μόνο στη **λειτουργία προγραμματιστή** του Openplanet, που
  περιορίζει το online παιχνίδι. Το plugin μπορεί να υπογραφεί στο openplanet.dev· εδώ δεν είναι υπογεγραμμένο.

Οι διαδρομές γράφονται στο `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Φορτώστε αυτά τα
αρχεία CSV στην καρτέλα Race analysis του προβολέα. Τα `-o` και `--port` αγνοούνται για το Trackmania.

## Τι καταγράφει το plugin {#what-the-plugin-records}

Διαβάζει μόνο ό,τι εκθέτει το Openplanet - την κατάσταση του οχήματος που βλέπει ο παίκτης
(`VehicleState::ViewingPlayerState()`) και τον χρόνο αγώνα και τον αριθμό επανεμφανίσεων του παίκτη
(`CSmScriptPlayer`) - δεν στέλνει τίποτα πουθενά και δεν αλλάζει τίποτα στο παιχνίδι. Μια γραμμή γράφεται σε
κάθε καρέ (`Update`), οπότε ο ρυθμός δειγματοληψίας είναι ο ρυθμός καρέ του παιχνιδιού.

| Στήλη | Πηγή |
|---|---|
| `time` | `CurrentRaceTime` / 1000, δευτερόλεπτα |
| `x`, `y`, `z` | `Position` (παγκόσμιο, Y προς τα πάνω) |
| `speed` | μήκος του `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ή 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | το `SlipCoef` κάθε τροχού (μέτρο ολίσθησης 0..1) |
| `loose` | 1 όταν το υλικό εδάφους κάποιου τροχού είναι Grass, Ice, Sand, Dirt, Green ή RoadIce |
| `airborne` | 1 όταν το αυτοκίνητο δεν έχει επαφή με το έδαφος |
| `respawns` | επανεμφανίσεις από την αρχή της διαδρομής |

## Διαδρομές {#runs}

- Μια διαδρομή **ξεκινά** στο πρώτο καρέ όπου ο χρόνος αγώνα δεν είναι αρνητικός (η αντίστροφη μέτρηση
  δεν καταγράφεται).
- **Τελειώνει** όταν η ακολουθία UI της playground είναι η ακολουθία τερματισμού (τιμή 11): το αρχείο
  γράφεται ως ολοκληρωμένο, με τον τελευταίο χρόνο αγώνα ως `seconds`.
- **Εγκαταλείπεται** - γράφεται με `_partial` στο όνομα και `"complete": false` - όταν το ρολόι του αγώνα
  πάει πίσω πάνω από μισό δευτερόλεπτο (επανεκκίνηση), ή όταν ο παίκτης φεύγει από την playground.
- Μια διαδρομή με λιγότερες από 20 γραμμές δεν γράφεται.

## Το αρχείο {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Ονομάζεται `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Το όνομα της πίστας έχει αφαιρεμένους τους κωδικούς
μορφοποίησης, και τα διπλά εισαγωγικά αντικαθίστανται με μονά. Οι τιμές γράφονται με τέσσερα δεκαδικά. Η
μορφή περιγράφεται στο [Το αρχείο heat3d-lap](lap-format.md#the-csv-form).

Το `meta` της κεφαλίδας έχει `"slip": "index"` - τα κανάλια `slipIndex.*` είναι το δικό του μέτρο
ολίσθησης του Trackmania 0..1, όχι φυσική ολίσθηση - και `"discipline": "arcade"`.
