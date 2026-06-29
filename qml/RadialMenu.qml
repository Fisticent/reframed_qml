import QtQuick
import QtQuick.Window

Window {
    id: radialWin
    objectName: "radialWin"
    transientParent: null
    width: radial.wheelSize
    height: radial.wheelSize
    x: radial.posX
    y: radial.posY
    visible: radial.isOpen
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window | Qt.WindowTransparentForInput
    color: "transparent"

    Connections {
        target: radial
        function onOpenChanged() {
            if (radial.isOpen) {
                radialWin.show()
                radialWin.raise()
            }
        }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        property real cx: width / 2
        property real cy: height / 2
        property int hovered: radial.hoveredIndex

        onHoveredChanged: requestPaint()

        Connections {
            target: radial
            function onItemsChanged() { canvas.requestPaint() }
            function onCurrentNameChanged() { canvas.requestPaint() }
            function onOpenChanged() { if (radial.isOpen) canvas.requestPaint() }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)

            var items = radial.items
            var n = items.length
            if (n === 0) return

            var rOuter = radial.radiusOuter
            var rInner = radial.radiusInner
            var anglePer = 2 * Math.PI / n
            var C = radial.colors

            for (var i = 0; i < n; i++) {
                // start at top (-90deg), clockwise
                var start = -Math.PI / 2 + i * anglePer
                var end = start + anglePer
                var isActive = items[i].name === radial.currentName
                var baseColor = isActive ? C.radial_active : C.radial_bg
                var fill = (i === hovered) ? C.radial_hover : baseColor
                var stroke = (i === hovered) ? C.radial_accent : C.radial_outline

                ctx.beginPath()
                ctx.moveTo(cx, cy)
                ctx.arc(cx, cy, rOuter, start, end, false)
                ctx.closePath()
                ctx.fillStyle = fill
                ctx.fill()
                ctx.lineWidth = 2
                ctx.strokeStyle = stroke
                ctx.stroke()

                // text
                var mid = start + anglePer / 2
                var tx = cx + Math.cos(mid) * (rOuter * 0.65)
                var ty = cy + Math.sin(mid) * (rOuter * 0.65)
                ctx.fillStyle = C.text
                ctx.font = "bold " + Colors.font_size_ui + "px " + Colors.font_family
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                var label = items[i].name.substring(0, 10)
                ctx.fillText(label, tx, ty + 16)
            }

            // center hub
            ctx.beginPath()
            ctx.arc(cx, cy, rInner, 0, 2 * Math.PI, false)
            ctx.fillStyle = C.bg
            ctx.fill()
            ctx.lineWidth = 2
            ctx.strokeStyle = C.radial_outline
            ctx.stroke()

            ctx.beginPath()
            ctx.arc(cx, cy, 4, 0, 2 * Math.PI, false)
            ctx.fillStyle = C.radial_accent
            ctx.fill()
        }
    }

    // icônes de classe (rendues par-dessus le canvas via Repeater)
    Repeater {
        model: radial.items
        Image {
            property int n: radial.items.length
            property real anglePer: n > 0 ? 2 * Math.PI / n : 0
            property real mid: -Math.PI / 2 + index * anglePer + anglePer / 2
            visible: source != "" && n > 0
            source: modelData.icon
            width: 32; height: 32
            sourceSize.width: 32; sourceSize.height: 32
            x: radialWin.width / 2 + Math.cos(mid) * (radial.radiusOuter * 0.65) - 16
            y: radialWin.height / 2 + Math.sin(mid) * (radial.radiusOuter * 0.65) - 18
        }
    }
}
