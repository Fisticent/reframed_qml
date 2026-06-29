import QtQuick
import QtQuick.Controls.Basic
import "ThemeUtils.js" as Theme

Button {
    id: control
    property color baseColor: Colors.secondary
    property color hoverColor: Colors.secondary_hover
    property color textColor: Colors.text
    property bool forceLightText: false
    property bool labelOnFill: true
    property int radius: Colors.radius_control
    property int borderW: 0
    property color borderColor: "transparent"
    property string tooltipText: ""
    property string iconSource: ""

    readonly property color _fill: Theme.fillColor(
        baseColor, hoverColor, hovered, pressed, enabled, Colors)
    readonly property color _labelColor: {
        if (!enabled)
            return Colors.text_muted
        if (forceLightText)
            return Colors.text
        if (!labelOnFill && (hovered || pressed))
            return Colors.text
        if (!labelOnFill)
            return textColor
        return Theme.textForFill(_fill, Colors)
    }

    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    implicitHeight: 32

    ToolTip.visible: hovered && tooltipText !== "" && (typeof app !== "undefined" ? app.showTooltips : true)
    ToolTip.text: tooltipText
    ToolTip.delay: 400

    contentItem: Item {
        Image {
            anchors.centerIn: parent
            visible: control.iconSource !== ""
            source: control.iconSource
            width: 16
            height: 16
            sourceSize.width: 16
            sourceSize.height: 16
        }
        Text {
            anchors.centerIn: parent
            visible: control.iconSource === ""
            text: control.text
            color: control._labelColor
            font.pixelSize: Colors.font_size_ui
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    background: Rectangle {
        radius: control.radius
        color: control._fill
        border.width: control.activeFocus ? 2 : control.borderW
        border.color: control.activeFocus ? Colors.focus_ring : control.borderColor
        scale: control.pressed ? 0.98 : 1.0

        Behavior on scale {
            enabled: !(typeof Qt !== "undefined" && Qt.styleHints && Qt.styleHints.reduceAnimations)
            NumberAnimation { duration: 80; easing.type: Easing.OutQuad }
        }
    }
}
