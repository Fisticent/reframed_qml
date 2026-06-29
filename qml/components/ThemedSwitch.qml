import QtQuick
import QtQuick.Controls.Basic
import "ThemeUtils.js" as Theme

Switch {
    id: control
    property string tooltipText: ""
    readonly property bool animate: !(typeof Qt !== "undefined" && Qt.styleHints && Qt.styleHints.reduceAnimations)

    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    ToolTip.visible: hovered && tooltipText !== "" && (typeof app !== "undefined" ? app.showTooltips : true)
    ToolTip.text: tooltipText
    ToolTip.delay: 400

    indicator: Rectangle {
        implicitWidth: 40
        implicitHeight: 20
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: 10
        color: control.checked ? Colors.primary_button : Colors.secondary
        border.color: control.activeFocus ? Colors.focus_ring
                    : (control.checked ? Colors.primary_button_hover : Colors.secondary_hover)
        border.width: control.activeFocus ? 2 : 1

        Rectangle {
            x: control.checked ? parent.width - width - 2 : 2
            y: 2
            width: 16
            height: 16
            radius: 8
            color: Colors.text

            Behavior on x {
                enabled: control.animate
                NumberAnimation { duration: 120; easing.type: Easing.OutQuad }
            }
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? Colors.text : Colors.text_muted
        font.pixelSize: Colors.font_size_ui
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + 8
    }
}
