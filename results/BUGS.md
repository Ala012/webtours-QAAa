# Bugs réels détectés (WebTours 1.0, exécution du 2026-11-20)

Tous reproduits par requêtes HTTP contre http://127.0.0.1:1080 et corrélés avec `C:\WebTours\logs\error.log`.
Suite automatique : 36 tests, **26 réussis, 10 échoués** (9 = bugs ci-dessous, 1 = test Selenium à corriger, pas un bug de l'appli).

| ID | Sév. | Test lié | Bug | Preuve |
|----|------|----------|-----|--------|
| BUG-01 | Critique | RSVF-2410 (PT) | `reservations.pl` utilisable **sans login** : la liste des vols est renvoyée à un visiteur anonyme | POST sans session -> 200 + `outboundFlight` |
| BUG-02 | Haute (crash) | RSVF-2405 (ET) | **Plantage du script Perl** si la date est invalide (`13/45/2026`, `abc`, vide, `00/00/0000`) : page vide de 717 octets | error.log : `Month '12' out of range 0..11 at reservations.pl line 727` / `Month '-1'…` |
| BUG-03 | Haute | RSVF-2412 (PT) | Un `flightID` inexistant (`INEXISTANT`) est accepté : "Reservation Made!" et une ligne corrompue (vol "INEXISTANT", Denver->Denver, total 0 $) apparaît dans l'itinéraire | POST `outboundFlight=INEXISTANT` |
| BUG-04 | Haute | RSVF-2406 (ET) | Achat accepté avec carte invalide (`abcd`) ou **tous champs vides** : "Reservation Made!" | POST `buyFlights` sans données |
| BUG-05 | Haute | RSVI-2403 (FT) | **« Cancel All » échoue** : "could not delete your entire itinerary because of a database synchronization error" (itinéraire contenant des lignes issues de BUG-03) | POST `removeAllFlights` |
| BUG-06 | Haute (sécurité) | RSVF (ET) | **XSS réfléchi** : `depart=<script>alert(1)</script>` est renvoyé non échappé dans la page | réponse contient le script brut |
| BUG-07 | Haute (sécurité) | RSVA (PT) | `admin.pl` accessible **sans authentification** (page d'administration affichée) | GET sans session -> 200 |
| BUG-08 | Moyenne | RSVF-2404 (ET) | Vols proposés avec départ = arrivée (Paris -> Paris) | recherche Paris/Paris |
| BUG-09 | Moyenne | RSVF-2405 (ET) | Date de retour antérieure au départ acceptée | 12/20 -> 12/10 |
| BUG-10 | Moyenne | RSVF-2407/2408/2409 (BT) | Nombre de passagers 0, -1 (et 9999) accepté | `numPassengers` hors bornes |
| BUG-11 | Basse | RSVA | `printenv.pl` -> **HTTP 500** : script absent / interpréteur introuvable | error.log : `couldn't spawn child process: printenv.pl` |

À noter :
- Les tests RSVA (login, signup, mauvais mot de passe, injection SQL, session après Sign Off) **passent** : pas de bug détecté de ce côté.
- Les données de test (compte jojo) sont polluées par BUG-03 ; supprimer `C:\WebTours\cgi-bin\users\jojo` des réservations avant de rejouer si besoin.
