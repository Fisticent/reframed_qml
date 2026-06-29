# Design System — REFRAMED QML

Source de vérité des tokens : `constants.py` (`COLORS`), exposés à QML via le contexte `Colors`.

## Registre

Outil desktop dense (registre **product**). Voir `PRODUCT.md` pour les principes produit.

## Couleurs

| Token | Valeur | Usage |
|-------|--------|-------|
| `bg` | `#1e2128` | Fond fenêtres |
| `bg_card` | `#262a33` | Cartes / sections |
| `bg_elevated` | `#2f3540` | Champs, surfaces surélevées |
| `text` | `#e8eaed` | Texte principal, libellés sur fonds sombres |
| `text_muted` | `#8b95a5` | Sous-titres, placeholders, états vides |
| `text_on_accent` | `#1e2128` | Texte sur fonds verts/orange clairs |
| `primary` | `#5a9e3e` | Accents, indicateurs, équipe 1 |
| `primary_button` | `#3d6b28` | Boutons d'action remplis (contraste AA) |
| `primary_button_hover` | `#356024` | Hover boutons primaires |
| `secondary` | `#363d4a` | Boutons secondaires, bordures |
| `success` / `warning` / `danger` | — | États sémantiques |
| `focus_ring` | `#8bc96e` | Focus clavier |
| `toolbar_header` | `#3d5a2a` | Bandeau overlay in-game |

Règle contraste : fonds saturés clairs (`primary`, `success`, `warning`, `leader`) → `text_on_accent`. Fonds sombres ou `danger` / `team2` → `text`.

## Typographie

| Token | Valeur |
|-------|--------|
| `font_family` | Segoe UI (Windows) |
| `font_size_ui` | 12 |
| `font_size_heading` | 14 |
| `font_size_title` | 20 |

Échelle fixe (pas de clamp fluide). Une seule famille pour tout l'UI.

## Rayons

| Token | Valeur |
|-------|--------|
| `radius_card` | 8 |
| `radius_control` | 6 |

## Composants (`qml/components/`)

| Composant | Rôle |
|-----------|------|
| `ThemedButton` | Bouton rempli ; hover, focus, pressed ; texte auto-contrasté via `ThemeUtils.js` |
| `ThemedSwitch` | Toggle ; animation 120 ms (respecte `Qt.styleHints.reduceAnimations`) |
| `HotkeyButton` | Capture / effacement raccourci |
| `CalibChip` | Pastille d'état calibration (point + label + OK/Part.) |
| `ThemedComboBox` | Liste déroulante thémée |
| `ThemedCheckBox` | Case à cocher |
| `ThemedSlider` | Curseur (volume, etc.) |
| `ThemedTextField` | Champ texte |
| `ThemeUtils.js` | Helpers contraste et couleur de remplissage |

## États interactifs

Chaque contrôle custom expose : **default**, **hover**, **focus** (`focus_ring` 2 px), **pressed** (`scale: 0.98`), **disabled** (`text_muted` / `disabled_bg`).

Tooltips : `tooltip_bg` / `tooltip_fg`, désactivables via « Infobulles ».

## Architecture des écrans

### Fenêtre principale (cockpit)

Consultée en rafale, orientée **pilotage quotidien** :

1. **Raccourcis REFRAMED** — groupés Navigation / Multi-compte / Interface
2. **Options rapides** — toggles utilisés en jeu (overlay, auto-invite…)
3. **Calibrages** — bandeau d'état (chips ✅/⚠️/○), pas de grosses actions mélangées
4. **Actions courantes** — inviter groupe, fermer team
5. **Comptes actifs** — liste principale

Lien contextuel vers **⚙️ Paramètres** (header) — pas de second bouton sur l'accueil.

### Fenêtre Paramètres (config secondaire)

Touches **inventaire/sorts/zaap**, roue radiale + **volume**, vitesse clic, délai zaap, visibilité overlay, **réinitialisation**.


- **ToolbarWindow** : overlay compact (boutons 32×32), draggable.
- **RadialMenu** : canvas + icônes ; couleurs `radial_*`.
- **CalibOverlay** : bandeau instruction calibration.

## Legacy

`theme/reframed.json` provient de l'édition CustomTkinter ; **non utilisé par QML**. Ne pas modifier pour l'UI Qt — mettre à jour `constants.py` uniquement.
