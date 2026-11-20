"""Génère les CSV d'import Jira/Xray (user stories + tests manuels).
Usage: python gen_xray_csv.py   ->  stories.csv, xray_tests.csv
Import: Jira > Xray > Test Case Importer (CSV) ; stories via Jira > Import issues from CSV.
"""
import csv

MODS = {
    "RSVA": ("Authentification", "AUTH"),
    "RSVF": ("Flight", "FLIGHT"),
    "RSVI": ("Itinerary", "ITINERARY"),
}
TYPES = {"FT": "Functional Testing", "ET": "Error Testing",
         "BT": "Boundary Testing", "PT": "Permission Testing"}

# (module, type, titre, préconditions, étapes, résultat attendu)
T = [
    # ---------- RSVA : Authentification ----------
    ("RSVA", "FT", "Login valide jojo/bean", "Appli démarrée, user jojo/bean existant",
     "Ouvrir /WebTours/\nSaisir username=jojo, password=bean\nCliquer Login",
     "Page 'Welcome, jojo' affichée, menu Flights/Itinerary/Sign Off visible"),
    ("RSVA", "FT", "Création d'un nouveau compte (Sign up)", "Username inexistant",
     "Cliquer 'sign up now'\nRemplir username, password, confirm, nom, prénom, adresse\nCliquer Continue",
     "Message 'Thank you, <user>, for registering' affiché"),
    ("RSVA", "FT", "Sign Off après login", "Utilisateur connecté",
     "Cliquer Sign Off", "Retour à la page de login, session fermée"),
    ("RSVA", "ET", "Login avec mauvais mot de passe", "User jojo existant",
     "Saisir jojo / mauvais_mdp\nCliquer Login",
     "Erreur 'password was incorrect', pas d'accès"),
    ("RSVA", "ET", "Login avec utilisateur inexistant", "-",
     "Saisir user_inconnu_xyz / test\nCliquer Login",
     "Erreur 'unable to find the user name', pas d'accès"),
    ("RSVA", "ET", "Sign up avec confirmation de mot de passe différente", "-",
     "Remplir password=abc, confirm=xyz\nCliquer Continue",
     "Erreur 'Passwords do not match' (BUG potentiel si compte créé)"),
    ("RSVA", "BT", "Login avec champs vides", "-",
     "Laisser username et password vides\nCliquer Login",
     "Erreur demandant les identifiants, pas d'accès"),
    ("RSVA", "BT", "Username très long (256 caractères)", "-",
     "Saisir 256 'a' en username\nCliquer Login",
     "Rejet propre sans crash serveur ni stack trace"),
    ("RSVA", "BT", "Username avec injection ' OR 1=1 --", "-",
     "Saisir ' OR 1=1 -- en username\nCliquer Login",
     "Login refusé, aucune erreur technique affichée"),
    ("RSVA", "PT", "Accès à welcome.pl sans session", "Aucune session",
     "Appeler /cgi-bin/welcome.pl?page=menu sans userSession valide",
     "Redirection/erreur, contenu protégé non affiché"),
    ("RSVA", "PT", "Réutilisation d'une session après Sign Off", "Utilisateur déconnecté, ancien userSession conservé",
     "Se connecter, noter userSession\nSign Off\nRejouer une requête avec l'ancien userSession",
     "Session refusée"),
    ("RSVA", "PT", "Accès au profil d'un autre utilisateur", "Connecté en jojo",
     "Modifier le paramètre username dans la requête de profil",
     "Accès refusé aux données d'un autre utilisateur"),
    # ---------- RSVF : Flight ----------
    ("RSVF", "FT", "Recherche d'un vol aller simple valide", "Connecté en jojo",
     "Menu Flights\nDepart=Denver, Arrive=London\nDates valides, 1 passager\nCliquer Continue",
     "Liste de vols (outboundFlight) affichée"),
    ("RSVF", "FT", "Réservation complète d'un vol", "Connecté, recherche faite",
     "Choisir un vol\nContinue\nSaisir infos passager + carte 4111111111111111, exp 12/30\nSecure Purchase",
     "Page 'Thank you for booking through Web Tours' avec récapitulatif"),
    ("RSVF", "FT", "Recherche aller-retour avec préférence siège", "Connecté",
     "Cocher Round trip\nSeat pref=Window, type=First\nContinue",
     "Vols aller et retour proposés"),
    ("RSVF", "ET", "Depart = Arrive (même ville)", "Connecté",
     "Depart=Paris, Arrive=Paris\nContinue",
     "Erreur (villes identiques) - BUG si accepté"),
    ("RSVF", "ET", "Date de retour antérieure à la date de départ", "Connecté",
     "Depart 12/20/2026, Return 12/10/2026\nContinue",
     "Erreur de date, pas de vols proposés"),
    ("RSVF", "ET", "Paiement avec numéro de carte invalide", "Vol sélectionné",
     "creditCard=abcd\nSecure Purchase",
     "Erreur de validation, réservation non créée"),
    ("RSVF", "BT", "Nombre de passagers = 0", "Connecté",
     "numPassengers=0\nContinue", "Rejet de la valeur"),
    ("RSVF", "BT", "Nombre de passagers très grand (9999)", "Connecté",
     "numPassengers=9999\nContinue", "Rejet ou limite appliquée, pas de crash"),
    ("RSVF", "BT", "Nombre de passagers négatif (-1)", "Connecté",
     "numPassengers=-1\nContinue", "Rejet de la valeur"),
    ("RSVF", "PT", "Accès à reservations.pl sans login", "Aucune session",
     "GET /cgi-bin/reservations.pl sans session", "Accès refusé / redirection login"),
    ("RSVF", "PT", "Manipulation du prix dans le POST", "Connecté, vol sélectionné",
     "Intercepter le POST, modifier le prix\nEnvoyer",
     "Prix recalculé côté serveur, valeur falsifiée ignorée"),
    ("RSVF", "PT", "Falsification du flightID", "Connecté",
     "Modifier outboundFlight par un ID inexistant\nEnvoyer",
     "Erreur gérée, aucune réservation créée"),
    # ---------- RSVI : Itinerary ----------
    ("RSVI", "FT", "Affichage de l'itinéraire après réservation", "Au moins 1 vol réservé",
     "Menu Itinerary", "Vol réservé listé avec détails"),
    ("RSVI", "FT", "Annulation d'un vol sélectionné", "1 vol dans l'itinéraire",
     "Cocher le vol\nCliquer 'Cancel Selected'", "Vol supprimé de l'itinéraire"),
    ("RSVI", "FT", "Annulation de tous les vols", "2 vols réservés ou plus",
     "Cliquer 'Cancel All'", "Itinéraire vide, message 'No flights have been reserved'"),
    ("RSVI", "ET", "Annuler sans sélectionner de vol", "Itinéraire non vide",
     "Ne rien cocher\nCliquer 'Cancel Selected'",
     "Message d'erreur ou aucune modification, pas de crash"),
    ("RSVI", "ET", "Itinéraire d'un nouvel utilisateur sans réservation", "Nouveau compte",
     "Menu Itinerary", "Message 'No flights have been reserved'"),
    ("RSVI", "ET", "Double annulation du même vol (rejeu de requête)", "Vol déjà annulé",
     "Rejouer la requête d'annulation", "Erreur gérée, pas d'incohérence"),
    ("RSVI", "BT", "Itinéraire avec 1 seul vol", "1 vol réservé",
     "Menu Itinerary", "1 ligne affichée, bouton Cancel fonctionnel"),
    ("RSVI", "BT", "Itinéraire avec 10 vols", "10 vols réservés",
     "Menu Itinerary", "Les 10 vols affichés, pas de troncature"),
    ("RSVI", "BT", "flightID de longueur excessive dans removeFlights", "Connecté",
     "Envoyer un flightID de 500 caractères", "Rejet propre, pas d'erreur serveur"),
    ("RSVI", "PT", "Accès à itinerary.pl sans login", "Aucune session",
     "GET /cgi-bin/itinerary.pl sans session", "Accès refusé / redirection login"),
    ("RSVI", "PT", "Annulation du vol d'un autre utilisateur", "2 comptes avec vols",
     "Connecté en A, envoyer le flightID de B",
     "Annulation refusée (BUG IDOR si acceptée)"),
    ("RSVI", "PT", "Itinéraire après Sign Off (bouton Retour)", "Connecté puis déconnecté",
     "Sign Off\nBouton Retour du navigateur", "Données d'itinéraire non réaffichées"),
]

STORIES = [
    ("[US-AUTH-01] En tant que client, je veux me connecter pour accéder à mon espace", "RSVA"),
    ("[US-AUTH-02] En tant que visiteur, je veux créer un compte pour pouvoir réserver", "RSVA"),
    ("[US-AUTH-03] En tant que client, je veux me déconnecter pour protéger ma session", "RSVA"),
    ("[US-FLT-01] En tant que client, je veux rechercher des vols pour comparer les offres", "RSVF"),
    ("[US-FLT-02] En tant que client, je veux réserver et payer un vol", "RSVF"),
    ("[US-ITI-01] En tant que client, je veux consulter mon itinéraire", "RSVI"),
    ("[US-ITI-02] En tant que client, je veux annuler un ou plusieurs vols", "RSVI"),
]


def main():
    # Format Xray Test Case Importer : une ligne par étape, Summary répété (1re ligne = test)
    with open("xray_tests.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["TestKey", "Summary", "Description", "Test Type", "Test Repository Path",
                    "Labels", "Action", "Data", "Expected Result"])
        counters = {m: 2400 for m in MODS}
        n = 0
        for mod, typ, title, pre, steps, exp in T:
            counters[mod] += 1
            n += 1
            name, lab = MODS[mod]
            summary = f"[{mod}-{counters[mod]}] {title}"
            path = f"/WebTours/{mod} - {name}/{typ} - {TYPES[typ]}"
            labels = f"MANUAL {lab} MODULE-{mod} {typ} {mod} TYPE-{typ} WEBTOURS"
            lines = steps.split("\n")
            for i, act in enumerate(lines):
                last = i == len(lines) - 1
                w.writerow([f"T{n}", summary if i == 0 else "", f"Préconditions : {pre}" if i == 0 else "",
                            "Manual" if i == 0 else "", path if i == 0 else "", labels if i == 0 else "",
                            act, "", exp if last else ""])
    with open("stories.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Summary", "Issue Type", "Labels"])
        for s, m in STORIES:
            w.writerow([s, "Story", f"WEBTOURS {m}"])
    print(len(T), "tests,", len(STORIES), "stories")


if __name__ == "__main__":
    main()
