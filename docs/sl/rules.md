---
title: Pravila
nav_order: 2
lang: "sl"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Pravila, pod katerimi je to zgrajeno {#the-rules-this-is-built-under}

Vsak del 3DHeat GameCapture upošteva iste omejitve. So zasnovne odločitve, ne odrekanja
odgovornosti, in več izmed njih namerno stane natančnost.

## Ničesar se ne vbrizga in nič se ne priklopi {#nothing-is-injected-nothing-is-hooked}

Noben del se ne priklopi na proces igre, ne bere njenega pomnilnika in se ne dotika njenega
grafičnega API-ja.

- **Okvirji** prihajajo iz Windows Graphics Capture, javnega API-ja, ki ga uporabljajo snemalniki
  zaslona (prek paketa `windows-capture`), ali iz video datoteke. Glejte
  [Zajem, maske in kakovost okvirjev](reconstruction-capture.md).
- **Telemetrija** prihaja samo iz vmesnikov, ki jih igre za to objavijo:
  - UDP tok Data Out igre Forza, vklopljen v nastavitvah igre;
  - poimenovane strani skupnega pomnilnika, ki jih igre Kunos objavljajo za aplikacije
    (`Local\acpmf_physics` in podobne). Odprte so samo za branje z `mmap`; to je dokumentiran način,
    kako aplikacije z njimi berejo, ne branje pomnilnika procesa igre;
  - UDP telemetrija, ki jo EA SPORTS WRC, igre DiRT in Richard Burns Rally (prek vtičnika RSF/NGP)
    pošiljajo, kadar je vklopljena v njihovih lastnih datotekah z nastavitvami;
  - vmesnik protokola BeamNG prek majhne modifikacije „protocol“ v Lua, ki jo naloži in pošlje lastna
    datoteka igre `lua/vehicle/protocols.lua`;
  - vmesnik vtičnika Openplanet za Trackmania, prek vtičnika, ki bere samo to, kar Openplanet izpostavi,
    in piše datoteke;
  - lastne telemetrijske datoteke iRacing `.ibt`.

## Zakaj je to pomembno {#why-it-matters}

Igra natančno pozna globino vsake slikovne pike, priklopljen medpomnilnik globine pa bi rekonstrukcijo
nivoja naredil skoraj popolno in banalno. Pomenil bi tudi vbrizgavanje v procese, ki jih lahko ščiti
proti goljufanju, kar ogroža račun vsakogar, ki to zažene. Zato se globina raje *oceni* iz slike
([Globina](reconstruction-depth.md)), velik del cevovoda za rekonstrukcijo pa obstaja zato, da iz
virov, ki so prosto uporabni, povrne čim več izgubljene natančnosti: položaje iz telemetrije, kjer jih
igra objavi, merilo ravnine tal, kjer jih ne, in maske, ki iz reševanja izločijo HUD in kabino.

Medpomnilnik globine ReShade je bil preučen in ni uporabljen. ReShade po zasnovi onemogoči dostop do
globine v večigralskih sejah, zato bi pomagal samo enoigralskim naslovom (glejte
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Stvari, ki jih orodje spremeni na vašem računalniku, in samo na zahtevo {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Dejanje | Kdaj | Kaj točno |
|---|---|---|
| Namesti pakete Python | prvi zagon okna za skeniranje, po pogovornem oknu in potrditvi | `pip install` v tolmač, ki zažene orodje – s `scan.bat` v zasebni `.venv` ob njem. Nikoli samodejno za ves sistem. |
| Pretvori model globine | gumb „Set up the depth model“, po drugem pogovornem oknu za PyTorch in ostalo | zapiše `models/depth-small-518.onnx` |
| Uredi `config.json` igre EA SPORTS WRC | `telemetry --game wrc --configure <file>` | vklopi paket `wrc` / `session_update` na 127.0.0.1; stara datoteka ostane kot `config.json.bak` |
| Kopira modifikacijo za BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` v `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (nadomesti starejšo kopijo) |
| Kopira vtičnik za Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` v `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (nadomesti starejšo kopijo) |
| Registrira globalne bližnjice | med odprtim oknom za skeniranje (Windows) | Ctrl+Alt+F9 / F10 / F11, sprostijo se, ko se okno zapre |
| Posodobi orodje | potem ko na poziv za posodobitev odgovorite z da, ali zaženete `python -m heat3d_update` | glejte [Posodobitve](updates.md) |

Orodje **ne** ureja datotek `hardware_settings_config.xml` iger DiRT in `RichardBurnsRally.ini` igre
Richard Burns Rally; izhod UDP za njih vklopite sami (glejte [Rally igre](telemetry-rally.md)).

## Kaj ostane odgovornost uporabnika {#what-stays-the-users-responsibility}

Za to, kamor uporabnik usmeri orodja, veljata licenca in EULA te igre. Datoteke krogov, posnetki,
rekonstrukcije in izvožene proge pripadajo tistemu, ki ima igro in podatke; `.gitignore` repozitorija
posnetke, datoteke krogov, mreže, uteži modelov in video izloči iz nadzora različic po mapi in po vrsti
datoteke.
