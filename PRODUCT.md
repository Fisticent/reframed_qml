# Product

## Register

product

## Users

Joueurs multi-comptes de **Dofus** sur Windows (souvent AZERTY, droits admin). Contexte d'usage :
ils pilotent 2 à 8 fenêtres de jeu en parallèle et veulent basculer le focus, synchroniser
des clics et lancer des macros **sans jamais quitter le jeu des yeux**. Profil dominant =
**power user** qui configure une fois puis pilote au clavier/souris en plein combat. L'UI de
configuration est consultée par rafales ; l'overlay in-game et la roue radiale sont les
surfaces réellement « chaudes » pendant le jeu.

## Product Purpose

REFRAMED est un **panneau de contrôle** pour le multi-compte : détection des fenêtres,
cycle/focus entre persos (raccourcis, binds avancés, roue radiale), clics synchronisés,
macros (auto-zaap, invite groupe, swap XP/drop), toolbar flottante in-game,
auto-accept échange, system tray. Succès = l'outil **disparaît dans la tâche** : zéro friction
pendant le jeu, configuration faite une fois.

## Brand Personality

Outil, pas vitrine. Dense, fiable, rapide. Trois mots : **technique, compact, sans-friction**.
Esthétique sombre type « console de raid ». La personnalité passe par la clarté des états et la
réactivité, pas par la décoration.

## Anti-references

- Sites vitrines / landing pages (hero géant, scroll narratif, sections aérées) — l'opposé du besoin.
- Dashboards SaaS « hero-metric » (grand chiffre + label + accent dégradé).
- Tout ce qui ajoute de la cérémonie entre l'intention et l'action (modales superflues, animations lentes).

## Design Principles

1. **L'outil disparaît dans la tâche** — pendant le jeu, l'UI ne doit jamais réclamer d'attention.
2. **L'état avant la décoration** — calibré/non-calibré, actif, en-écoute, leader : ces états
   doivent être lisibles d'un coup d'œil, c'est le cœur du produit.
3. **Densité assumée, mais hiérarchisée** — beaucoup d'infos OK, à condition d'une hiérarchie claire.
4. **Lisibilité in-game prioritaire** — overlay et roue radiale doivent rester nets par-dessus un décor chargé.
5. **Familiarité gagnée** — affordances standard (combos, switches, listes), pas d'affordance réinventée.

## Accessibility & Inclusion

Desktop Windows, écrans haute densité (200 % DPI courant). Contraste du texte ≥ 4.5:1 sur fond
sombre. Ne jamais coder une information par la **couleur seule** (T1/T2, leader, calibré) — doubler
par icône/texte/forme. Cibles cliquables confortables (l'overlay est utilisé vite, en plein jeu).
