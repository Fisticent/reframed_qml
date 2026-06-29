import QtQuick
import QtQuick.Controls.Basic

CheckBox {
    id: control
    implicitHeight: 28

    indicator: Rectangle {
        implicitWidth: 18
        implicitHeight: 18
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: 4
        color: control.checked ? Colors.primary_button : Colors.bg_elevated
        border.color: control.activeFocus ? Colors.focus_ring
                    : (control.checked ? Colors.primary_button_hover : Colors.secondary_hover)
        border.width: control.activeFocus ? 2 : 1

        Text {
            anchors.centerIn: parent
            text: "✓"
            color: Colors.text_on_accent
            font.pixelSize: 11
            font.bold: true
            visible: control.checked
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? Colors.text : Colors.text_muted
        font.pixelSize: 12
        leftPadding: control.indicator.width + 8
        verticalAlignment: Text.AlignVCenter
    }
}
