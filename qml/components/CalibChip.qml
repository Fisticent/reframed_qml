import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "ThemeUtils.js" as Theme

Button {
    id: control
    property string calibKey: ""
    property string label: ""
    signal triggered()

    readonly property var st: app.calibStates
    readonly property bool done: calibKey === "zaap" ? st.zaap === "full" : st[calibKey] === true
    readonly property bool partial: calibKey === "zaap" && st.zaap === "partial"

    implicitHeight: 34
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    readonly property color fillColor: done ? Colors.success
        : (partial ? Colors.warning : Colors.calib)
    readonly property color hoverFill: done ? Colors.success_hover
        : (partial ? Colors.warning_hover : Colors.calib_hover)
    readonly property color ink: Theme.textForFill(
        control.enabled ? (control.hovered ? hoverFill : fillColor) : Colors.disabled_bg, Colors)

    ToolTip.visible: hovered && (typeof app !== "undefined" ? app.showTooltips : true)
    ToolTip.text: done ? (label + " calibré")
               : partial ? app.zaapCalibHint()
               : ("Calibrer " + label)
    ToolTip.delay: 400

    contentItem: RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 8
        spacing: 8

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: control.done ? ink
                  : control.partial ? ink
                  : "transparent"
            border.width: control.done || control.partial ? 0 : 1.5
            border.color: control.ink
            opacity: control.done || control.partial ? 1.0 : 0.55
        }

        Text {
            Layout.fillWidth: true
            text: control.label
            color: control.ink
            font.pixelSize: 11
            font.bold: true
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        Text {
            visible: control.done || control.partial
            text: control.done ? "OK" : "Part."
            color: control.ink
            font.pixelSize: Colors.font_size_secondary
            font.bold: true
            opacity: 0.9
        }
    }

    background: Rectangle {
        radius: Colors.radius_control
        color: control.enabled
               ? (control.hovered ? control.hoverFill : control.fillColor)
               : Colors.disabled_bg
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Colors.focus_ring
                      : (control.done ? Qt.rgba(0, 0, 0, 0.15)
                         : (control.partial ? Colors.warning_hover : Colors.secondary_hover))
        scale: control.pressed ? 0.98 : 1.0
    }

    onClicked: control.triggered()
}
