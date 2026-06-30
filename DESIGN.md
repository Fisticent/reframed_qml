# Design System — REFRAMED QML

Source de vérité des tokens : `constants.py` (`COLORS`), exposés à QML via le contexte `Colors`.
Dernière synchro : scan code (`constants.py`, `qml/components/`, fenêtres principales).

## Registre

Outil desktop dense (registre **product**). Voir `PRODUCT.md` pour les principes produit.

## Couleurs

### Surfaces & texte

| Token | Valeur | Usage |
|-------|--------|-------|
| `bg` | `#1e2128` | Fond fenêtres |
| `bg_card` | `#262a33` | Cartes / sections |
| `bg_elevated` | `#2f3540` | Champs, surfaces surélevées |
| `text` | `#e8eaed` | Texte principal, libellés sur fonds sombres |
| `text_muted` | `#8b95a5` | Sous-titres, placeholders, états vides / disabled |
| `text_on_accent` | `#1e2128` | Texte sur fonds verts/orange clairs |
| `separator` | `#363d4a` | Séparateurs discrets |
| `disabled_bg` | `#2a2f3a` | Fond contrôles désactivés |

### Primaire & actions

| Token | Valeur | Usage |
|-------|--------|-------|
| `primary` | `#5a9e3e` | Accents, indicateurs, équipe 1 |
| `primary_hover` | `#4a8532` | Hover accents / toolbar macro |
| `primary_bright` | `#6db84a` | Variante claire (rare) |
| `primary_button` | `#3d6b28` | Boutons d'action remplis (contraste AA) |
| `primary_button_hover` | `#356024` | Hover boutons primaires |
| `secondary` | `#363d4a` | Boutons secondaires, bordures |
| `secondary_hover` | `#424957` | Hover secondaire |
| `secondary_dark` | `#2a2f3a` | Fond bouton icône / surfaces basses |
| `focus_ring` | `#8bc96e` | Focus clavier (2 px) |
| `toolbar_header` | `#3d5a2a` | Bandeau drag overlay in-game |

### Sémantique & calibration

| Token | Valeur | Usage |
|-------|--------|-------|
| `success` / `success_hover` | `#4caf6a` / `#3d9460` | Calibré OK, chip done |
| `warning` / `warning_hover` | `#c4782a` / `#a86520` | Partiel, leader, alerte |
| `danger` / `danger_hover` | `#b83a32` / `#962f28` | Destructif, erreur |
| `calib` / `calib_hover` | `#363d4a` / `#424957` | Chip non calibré |
| `calib_border` | `#c4782a` | Bordure chip partiel |

### Équipes & radial

| Token | Valeur | Usage |
|-------|--------|-------|
| `team1` / `team1_hover` | `#5a9e3e` / `#4a8532` | Équipe 1 |
| `team2` / `team2_hover` | `#8b4040` / `#723535` | Équipe 2 |
| `leader` | `#c4782a` | Badge leader |
| `radial_accent` | `#5a9e3e` | Roue radiale — accent |
| `radial_hover` | `#4a8532` | Roue radiale — hover |
| `radial_active` | `#3d5a2a` | Compte actif (liste + radial) |
| `radial_bg` | `#262a33` | Fond roue |
| `radial_outline` | `#363d4a` | Contour roue |

### Tooltips

| Token | Valeur | Usage |
|-------|--------|-------|
| `tooltip_bg` | `#363d4a` | Fond infobulle |
| `tooltip_fg` | `#e8eaed` | Texte infobulle |

**Règle contraste :** fonds saturés clairs (`primary`, `success`, `warning`, `leader`) → `text_on_accent`. Fonds sombres ou `danger` / `team2` → `text`. Utiliser `ThemeUtils.js` (`textForFill`, `fillColor`) pour le texte sur remplissages dynamiques.

## Typographie

| Token | Valeur | Usage |
|-------|--------|-------|
| `font_family` | Segoe UI | Toute l'UI (Windows) |
| `font_size_ui` | 12 | Corps, boutons, labels |
| `font_size_secondary` | 11 | Sous-textes, combos, chips, hints |
| `font_size_heading` | 14 | Titres de section |
| `font_size_title` | 20 | Titre fenêtre principale |

Échelle fixe (pas de clamp fluide). Une seule famille pour tout l'UI. Exception locale : bandeau toolbar `9px` bold (drag handle compact).

## Rayons

| Token | Valeur | Usage |
|-------|--------|-------|
| `radius_control` | 6 | Boutons, champs, toolbar, chips |
| `radius_card` | 8 | Cartes / panneaux |
| `radius_window` | 10 | Chrome fenêtre (si applicable) |

## Icônes

Charger via `app.assetUrl("icons/…")` ou `app.skinUrl(…)` pour les assets jeu.

| Fichier | Usage |
|---------|--------|
| `settings.svg` | Paramètres (header Main, Settings) |
| `close.svg` | Fermer / effacer raccourci |
| `paste.svg` | Coller+Entrée (toolbar) |
| `user.svg` | Fallback avatar compte |
| `teams.svg` | Gestionnaire binds |
| `calibrations.svg` | Section calibrages |
| `shortcuts.svg` | Section raccourcis |
| `chevron-up.svg` / `chevron-down.svg` | Réordonner comptes |
| `star-filled.svg` / `star-outline.svg` | Leader |
| `open-panel.svg` | Ouvrir UI depuis toolbar |
| `radial.svg`, `overlay-bar.svg`, `tutorial-welcome.svg` | Onboarding / radial |

Boutons icône : **16×16** (`ThemedButton`), **20×20** (toolbar `MacroButton`), **24×24** (classe active toolbar). Toujours fournir un `fallback` texte court si l'image manque.

## Composants (`qml/components/`)

| Composant | Rôle |
|-----------|------|
| `ThemedButton` | Bouton rempli ou icône ; `iconSource`, tooltips ; contraste auto via `ThemeUtils.js` |
| `ThemedSwitch` | Toggle ; animation 120 ms (respecte `Qt.styleHints.reduceAnimations`) |
| `HotkeyButton` | Capture / effacement raccourci ; icône `close.svg` ; mode `compact` |
| `CalibChip` | Pastille calibration (point 8px + label + OK/Part.) ; états success/warning/calib |
| `ThemedComboBox` | Liste déroulante ; typo `font_size_secondary` |
| `ThemedCheckBox` | Case à cocher |
| `ThemedSlider` | Curseur (volume, etc.) |
| `ThemedTextField` | Champ texte |
| `WindowChrome` | Barre titre / drag custom |
| `ThemeUtils.js` | `fillColor`, `textForFill` — contraste sur remplissages |

## États interactifs

Chaque contrôle custom expose : **default**, **hover**, **focus** (`focus_ring` 2 px), **pressed** (`scale: 0.98`, 80 ms OutQuad), **disabled** (`text_muted`, `opacity: 0.42` toolbar).

Tooltips : `tooltip_bg` / `tooltip_fg`, délai 400 ms, désactivables via `app.showTooltips`.

**Actions conditionnelles** (Python `app_controller.py`) — boutons `enabled` + tooltip explicatif si faux :

| Slot QML | Condition |
|----------|-----------|
| `app.canGroupInvite()` | Chat calibré + `leader_name` défini |
| `app.canAutoZaap()` | Calibration zaap `full` |
| `app.canSwapXp()` | Calibration XP calibrée |

Ne jamais coder l'état calibration par la couleur seule : doubler par texte/icône/forme (cf. `PRODUCT.md`).

## Architecture des écrans

### Fenêtre principale (cockpit)

Consultée en rafale, orientée **pilotage quotidien** :

1. **Raccourcis REFRAMED** — groupés Navigation / Multi-compte / Interface
2. **Options rapides** — toggles utilisés en jeu (overlay, auto-invite…)
3. **Calibrages** — bandeau d'état (chips ✅/⚠️/○), pas de grosses actions mélangées
4. **Actions courantes** — inviter groupe (`canGroupInvite`), fermer team
5. **Comptes actifs** — liste avec indicateur actif (barre 3 px + bordure), leader étoile, chevrons, close

Lien vers **Paramètres** via icône `settings.svg` dans le header — pas de second bouton sur l'accueil.

### Fenêtre Paramètres (config secondaire)

Touches inventaire/sorts/zaap, roue radiale + volume, vitesse clic, délai zaap, visibilité overlay, réinitialisation. Header avec icône `settings.svg`.

### Toolbar in-game (`ToolbarWindow`)

- Frameless, `opacity: 0.95`, draggable via bandeau `toolbar_header`
- Boutons macro **32×32**, `MacroButton` interne
- Ligne 1 : ouvrir UI, combo mode ALL/T1/T2, refresh, coller+entrée
- Ligne 2 : icône classe + raccourcis jeu (visibilité via `overlay_show_*`)
- Zaap / Invite : `enabled` lié à `canAutoZaap` / `canGroupInvite`

### Autres surfaces

- **RadialMenu** : canvas + icônes ; tokens `radial_*`
- **CalibOverlay** : bandeau instruction calibration
- **CharManagerWindow** : binds avancés par personnage

## Do's et Don'ts

### Do

- **Do** garder l'UI dense mais hiérarchisée (titres 14 px, corps 12 px, hints 11 px).
- **Do** utiliser les tokens `Colors.*` — jamais de hex en dur dans le QML.
- **Do** préférer les icônes SVG du dossier `icons/` aux emojis dans les titres/boutons.
- **Do** désactiver + tooltip explicatif quand une action requiert une calibration manquante.
- **Do** respecter `Qt.styleHints.reduceAnimations` pour toute animation.

### Don't

- **Don't** faire une landing page (hero géant, scroll narratif, sections aérées).
- **Don't** ajouter des dashboards « hero-metric » ou des dégradés décoratifs.
- **Don't** insérer de modales ou animations lentes entre intention et action.
- **Don't** modifier `theme/reframed.json` pour l'UI Qt — legacy CustomTkinter uniquement.
- **Don't** toucher `constants.py` depuis plusieurs agents en parallèle sans merge coordonné.

## Legacy

`theme/reframed.json` provient de l'édition CustomTkinter ; **non utilisé par QML**. Mettre à jour `constants.py` uniquement pour les tokens visuels.
