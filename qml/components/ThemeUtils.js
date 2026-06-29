.pragma library

var LIGHT_TEXT_FILLS = {
    "#b83a32": true,
    "#962f28": true,
    "#8b4040": true,
    "#723535": true,
    "#363d4a": true,
    "#424957": true,
    "#2a2f3a": true,
    "#262a33": true,
    "#2f3540": true,
    "#1e2128": true,
    "#3d5a2a": true
}

function normalizeColor(c) {
    if (!c)
        return ""
    return String(c).toLowerCase()
}

function isTransparent(bg) {
    var s = normalizeColor(bg)
    if (!s || s === "transparent")
        return true
    // Qt convertit "transparent" en #00000000
    if (s === "#00000000" || s === "#000000")
        return true
    if (s.length === 9 && s.slice(7, 9) === "00")
        return true
    return false
}

function prefersLightText(bg) {
    if (isTransparent(bg))
        return false
    var s = normalizeColor(bg)
    if (s.indexOf("#") !== 0)
        return false
    return !!LIGHT_TEXT_FILLS[s]
}

function textForFill(bg, colors) {
    if (!colors)
        return "#e8eaed"
    if (isTransparent(bg))
        return colors.text
    if (prefersLightText(bg))
        return colors.text
    return colors.text_on_accent || "#1e2128"
}

function fillColor(base, hover, hovered, pressed, enabled, colors) {
    if (!enabled)
        return colors.disabled_bg || colors.secondary_dark
    if (pressed)
        return hover
    if (hovered)
        return hover
    return base
}
